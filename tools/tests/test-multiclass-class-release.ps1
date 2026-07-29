[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$aaSource = Get-Content -LiteralPath (
    Join-Path $repoRoot 'server-mods\code\zone\aa.cpp'
) -Raw
$plugin = Get-Content -LiteralPath (
    Join-Path $repoRoot 'server-mods\plugins\multiclass.pl'
) -Raw

$start = $aaSource.IndexOf('void Client::PurgeAfterClassRelease')
$end = $aaSource.IndexOf('SwarmPet::SwarmPet', $start)
if ($start -lt 0 -or $end -lt 0) {
    throw 'Unable to isolate PurgeAfterClassRelease'
}
$purge = $aaSource.Substring($start, $end - $start)

function Assert-Ordered(
    [string]$Text,
    [string]$First,
    [string]$Second,
    [string]$Message
) {
    $firstIndex = $Text.IndexOf($First)
    $secondIndex = $Text.IndexOf($Second)
    if ($firstIndex -lt 0 -or $secondIndex -lt 0 -or $firstIndex -gt $secondIndex) {
        throw $Message
    }
}

Assert-Ordered $purge 'LoadMulticlassMask();' 'GetMulticlassList()' `
    'Release cleanup must reload the retained-class mask before evaluating skills'
if ($purge -notmatch 'ability->classes\s*&\s*mask') {
    throw 'AAs shared with a retained class must survive release cleanup'
}
if ($purge -notmatch 'for\s*\(uint8 c : GetMulticlassList\(\)\)') {
    throw 'Skill cleanup must evaluate only the retained held classes'
}
if ($purge -notmatch 'if\s*\(current > retained_cap\)\s*\{\s*SetSkill\(skill,\s*retained_cap\)') {
    throw 'Unique skills must drop to zero and over-cap shared skills must clamp'
}
if ($purge -match 'SetSkill\(skill,\s*retained_cap\)\s*;\s*\}\s*else') {
    throw 'Shared skills already under the retained cap must not be rewritten'
}
Assert-Ordered $purge 'database.DeleteCharacterAAs' 'SaveAA();' `
    'Removed AAs must be deleted before retained AAs are persisted'
Assert-Ordered $purge 'SendClearPlayerAA();' 'SendAlternateAdvancementTable();' `
    'The client AA list must be cleared before retained AAs are repopulated'

$update = $plugin.IndexOf('UPDATE character_multiclass SET')
$call = $plugin.IndexOf('$client->PurgeAfterClassRelease($revoked);')
if ($update -lt 0 -or $call -lt 0 -or $update -gt $call) {
    throw 'The database slot release must complete before live cleanup reloads the mask'
}

'PASS: class release removes unique capabilities and retains legal shared skills'
