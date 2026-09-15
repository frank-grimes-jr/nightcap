# Transactional repair for the legacy globally widened skill_caps table.
#
# DryRun and Apply require the target to be the exact strict superset captured in
# docs/audits/skill-caps-diff/live-only.csv. Rollback requires an exact canonical
# target plus the retained skill_caps_epic10_removed table.

[CmdletBinding()]
param(
    [ValidateSet('DryRun', 'Apply', 'Rollback')]
    [string]$Mode = 'DryRun',
    [string]$TargetContainer = 'nightcap-peq-rehearsal',
    [string]$TargetDatabase = 'peq',
    [string]$TargetUser = 'eqemu',
    [string]$TargetPassword = 'rehearsal-eqemu',
    [string]$CanonicalContainer = 'nightcap-peq-baseline',
    [string]$CanonicalDatabase = 'peq',
    [string]$CanonicalUser = 'eqemu',
    [string]$CanonicalPassword = 'baseline-eqemu',
    [string]$EvidenceCsv,
    [string]$BackupTable = 'skill_caps_epic10_removed',
    [int]$ExpectedTargetRows = 74449,
    [int]$ExpectedCanonicalRows = 58359,
    [int]$ExpectedRemovalRows = 16090,
    [string]$ExpectedEvidenceSha256 =
        '8DF2E24F7866E2EF6F49396212D31AF57456403595CA1EC643106DF85D331270',
    [switch]$AllowLiveTarget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$liveContainerName = 'akk-stack-mariadb-1'
$stagingTable = 'skill_caps_epic10_removal_keys'
$procedureName = 'apply_epic10_skill_caps_repair'

if (-not $EvidenceCsv) {
    $EvidenceCsv = Join-Path $PSScriptRoot `
        '..\docs\audits\skill-caps-diff\live-only.csv'
}

if (
    $TargetContainer -eq $liveContainerName -and
    -not $AllowLiveTarget
) {
    throw (
        "Refusing to target live container $liveContainerName without " +
        '-AllowLiveTarget'
    )
}

foreach ($value in @(
    $TargetContainer,
    $TargetDatabase,
    $TargetUser,
    $TargetPassword,
    $CanonicalContainer,
    $CanonicalDatabase,
    $CanonicalUser,
    $CanonicalPassword,
    $BackupTable,
    $stagingTable,
    $procedureName
)) {
    if ($value -notmatch '^[A-Za-z0-9_.-]+$') {
        throw "Unsafe container/database/user/password/identifier argument: $value"
    }
}

if (-not (Test-Path -LiteralPath $EvidenceCsv)) {
    throw "Removal evidence does not exist: $EvidenceCsv"
}

$evidenceHash = (Get-FileHash -LiteralPath $EvidenceCsv -Algorithm SHA256).Hash
if ($evidenceHash -ne $ExpectedEvidenceSha256) {
    throw (
        "Removal evidence SHA-256 mismatch. Expected " +
        "$ExpectedEvidenceSha256, got $evidenceHash"
    )
}

$evidence = @(Import-Csv -LiteralPath $EvidenceCsv)
if ($evidence.Count -ne $ExpectedRemovalRows) {
    throw (
        "Removal evidence row count mismatch. Expected " +
        "$ExpectedRemovalRows, got $($evidence.Count)"
    )
}

$evidenceMap = @{}
foreach ($row in $evidence) {
    foreach ($column in @('skill_id', 'class_id', 'level', 'cap')) {
        $parsed = 0
        if (-not [int]::TryParse([string]$row.$column, [ref]$parsed)) {
            throw "Non-integer $column in removal evidence: $($row.$column)"
        }
    }

    $skillId = [int]$row.skill_id
    $classId = [int]$row.class_id
    $level = [int]$row.level
    $cap = [int]$row.cap
    if (
        $skillId -lt 0 -or $skillId -gt 255 -or
        $classId -lt 0 -or $classId -gt 255 -or
        $level -lt 0 -or $level -gt 255 -or
        $cap -lt 0 -or $cap -gt 16777215
    ) {
        throw "Out-of-range removal evidence row: $($row | ConvertTo-Json -Compress)"
    }

    $key = "$skillId|$classId|$level"
    if ($evidenceMap.ContainsKey($key)) {
        throw "Duplicate composite key in removal evidence: $key"
    }
    $evidenceMap[$key] = $cap
}

function Read-SkillCaps(
    [string]$Container,
    [string]$Database,
    [string]$User,
    [string]$Password
) {
    $rows = @(
        & docker exec $Container mysql "-u$User" "-p$Password" $Database `
            --batch --raw --skip-column-names `
            -e 'SELECT skill_id,class_id,level,cap FROM skill_caps ORDER BY class_id,skill_id,level;' 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Read failed for ${Container}/${Database}: $($rows -join [Environment]::NewLine)"
    }

    $map = @{}
    foreach ($row in $rows) {
        $parts = $row -split "`t"
        if ($parts.Count -ne 4) {
            throw "Unexpected skill_caps row from ${Container}: $row"
        }
        $key = "$($parts[0])|$($parts[1])|$($parts[2])"
        if ($map.ContainsKey($key)) {
            throw "Duplicate skill_caps composite key in ${Container}: $key"
        }
        $map[$key] = [int]$parts[3]
    }
    return $map
}

