# Generates the exhaustive Epic #10 class x held-slot x capability matrix.

[CmdletBinding()]
param(
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $OutputPath) {
    $OutputPath = Join-Path $PSScriptRoot '..\docs\audits\multiclass-acceptance-matrix.csv'
}

$classes = [ordered]@{
    1  = 'Warrior'
    2  = 'Cleric'
    3  = 'Paladin'
    4  = 'Ranger'
    5  = 'ShadowKnight'
    6  = 'Druid'
    7  = 'Monk'
    8  = 'Bard'
    9  = 'Rogue'
    10 = 'Shaman'
    11 = 'Necromancer'
    12 = 'Wizard'
    13 = 'Magician'
    14 = 'Enchanter'
    15 = 'Beastlord'
    16 = 'Berserker'
}

$slots = @('primary', 'secondary', 'tertiary')
$capabilities = [ordered]@{
    'skill_lifecycle'         = 'server-skills'
    'trainer'                 = 'server-skills/client-trainer'
    'activated_combat_skill'  = 'server-combat/client-abilities'
    'passive_innate'          = 'server-passives'
    'spellbook_and_casting'   = 'server-spells/client-spellbook'
    'discipline'              = 'server-disciplines/client-abilities'
    'alternate_advancement'   = 'server-aa/client-aa'
    'equipment'               = 'server-items/client-equipment'
    'stats_and_resources'     = 'server-stats/client-hud'
    'persistence_and_release' = 'server-persistence'
}

$rows = foreach ($classEntry in $classes.GetEnumerator()) {
    foreach ($slot in $slots) {
        foreach ($capabilityEntry in $capabilities.GetEnumerator()) {
            [pscustomobject][ordered]@{
                class_id          = $classEntry.Key
                class_name        = $classEntry.Value
                held_slot         = $slot
                capability        = $capabilityEntry.Key
                expected          = 'held_class_parity'
                owner             = $capabilityEntry.Value
                automated_evidence = 'pending'
                manual_evidence   = 'pending'
                status            = 'planned'
            }
        }
    }
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8
Write-Output "Wrote $($rows.Count) acceptance rows to $OutputPath"
