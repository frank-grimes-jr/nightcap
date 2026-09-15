# Exact, read-only comparison of live and isolated canonical skill_caps tables.

[CmdletBinding()]
param(
    [string]$LiveContainer = 'akk-stack-mariadb-1',
    [string]$LiveDatabase = 'peq',
    [string]$LiveUser = 'eqemu',
    [string]$LivePassword = 'eqemu',
    [string]$CanonicalContainer = 'nightcap-peq-baseline',
    [string]$CanonicalDatabase = 'peq',
    [string]$CanonicalUser = 'eqemu',
    [string]$CanonicalPassword = 'baseline-eqemu',
    [string]$OutputDirectory,
    [string]$BaselineSource = 'https://gitlab.com/TheGrandLibrary/db.projecteq.net-dumps/-/package_files/232952944/download',
    [string]$BaselineSha256 = 'ac8649f23d2c3aea2cade138dfe10d46d1b21ad1a80d08ca95f5434fab7f218d'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot '..\docs\audits\skill-caps-diff'
}

foreach ($value in @(
    $LiveContainer,
    $LiveDatabase,
    $LiveUser,
    $CanonicalContainer,
    $CanonicalDatabase,
    $CanonicalUser
)) {
    if ($value -notmatch '^[A-Za-z0-9_.-]+$') {
        throw "Unsafe container/database/user argument: $value"
    }
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
    $ordered = [System.Collections.Generic.List[object]]::new()
    foreach ($row in $rows) {
        $parts = $row -split "`t"
        if ($parts.Count -ne 4) {
            throw "Unexpected skill_caps row from ${Container}: $row"
        }

        $record = [pscustomobject][ordered]@{
            skill_id = [int]$parts[0]
            class_id = [int]$parts[1]
            level    = [int]$parts[2]
            cap      = [int]$parts[3]
        }
        $key = "$($record.skill_id)|$($record.class_id)|$($record.level)"
        if ($map.ContainsKey($key)) {
            throw "Duplicate composite key in ${Container}: $key"
        }
        $map[$key] = $record
        $ordered.Add($record)
    }

    return [pscustomobject]@{ Map = $map; Ordered = $ordered }
}

$live = Read-SkillCaps $LiveContainer $LiveDatabase $LiveUser $LivePassword
$canonical = Read-SkillCaps $CanonicalContainer $CanonicalDatabase $CanonicalUser $CanonicalPassword

$liveOnly = [System.Collections.Generic.List[object]]::new()
$canonicalOnly = [System.Collections.Generic.List[object]]::new()
$capMismatches = [System.Collections.Generic.List[object]]::new()

foreach ($record in $live.Ordered) {
    $key = "$($record.skill_id)|$($record.class_id)|$($record.level)"
    if (-not $canonical.Map.ContainsKey($key)) {
        $liveOnly.Add($record)
        continue
    }
    if ($record.cap -ne $canonical.Map[$key].cap) {
        $capMismatches.Add(
            [pscustomobject][ordered]@{
                skill_id      = $record.skill_id
                class_id      = $record.class_id
                level         = $record.level
                live_cap      = $record.cap
                canonical_cap = $canonical.Map[$key].cap
            }
        )
    }
}

foreach ($record in $canonical.Ordered) {
    $key = "$($record.skill_id)|$($record.class_id)|$($record.level)"
    if (-not $live.Map.ContainsKey($key)) {
        $canonicalOnly.Add($record)
    }
}

function Write-DiffCsv(
    [System.Collections.ICollection]$Rows,
    [string]$Path,
    [string]$EmptyHeader
) {
    if ($Rows.Count -eq 0) {
        Set-Content -LiteralPath $Path -Value $EmptyHeader -Encoding utf8
    } else {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding utf8
    }
}

$verdict = if (
    $liveOnly.Count -eq 0 -and
    $canonicalOnly.Count -eq 0 -and
    $capMismatches.Count -eq 0
) {
    'exact_canonical_match'
} elseif ($canonicalOnly.Count -eq 0 -and $capMismatches.Count -eq 0) {
    'strict_live_superset_repair_candidate'
} else {
    'divergence_blocks_migration'
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
Write-DiffCsv $liveOnly (Join-Path $OutputDirectory 'live-only.csv') '"skill_id","class_id","level","cap"'
Write-DiffCsv $canonicalOnly (Join-Path $OutputDirectory 'canonical-only.csv') '"skill_id","class_id","level","cap"'
Write-DiffCsv $capMismatches (Join-Path $OutputDirectory 'cap-mismatches.csv') '"skill_id","class_id","level","live_cap","canonical_cap"'

$summary = @(
    "baseline_source=$BaselineSource",
    "baseline_sha256=$BaselineSha256",
    "live_container=$LiveContainer",
    "canonical_container=$CanonicalContainer",
    "live_rows=$($live.Map.Count)",
    "canonical_rows=$($canonical.Map.Count)",
    "live_only_rows=$($liveOnly.Count)",
    "canonical_only_rows=$($canonicalOnly.Count)",
    "cap_mismatches=$($capMismatches.Count)",
    "verdict=$verdict"
)
$summary | Set-Content (Join-Path $OutputDirectory 'summary.txt') -Encoding utf8
$summary

if ($verdict -eq 'divergence_blocks_migration') {
    exit 2
}