function Get-CanonicalRelationship {
    $target = Read-SkillCaps `
        $TargetContainer $TargetDatabase $TargetUser $TargetPassword
    $canonical = Read-SkillCaps `
        $CanonicalContainer $CanonicalDatabase $CanonicalUser $CanonicalPassword

    $liveOnly = @{}
    $canonicalOnly = 0
    $capMismatches = 0

    foreach ($entry in $target.GetEnumerator()) {
        if (-not $canonical.ContainsKey($entry.Key)) {
            $liveOnly[$entry.Key] = [int]$entry.Value
        }
        elseif ([int]$entry.Value -ne [int]$canonical[$entry.Key]) {
            $capMismatches++
        }
    }
    foreach ($entry in $canonical.GetEnumerator()) {
        if (-not $target.ContainsKey($entry.Key)) {
            $canonicalOnly++
        }
    }

    return [pscustomobject]@{
        TargetRows = $target.Count
        CanonicalRows = $canonical.Count
        LiveOnly = $liveOnly
        CanonicalOnly = $canonicalOnly
        CapMismatches = $capMismatches
    }
}

function Assert-StrictSuperset([object]$Relationship) {
    if ($Relationship.TargetRows -ne $ExpectedTargetRows) {
        throw (
            "Target row count mismatch. Expected $ExpectedTargetRows, got " +
            "$($Relationship.TargetRows)"
        )
    }
    if ($Relationship.CanonicalRows -ne $ExpectedCanonicalRows) {
        throw (
            "Canonical row count mismatch. Expected $ExpectedCanonicalRows, got " +
            "$($Relationship.CanonicalRows)"
        )
    }
    if (
        $Relationship.CanonicalOnly -ne 0 -or
        $Relationship.CapMismatches -ne 0 -or
        $Relationship.LiveOnly.Count -ne $ExpectedRemovalRows
    ) {
        throw (
            'Target is not the expected strict canonical superset: ' +
            "live-only=$($Relationship.LiveOnly.Count), " +
            "canonical-only=$($Relationship.CanonicalOnly), " +
            "cap-mismatches=$($Relationship.CapMismatches)"
        )
    }
    foreach ($entry in $Relationship.LiveOnly.GetEnumerator()) {
        if (
            -not $evidenceMap.ContainsKey($entry.Key) -or
            [int]$evidenceMap[$entry.Key] -ne [int]$entry.Value
        ) {
            throw "Target live-only row is absent or different in evidence: $($entry.Key)"
        }
    }
}

function Assert-Canonical([object]$Relationship) {
    if (
        $Relationship.TargetRows -ne $ExpectedCanonicalRows -or
        $Relationship.CanonicalRows -ne $ExpectedCanonicalRows -or
        $Relationship.LiveOnly.Count -ne 0 -or
        $Relationship.CanonicalOnly -ne 0 -or
        $Relationship.CapMismatches -ne 0
    ) {
        throw (
            'Target does not exactly match canonical: ' +
            "target=$($Relationship.TargetRows), " +
            "canonical=$($Relationship.CanonicalRows), " +
            "live-only=$($Relationship.LiveOnly.Count), " +
            "canonical-only=$($Relationship.CanonicalOnly), " +
            "cap-mismatches=$($Relationship.CapMismatches)"
        )
    }
}

$before = Get-CanonicalRelationship
if ($Mode -eq 'Rollback') {
    Assert-Canonical $before
}
else {
    Assert-StrictSuperset $before
}

