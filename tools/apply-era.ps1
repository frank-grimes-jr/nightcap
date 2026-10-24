# Declarative era lock for the Nightcap server. Source of truth: E:\EQ_Local_Dev\era.json
#
#   apply-era.ps1                  apply era.json to the live server (idempotent) + restart all zones
#   apply-era.ps1 -CapCharacters   also de-level characters above max_level (destructive; off by default)
#   apply-era.ps1 -Check           report drift between era.json and live state; exit 1 on drift
#
# Changing era = edit era.json, commit, run this script. The GM tool button (if revived)
# should invoke this script rather than writing DB state itself.

param(
    [switch]$Check,
    [switch]$CapCharacters
)

$ErrorActionPreference = 'Stop'

$Root    = Split-Path -Parent $PSScriptRoot
$Era     = Get-Content (Join-Path $Root 'era.json') -Raw | ConvertFrom-Json
$Ini     = Join-Path $Root 'Client_RoF2_Dev\everquest_rof2\eqclient.ini'
$AAOpen  = if ($Era.aa_open) { 'false' } else { 'true' }   # rule is UseCurrentExpansionAAOnly (inverted)
$Luclin  = if ($Era.luclin_models) { 'FALSE' } else { 'TRUE' } # ini key is AllLuclinPcModelsOff (inverted)

if ($Era.aa_policy) {
    if ($Era.aa_policy -ne 'config/aa-policy.json') { throw 'Unsupported AA policy source.' }
    python -B (Join-Path $Root 'tools/aa_tbs_policy.py') --check
    if ($LASTEXITCODE -ne 0) { throw 'AA policy generation is stale; no era changes applied.' }
    Write-Output 'AA policy source verified. Installing/changing this policy requires the matching zone build; era SQL does not install it.'
}

function Sql($query) {
    docker exec akk-stack-mariadb-1 mysql -ueqemu -peqemu peq -N -e $query
    if ($LASTEXITCODE -ne 0) { throw "Era SQL failed; further changes and restarts stopped." }
}

# An exception is installed only by its guarded, paired content migration.
# Era apply validates its declaration; it never opens the rest of Rain of Fear.
if ($Era.zone_exception_policy) {
    if ($Era.zone_exception_policy -ne 'config/chapterhouse-access.json') { throw 'Unsupported zone exception policy.' }
    python -B -c "import sys; sys.path.insert(0, sys.argv[1]); from chapterhouse_content import access_policy; access_policy()" $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { throw 'Invalid Chapterhouse policy; no era changes applied.' }
    Write-Output 'Chapterhouse candidate policy verified. Activation is a separate paired content release.'
}

if ($Era.additional_zone_exception_policies) {
    if (@($Era.additional_zone_exception_policies).Count -ne 1 -or $Era.additional_zone_exception_policies[0] -ne 'config/warhelm-access.json') { throw 'Unsupported additional zone policy.' }
    python -B -c "import sys; sys.path.insert(0, sys.argv[1]); from warhelm_content import access_policy; access_policy()" $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { throw 'Invalid Warhelm policy; no era changes applied.' }
    Write-Output 'Warhelm policy verified. Activation requires its paired content and client release.'
}

