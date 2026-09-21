[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))

function Read-RepoFile([string]$RelativePath) {
    return Get-Content -LiteralPath (Join-Path $repoRoot $RelativePath) -Raw
}

function Assert-Contains(
    [string]$Text,
    [string]$Pattern,
    [string]$Message
) {
    if ($Text -notmatch $Pattern) {
        throw $Message
    }
}

$clientHeader = Read-RepoFile 'server-mods\code\zone\client.h'
$clientSource = Read-RepoFile 'server-mods\code\zone\client.cpp'
$aaSource = Read-RepoFile 'server-mods\code\zone\aa.cpp'
$expSource = Read-RepoFile 'server-mods\code\zone\exp.cpp'
$perlBinding = Read-RepoFile 'server-mods\code\zone\perl_client.cpp'
$plugin = Read-RepoFile 'server-mods\plugins\multiclass.pl'
$globalLua = Read-RepoFile 'server-mods\quests\global\global_player.lua'

Assert-Contains $clientHeader 'uint32\s+ReconcileMulticlassSkills\(\);' `
    'Client must expose one authoritative multiclass skill reconciler'
Assert-Contains $clientSource 'uint32\s+Client::ReconcileMulticlassSkills\(\)' `
    'Client must implement the authoritative multiclass skill reconciler'
Assert-Contains $clientSource 'CollectNativeSkillSeeds' `
    'Client reconciler must use the tested native seed selector'
Assert-Contains $clientSource 'SetSkill\(skill,\s*1\)' `
    'Client reconciler must seed eligible skills at value 1'
Assert-Contains $clientSource 'ReconcileMulticlassSkills\(\);\s*\r?\n\s*RefreshClassPets' `
    'Zone-in must reconcile immediately after loading character data'
$nativeAdoptionStart = $aaSource.IndexOf('void Client::SetMulticlassSlot(')
$nativeAdoptionEnd = $aaSource.IndexOf('void Mob::TemporaryPets(', $nativeAdoptionStart)
if ($nativeAdoptionStart -lt 0 -or $nativeAdoptionEnd -lt $nativeAdoptionStart) {
    throw 'Unable to locate native class adoption'
}
$nativeAdoption = $aaSource.Substring($nativeAdoptionStart, $nativeAdoptionEnd - $nativeAdoptionStart)
Assert-Contains $nativeAdoption 'ReconcileMulticlassSkills\(\);' `
    'C++ class adoption must use the shared skill and capability reconciler'
Assert-Contains $perlBinding 'package\.add\("ReconcileMulticlassSkills"' `
    'Perl adoption must have a binding to the authoritative reconciler'
Assert-Contains $plugin '\$client->ReconcileMulticlassSkills\(\);' `
    'The production adoption plugin must reconcile immediately'

$setLevelStart = $expSource.IndexOf('void Client::SetLevel')
$levelAssignment = $expSource.IndexOf('level = set_level;', $setLevelStart)
$levelEvent = $expSource.IndexOf('EVENT_LEVEL_UP', $setLevelStart)
$levelReconcile = $expSource.IndexOf('ReconcileMulticlassSkills();', $setLevelStart)
if (
    $setLevelStart -lt 0 -or
    $levelAssignment -lt $setLevelStart -or
    $levelReconcile -lt $levelAssignment -or
    $levelReconcile -gt $levelEvent
) {
    throw 'Level-up must reconcile after setting the new level and before EVENT_LEVEL_UP'
}

$eventLevelStart = $globalLua.IndexOf('function event_level_up')
$eventLevelEnd = $globalLua.IndexOf("`nend", $eventLevelStart)
if ($eventLevelStart -lt 0 -or $eventLevelEnd -lt 0) {
    throw 'Unable to locate Lua event_level_up'
}
$eventLevelBody = $globalLua.Substring(
    $eventLevelStart,
    $eventLevelEnd - $eventLevelStart
)
if ($eventLevelBody -match 'free_skills|SetSkill') {
    throw 'Lua event_level_up must not retain a second skill-seeding policy'
}

'PASS: zone-in, C++/Perl adoption, and level-up use one value-1 reconciler'