$sql = [System.Text.StringBuilder]::new()
[void]$sql.AppendLine("DROP PROCEDURE IF EXISTS ``$procedureName``;")
[void]$sql.AppendLine("DROP TABLE IF EXISTS ``$stagingTable``;")
[void]$sql.AppendLine(@"
CREATE TABLE $stagingTable (
  `skill_id` tinyint(3) unsigned NOT NULL,
  `class_id` tinyint(3) unsigned NOT NULL,
  `level` tinyint(3) unsigned NOT NULL,
  `cap` mediumint(8) unsigned NOT NULL,
  PRIMARY KEY (`skill_id`, `class_id`, `level`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
"@)

for ($offset = 0; $offset -lt $evidence.Count; $offset += 500) {
    $last = [Math]::Min($offset + 499, $evidence.Count - 1)
    $values = for ($index = $offset; $index -le $last; $index++) {
        $row = $evidence[$index]
        "($([int]$row.skill_id),$([int]$row.class_id),$([int]$row.level),$([int]$row.cap))"
    }
    [void]$sql.AppendLine(
        "INSERT INTO ``$stagingTable`` VALUES " + ($values -join ',') + ';'
    )
}

[void]$sql.AppendLine(
    "CREATE TABLE IF NOT EXISTS ``$BackupTable`` LIKE ``skill_caps``;"
)
if ($Mode -ne 'Rollback') {
    [void]$sql.AppendLine(@"
INSERT IGNORE INTO $BackupTable
SELECT sc.*
FROM `skill_caps` sc
JOIN $stagingTable rk
  ON rk.skill_id = sc.skill_id
 AND rk.class_id = sc.class_id
 AND rk.level = sc.level
 AND rk.cap = sc.cap;
"@)
}

[void]$sql.AppendLine('DELIMITER //')
[void]$sql.AppendLine("CREATE PROCEDURE ``$procedureName``()")
[void]$sql.AppendLine('BEGIN')
[void]$sql.AppendLine('  DECLARE v_target_rows INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_staging_rows INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_matching_rows INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_backup_rows INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_backup_matches INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_overlap_rows INT DEFAULT 0;')
[void]$sql.AppendLine('  DECLARE v_changed_rows INT DEFAULT 0;')
[void]$sql.AppendLine(
    "  SELECT COUNT(*) INTO v_staging_rows FROM ``$stagingTable``;"
)
[void]$sql.AppendLine(
    "  IF v_staging_rows <> $ExpectedRemovalRows THEN " +
    "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'staging row-count precondition failed'; END IF;"
)
[void]$sql.AppendLine(
    "  SELECT COUNT(*) INTO v_backup_rows FROM ``$BackupTable``;"
)
[void]$sql.AppendLine(
    "  IF v_backup_rows <> $ExpectedRemovalRows THEN " +
    "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'rollback-set row-count precondition failed'; END IF;"
)

if ($Mode -eq 'Rollback') {
    [void]$sql.AppendLine(@"
  SELECT COUNT(*) INTO v_backup_matches
  FROM $BackupTable backup
  JOIN $stagingTable rk
    ON rk.skill_id = backup.skill_id
   AND rk.class_id = backup.class_id
   AND rk.level = backup.level
   AND rk.cap = backup.cap;
"@)
    [void]$sql.AppendLine(
        "  IF v_backup_matches <> $ExpectedRemovalRows THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'rollback-set content precondition failed'; END IF;"
    )
    [void]$sql.AppendLine(
        '  SELECT COUNT(*) INTO v_target_rows FROM `skill_caps`;'
    )
    [void]$sql.AppendLine(
        "  IF v_target_rows <> $ExpectedCanonicalRows THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'canonical row-count precondition failed'; END IF;"
    )
    [void]$sql.AppendLine(@"
  SELECT COUNT(*) INTO v_overlap_rows
  FROM `skill_caps` sc
  JOIN $BackupTable backup
    ON backup.id = sc.id
    OR (
      backup.skill_id = sc.skill_id
      AND backup.class_id = sc.class_id
      AND backup.level = sc.level
    );
"@)
    [void]$sql.AppendLine(
        "  IF v_overlap_rows <> 0 THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'rollback collision precondition failed'; END IF;"
    )
    [void]$sql.AppendLine('  START TRANSACTION;')
    [void]$sql.AppendLine(
        "  INSERT INTO ``skill_caps`` SELECT * FROM ``$BackupTable``;"
    )
    [void]$sql.AppendLine('  SET v_changed_rows = ROW_COUNT();')
    [void]$sql.AppendLine(
        '  SELECT COUNT(*) INTO v_target_rows FROM `skill_caps`;'
    )
    [void]$sql.AppendLine(
        "  IF v_changed_rows <> $ExpectedRemovalRows OR " +
        "v_target_rows <> $ExpectedTargetRows THEN ROLLBACK; " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'rollback postcondition failed'; END IF;"
    )
    [void]$sql.AppendLine('  COMMIT;')
    [void]$sql.AppendLine(
        "  SELECT 'rollback_committed' AS migration_status, " +
        'v_changed_rows AS changed_rows, v_target_rows AS final_rows;'
    )
}
else {
    [void]$sql.AppendLine(@"
  SELECT COUNT(*) INTO v_backup_matches
  FROM $BackupTable backup
  JOIN `skill_caps` sc
    ON sc.id = backup.id
   AND sc.skill_id = backup.skill_id
   AND sc.class_id = backup.class_id
   AND sc.level = backup.level
   AND sc.cap = backup.cap
   AND sc.class_ = backup.class_;
"@)
    [void]$sql.AppendLine(
        "  IF v_backup_matches <> $ExpectedRemovalRows THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'rollback snapshot precondition failed'; END IF;"
    )
    [void]$sql.AppendLine(
        '  SELECT COUNT(*) INTO v_target_rows FROM `skill_caps`;'
    )
    [void]$sql.AppendLine(
        "  IF v_target_rows <> $ExpectedTargetRows THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'target row-count precondition failed'; END IF;"
    )
    [void]$sql.AppendLine(@"
  SELECT COUNT(*) INTO v_matching_rows
  FROM `skill_caps` sc
  JOIN $stagingTable rk
    ON rk.skill_id = sc.skill_id
   AND rk.class_id = sc.class_id
   AND rk.level = sc.level
   AND rk.cap = sc.cap;
"@)
    [void]$sql.AppendLine(
        "  IF v_matching_rows <> $ExpectedRemovalRows THEN " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'removal-set match precondition failed'; END IF;"
    )
    [void]$sql.AppendLine('  START TRANSACTION;')
    [void]$sql.AppendLine(@"
  DELETE sc
  FROM `skill_caps` sc
  JOIN $stagingTable rk
    ON rk.skill_id = sc.skill_id
   AND rk.class_id = sc.class_id
   AND rk.level = sc.level
   AND rk.cap = sc.cap;
"@)
    [void]$sql.AppendLine('  SET v_changed_rows = ROW_COUNT();')
    [void]$sql.AppendLine(
        '  SELECT COUNT(*) INTO v_target_rows FROM `skill_caps`;'
    )
    [void]$sql.AppendLine(
        "  IF v_changed_rows <> $ExpectedRemovalRows OR " +
        "v_target_rows <> $ExpectedCanonicalRows THEN ROLLBACK; " +
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'repair postcondition failed'; END IF;"
    )
    if ($Mode -eq 'DryRun') {
        [void]$sql.AppendLine('  ROLLBACK;')
        [void]$sql.AppendLine(
            "  SELECT 'dry_run_rolled_back' AS migration_status, " +
            'v_changed_rows AS changed_rows, v_target_rows AS tested_rows;'
        )
    }
    else {
        [void]$sql.AppendLine('  COMMIT;')
        [void]$sql.AppendLine(
            "  SELECT 'repair_committed' AS migration_status, " +
            'v_changed_rows AS changed_rows, v_target_rows AS final_rows;'
        )
    }
}

[void]$sql.AppendLine('END//')
[void]$sql.AppendLine('DELIMITER ;')
[void]$sql.AppendLine("CALL ``$procedureName``();")
[void]$sql.AppendLine("DROP PROCEDURE ``$procedureName``;")
[void]$sql.AppendLine("DROP TABLE ``$stagingTable``;")

$migrationId = [guid]::NewGuid().ToString('N')
$hostSql = Join-Path ([System.IO.Path]::GetTempPath()) `
    "nightcap-skill-cap-migration-$migrationId.sql"
$containerSql = "/tmp/nightcap-skill-cap-migration-$migrationId.sql"

try {
    [System.IO.File]::WriteAllText(
        $hostSql,
        $sql.ToString(),
        [System.Text.UTF8Encoding]::new($false)
    )
    & docker cp $hostSql "${TargetContainer}:$containerSql"
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to copy generated migration SQL into target container'
    }

    $result = @(
        & docker exec $TargetContainer bash -lc (
            "mysql -u$TargetUser -p$TargetPassword " +
            "$TargetDatabase < $containerSql"
        ) 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Migration SQL failed: $($result -join [Environment]::NewLine)"
    }
    $result
}
finally {
    if (Test-Path -LiteralPath $hostSql) {
        Remove-Item -LiteralPath $hostSql -Force
    }
    & docker exec $TargetContainer rm -f $containerSql 2>$null
}

$after = Get-CanonicalRelationship
if ($Mode -eq 'Apply') {
    Assert-Canonical $after
}
else {
    Assert-StrictSuperset $after
}

[pscustomobject]@{
    Mode = $Mode
    TargetContainer = $TargetContainer
    BeforeRows = $before.TargetRows
    AfterRows = $after.TargetRows
    CanonicalRows = $after.CanonicalRows
    EvidenceSha256 = $evidenceHash
    BackupTable = $BackupTable
    Verified = $true
}
