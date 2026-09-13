# Generates the Epic #10 SkillUseTypes acquisition policy table from C++ source.

[CmdletBinding()]
param(
    [string]$SourceRoot,
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $SourceRoot) {
    $SourceRoot = Join-Path $PSScriptRoot '..\akk-stack\code'
}
if (-not $OutputPath) {
    $OutputPath = Join-Path $PSScriptRoot '..\docs\audits\multiclass-skill-acquisition.csv'
}

$skillsCpp = Get-Content (Join-Path $SourceRoot 'common\skills.cpp') -Raw

$mapMatch = [regex]::Match(
    $skillsCpp,
    'GetSkillTypeMap\(\).*?skill_type_map\s*=\s*\{(?<body>.*?)\n\t\};',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $mapMatch.Success) {
    throw 'Could not locate GetSkillTypeMap in common/skills.cpp.'
}

$skillMatches = [regex]::Matches(
    $mapMatch.Groups['body'].Value,
    '\{\s*(Skill[A-Za-z0-9]+),\s*"([^"]+)"\s*\}'
)
if ($skillMatches.Count -ne 78) {
    throw "Expected 78 RoF2 skills, found $($skillMatches.Count)."
}

$policyMatch = [regex]::Match(
    $skillsCpp,
    'GetSkillAcquisition\(SkillType skill\).*?switch \(skill\) \{(?<body>.*?)default:',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $policyMatch.Success) {
    throw 'Could not locate GetSkillAcquisition policy in common/skills.cpp.'
}

$stockSkills = @{}
foreach ($match in [regex]::Matches($policyMatch.Groups['body'].Value, 'case (Skill[A-Za-z0-9]+):')) {
    $stockSkills[$match.Groups[1].Value] = $true
}

$rows = for ($skillId = 0; $skillId -lt $skillMatches.Count; ++$skillId) {
    $enumName = $skillMatches[$skillId].Groups[1].Value
    $displayName = $skillMatches[$skillId].Groups[2].Value
    $isStock = $stockSkills.ContainsKey($enumName)

    $restriction = if ($enumName -eq 'SkillTinkering') {
        'stock acquisition; Gnome race restriction'
    } elseif ($enumName -in @(
        'SkillSenseHeading',
        'SkillSwimming',
        'SkillFishing',
        'SkillAlcoholTolerance'
    )) {
        'stock acquisition through normal use'
    } elseif ($isStock) {
        'stock universal tradeskill acquisition and recipe rules'
    } elseif ($enumName -eq 'SkillAlchemy') {
        'native held Shaman cap/level; minimum level and recipe rules'
    } elseif ($enumName -eq 'SkillMakePoison') {
        'native held Rogue cap/level; recipe rules'
    } elseif ($enumName -eq 'SkillResearch') {
        'native held-class cap/level; recipe rules'
    } elseif ($enumName -like 'SkillSpecialize*') {
        'native held-class cap/level; stock specialization limits'
    } else {
        'native held-class cap and unlock level'
    }

    [pscustomobject][ordered]@{
        skill_id       = $skillId
        enum_name      = $enumName
        skill_name     = $displayName
        acquisition    = if ($isStock) { 'stock_acquisition' } else { 'auto_grant_at_native_unlock' }
        restrictions   = $restriction
        automated_test = if ($isStock) {
            'SkillsUtilsTest::SkillAcquisitionPolicy'
        } else {
            'SkillsUtilsTest::SkillAcquisitionPolicy; SkillsUtilsTest::ShouldSeedAtNativeUnlock'
        }
    }
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8
Write-Output "Wrote $($rows.Count) skill acquisition rows to $OutputPath"