if ($Check) {
    $drift = 0
    $live = @{}
    (Sql "SELECT rule_name, rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name IN ('Expansion:CurrentExpansion','Character:MaxLevel','Character:MaxExpLevel','Expansion:UseCurrentExpansionAAOnly');") |
        ForEach-Object { $p = $_ -split "`t"; $live[$p[0]] = $p[1] }
    $expect = @{
        'Expansion:CurrentExpansion'          = [string]$Era.expansion
        'Character:MaxLevel'                  = [string]$Era.max_level
        'Character:MaxExpLevel'               = [string]$Era.max_level
        'Expansion:UseCurrentExpansionAAOnly' = $AAOpen
    }
    foreach ($k in $expect.Keys) {
        if ($live[$k] -ne $expect[$k]) { Write-Output "DRIFT $k = '$($live[$k])' (era.json says '$($expect[$k])')"; $drift++ }
    }
    $over = Sql "SELECT COUNT(*) FROM character_data WHERE deleted_at IS NULL AND level > $($Era.max_level);"
    if ([int]$over -gt 0) { Write-Output "DRIFT $over character(s) above level $($Era.max_level)"; $drift++ }
    if ((Test-Path $Ini) -and -not (Select-String -Path $Ini -Pattern "AllLuclinPcModelsOff=$Luclin" -Quiet)) {
        Write-Output "DRIFT eqclient.ini AllLuclinPcModelsOff != $Luclin"; $drift++
    }
    if ($drift -eq 0) { Write-Output "OK era matches era.json ($($Era.name), expansion $($Era.expansion), cap $($Era.max_level))"; exit 0 }
    exit 1
}

$VendorRestock = Get-Content (Join-Path $Root 'eq-solo-gm\scripts\vendor_restock.sql') -Raw
. (Join-Path $PSScriptRoot 'pok-hub-era.ps1')
Assert-PokHubEra -Era $Era -ReadSql ${function:Sql}

# -- Apply ---------------------------------------------------------------------
Sql "UPDATE rule_values SET rule_value='$($Era.expansion)' WHERE ruleset_id=1 AND rule_name='Expansion:CurrentExpansion';"
Sql "UPDATE rule_values SET rule_value='$($Era.max_level)' WHERE ruleset_id=1 AND rule_name IN ('Character:MaxLevel','Character:MaxExpLevel');"
Sql "UPDATE rule_values SET rule_value='$AAOpen' WHERE ruleset_id=1 AND rule_name='Expansion:UseCurrentExpansionAAOnly';"
Sql "UPDATE variables SET value='[Nightcap] Era: $($Era.name) - Level Cap $($Era.max_level)' WHERE varname='MOTD';"
Write-Output "rules + MOTD set: $($Era.name) (expansion $($Era.expansion)), cap $($Era.max_level), AA open=$($Era.aa_open)"

if ($CapCharacters) {
    Sql "UPDATE character_data SET level=$($Era.max_level), level2=$($Era.max_level), exp=0 WHERE deleted_at IS NULL AND level > $($Era.max_level);"
    Write-Output "characters above $($Era.max_level) capped (make sure they were logged out)"
} else {
    $over = Sql "SELECT COUNT(*) FROM character_data WHERE deleted_at IS NULL AND level > $($Era.max_level);"
    if ([int]$over -gt 0) { Write-Output "WARN: $over character(s) above cap - re-run with -CapCharacters (log them out first)" }
}

if (Test-Path $Ini) {
    $content = Get-Content $Ini -Raw
    $new = $content -replace 'AllLuclinPcModelsOff=(TRUE|FALSE)', "AllLuclinPcModelsOff=$Luclin"
    if ($new -ne $content) { Set-Content -Path $Ini -Value $new -Encoding ASCII; Write-Output "eqclient.ini: AllLuclinPcModelsOff=$Luclin" }
}

# Restock the PoK spell vendors against the (possibly changed) level cap.
# History: the GM tool's refresh once wiped a vendor (see CHANGES 2026-07-14).
$VendorRestock |
    docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq
if ($LASTEXITCODE -ne 0) { throw 'Spell restock failed; zone restart stopped. Inspect the error before continuing.' }
Write-Output 'spell vendors restocked for the era level cap'

# Restart every zone so all spawn lists rebuild under the new era (processes cache era at boot).
# pgrep -x matches the exact process name 'zone' - safe from matching this shell itself.
docker exec akk-stack-eqemu-server-1 bash -c 'pgrep -x zone | xargs -r kill'
Write-Output "all zone processes killed - eqlaunch respawns them under the new era"
Write-Output "Reminder: record the era change in CHANGES.md and commit era.json"
