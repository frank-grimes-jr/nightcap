[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$source = Get-Content -LiteralPath (
    Join-Path $repoRoot 'server-mods\code\zone\client_process.cpp'
) -Raw

function Get-FunctionBody([string]$Name, [string]$NextName) {
    $start = $source.IndexOf("void Client::$Name")
    $end = $source.IndexOf("void Client::$NextName", $start + 1)
    if ($start -lt 0 -or $end -lt 0) {
        throw "Unable to isolate $Name"
    }
    return $source.Substring($start, $end - $start)
}

$open = Get-FunctionBody 'OPGMTraining' 'OPGMEndTraining'
$train = Get-FunctionBody 'OPGMTrainSkill' 'OPGMSummon'

if ($open -notmatch 'SkillCaps::CanUseTrainer') {
    throw 'Opening a trainer must use held-class trainer authorization'
}
if ($train -notmatch 'SkillCaps::CanUseTrainer') {
    throw 'Training requests must use held-class trainer authorization'
}
if ($open -match 'MaxSkill\([^\r\n]+RuleI\(Character,\s*MaxLevel\)') {
    throw 'Trainer display must not expose future max-level skill caps'
}
if ($open -notmatch 'MaxSkill\([^\r\n]+GetLevel\(\)') {
    throw 'Trainer display must use the character current level'
}
if ($train -notmatch 'ResolveHeldSkillEligibility') {
    throw 'Training requests must resolve current eligibility across held classes'
}
if ($train -notmatch 'EvaluateSkillTraining') {
    throw 'Training requests must use the tested points/cap/currency decision'
}
if ($train -notmatch 'SetSkill\(skill,\s*skilllevel == 0 \? 1 : skilllevel \+ 1\)') {
    throw 'A trainer must open a zero-valued skill at exactly value 1'
}

$decision = $train.IndexOf('EvaluateSkillTraining')
$payment = $train.IndexOf('TakeMoneyFromPP(Cost)', $decision)
$mutation = $train.IndexOf('SetSkill(skill, skilllevel == 0 ? 1 : skilllevel + 1)')
if (
    $decision -lt 0 -or
    $payment -lt $decision -or
    $mutation -lt 0 -or
    $payment -gt $mutation
) {
    throw 'Skill training must collect payment before mutating the skill'
}

'PASS: held-class trainers enforce current unlocks, caps, points, and funds'
