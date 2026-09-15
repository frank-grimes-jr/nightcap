# Read-only Phase 0 audit for Epic #10.
#
# Default mode reports class coverage and known contamination controls.
# Exact mode compares live skill_caps with a separately imported canonical table:
#   .\tools\audit-multiclass-skill-caps.ps1 -CanonicalTable skill_caps_canonical
#
# This script never imports, updates, or deletes database data.

[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z0-9_.-]+$')]
    [string]$Container = 'akk-stack-mariadb-1',
    [ValidatePattern('^[A-Za-z0-9_]+$')]
    [string]$Database = 'peq',
    [ValidatePattern('^[A-Za-z0-9_]+$')]
    [string]$CanonicalTable,
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-ReadOnlySql([string]$Query) {
    if ($Query -notmatch '^\s*(SELECT|SHOW|DESCRIBE|EXPLAIN)\b') {
        throw 'Audit queries must be read-only SELECT/SHOW/DESCRIBE/EXPLAIN statements.'
    }

    $rows = & docker exec $Container mysql -ueqemu -peqemu $Database `
        --batch --raw --skip-column-names -e $Query 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "MariaDB audit query failed: $($rows -join [Environment]::NewLine)"
    }

    return @($rows)
}

function Add-Section(
    [System.Collections.Generic.List[string]]$Report,
    [string]$Title,
    [string[]]$Rows
) {
    $Report.Add('')
    $Report.Add("## $Title")
    if ($Rows.Count -eq 0) {
        $Report.Add('(none)')
        return
    }

    foreach ($row in $Rows) {
        $Report.Add($row)
    }
}

$report = [System.Collections.Generic.List[string]]::new()
$report.Add("Nightcap multiclass skill_caps audit: $(Get-Date -Format s)")
$report.Add("Container=$Container Database=$Database")
$report.Add('READ-ONLY: no database changes were attempted.')

$tableExists = Invoke-ReadOnlySql @"
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = '$Database' AND table_name = 'skill_caps';
"@
if ($tableExists[0] -ne '1') {
    throw "Table $Database.skill_caps does not exist."
}

Add-Section $report 'Live class coverage (class_id, distinct skills, rows)' `
    (Invoke-ReadOnlySql @'
SELECT class_id, COUNT(DISTINCT skill_id), COUNT(*)
FROM skill_caps
GROUP BY class_id
ORDER BY class_id;
'@)

Add-Section $report 'Heuristic contamination controls (skill_id, class_id, first level, last level, rows)' `
    (Invoke-ReadOnlySql @'
SELECT skill_id, class_id, MIN(level), MAX(level), COUNT(*)
FROM skill_caps
WHERE class_id = 1 AND skill_id IN (4, 5, 13, 14, 18, 24)
GROUP BY skill_id, class_id
ORDER BY skill_id;
'@)

$report.Add('')
$report.Add('NOTE: heuristic controls prove contamination but are not a migration diff.')

if ($CanonicalTable) {
    $canonicalExists = Invoke-ReadOnlySql @"
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = '$Database' AND table_name = '$CanonicalTable';
"@
    if ($canonicalExists[0] -ne '1') {
        throw "Canonical comparison table $Database.$CanonicalTable does not exist."
    }

    $requiredColumns = Invoke-ReadOnlySql @"
SELECT COUNT(*)
FROM information_schema.columns
WHERE table_schema = '$Database'
  AND table_name = '$CanonicalTable'
  AND column_name IN ('skill_id', 'class_id', 'level', 'cap');
"@
    if ($requiredColumns[0] -ne '4') {
        throw 'Canonical comparison table must contain skill_id, class_id, level, and cap.'
    }

    Add-Section $report 'Live-only rows (skill_id, class_id, level, cap)' `
        (Invoke-ReadOnlySql @"
SELECT live.skill_id, live.class_id, live.level, live.cap
FROM skill_caps AS live
LEFT JOIN $CanonicalTable AS canonical
  ON canonical.skill_id = live.skill_id
 AND canonical.class_id = live.class_id
 AND canonical.level = live.level
WHERE canonical.skill_id IS NULL
ORDER BY live.class_id, live.skill_id, live.level;
"@)

    Add-Section $report 'Canonical-only rows (skill_id, class_id, level, cap)' `
        (Invoke-ReadOnlySql @"
SELECT canonical.skill_id, canonical.class_id, canonical.level, canonical.cap
FROM $CanonicalTable AS canonical
LEFT JOIN skill_caps AS live
  ON live.skill_id = canonical.skill_id
 AND live.class_id = canonical.class_id
 AND live.level = canonical.level
WHERE live.skill_id IS NULL
ORDER BY canonical.class_id, canonical.skill_id, canonical.level;
"@)

    Add-Section $report 'Cap mismatches (skill_id, class_id, level, live cap, canonical cap)' `
        (Invoke-ReadOnlySql @"
SELECT live.skill_id, live.class_id, live.level, live.cap, canonical.cap
FROM skill_caps AS live
JOIN $CanonicalTable AS canonical
  ON canonical.skill_id = live.skill_id
 AND canonical.class_id = live.class_id
 AND canonical.level = live.level
WHERE live.cap <> canonical.cap
ORDER BY live.class_id, live.skill_id, live.level;
"@)
}

$reportText = $report -join [Environment]::NewLine
Write-Output $reportText

if ($OutputPath) {
    $resolvedParent = Split-Path -Parent $OutputPath
    if ($resolvedParent -and -not (Test-Path $resolvedParent)) {
        New-Item -ItemType Directory -Path $resolvedParent -Force | Out-Null
    }
    Set-Content -LiteralPath $OutputPath -Value $reportText -Encoding utf8
    Write-Output "Audit report written to $OutputPath"
}
