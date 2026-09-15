[CmdletBinding()]
param(
    [string]$TargetContainer = 'nightcap-peq-rehearsal',
    [string]$TargetDatabase = 'peq',
    [string]$TargetUser = 'eqemu',
    [string]$TargetPassword = 'rehearsal-eqemu',
    [string]$CanonicalContainer = 'nightcap-peq-baseline',
    [string]$CanonicalDatabase = 'peq',
    [string]$CanonicalUser = 'eqemu',
    [string]$CanonicalPassword = 'baseline-eqemu'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repairScript = Join-Path $PSScriptRoot '..\repair-multiclass-skill-caps.ps1'
$compareScript = Join-Path $PSScriptRoot '..\compare-multiclass-skill-caps.ps1'

if (-not (Test-Path -LiteralPath $repairScript)) {
    throw "Repair script does not exist: $repairScript"
}

function Invoke-TargetScalar([string]$Sql) {
    $result = @(
        & docker exec $TargetContainer mysql "-u$TargetUser" "-p$TargetPassword" `
            $TargetDatabase --batch --raw --skip-column-names -e $Sql 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Target query failed: $($result -join [Environment]::NewLine)"
    }
    return [string]$result[0]
}

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) {
        throw "$Message. Expected [$Expected], got [$Actual]."
    }
}

function Invoke-Repair([string]$Mode) {
    & $repairScript `
        -TargetContainer $TargetContainer `
        -TargetDatabase $TargetDatabase `
        -TargetUser $TargetUser `
        -TargetPassword $TargetPassword `
        -Mode $Mode
    if ($LASTEXITCODE -ne 0) {
        throw "Repair mode $Mode failed with exit code $LASTEXITCODE"
    }
}

Assert-Equal '74449' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'Fresh restored copy must begin with the widened live row count'

$guardFailed = $false
try {
    & $repairScript `
        -TargetContainer $TargetContainer `
        -TargetDatabase $TargetDatabase `
        -TargetUser $TargetUser `
        -TargetPassword $TargetPassword `
        -ExpectedTargetRows 1 `
        -Mode Apply 2>$null
}
catch {
    $guardFailed = $true
}
if (-not $guardFailed) {
    throw 'Apply must fail closed when the expected target count is wrong'
}
Assert-Equal '74449' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'A failed precondition must not mutate skill_caps'

Invoke-Repair DryRun
Assert-Equal '74449' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'DryRun must roll back the deletion'
Assert-Equal '16090' (
    Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps_epic10_removed;'
) 'DryRun must retain an exact rollback set'

Invoke-Repair Apply
Assert-Equal '58359' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'Apply must leave the canonical row count'

$comparisonDirectory = Join-Path ([System.IO.Path]::GetTempPath()) (
    'nightcap-skill-cap-test-' + [guid]::NewGuid().ToString('N')
)
try {
    & $compareScript `
        -LiveContainer $TargetContainer `
        -LiveDatabase $TargetDatabase `
        -LiveUser $TargetUser `
        -LivePassword $TargetPassword `
        -CanonicalContainer $CanonicalContainer `
        -CanonicalDatabase $CanonicalDatabase `
        -CanonicalUser $CanonicalUser `
        -CanonicalPassword $CanonicalPassword `
        -OutputDirectory $comparisonDirectory
    if ($LASTEXITCODE -ne 0) {
        throw 'Repaired rehearsal table does not exactly match canonical'
    }

    $summary = Get-Content -LiteralPath (
        Join-Path $comparisonDirectory 'summary.txt'
    )
    Assert-Equal $true ($summary -contains 'live_only_rows=0') `
        'Repaired table must have no live-only rows'
    Assert-Equal $true ($summary -contains 'canonical_only_rows=0') `
        'Repaired table must have no canonical-only rows'
    Assert-Equal $true ($summary -contains 'cap_mismatches=0') `
        'Repaired table must have no cap mismatches'
}
finally {
    if (Test-Path -LiteralPath $comparisonDirectory) {
        Remove-Item -LiteralPath $comparisonDirectory -Recurse -Force
    }
}

Invoke-Repair Rollback
Assert-Equal '74449' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'Rollback must restore the exact widened row count'

Invoke-Repair Apply
Assert-Equal '58359' (Invoke-TargetScalar 'SELECT COUNT(*) FROM skill_caps;') `
    'A second apply after rollback must succeed deterministically'

'PASS: guarded dry-run, apply, exact comparison, rollback, and reapply'
