[CmdletBinding()]
param(
	[string]$Source
)

$ErrorActionPreference = "Stop"
if (-not $Source) {
	$Source = Join-Path $PSScriptRoot "..\..\akk-stack\code\zone\special_attacks.cpp"
}

$resolvedSource = [System.IO.Path]::GetFullPath($Source)
$content = [System.IO.File]::ReadAllText($resolvedSource)

$requiredFragments = @(
	"const auto held_classes = GetMulticlassList();",
	"MaxSkill(skill, held_class, GetLevel())",
	"EQ::skills::CanUseMonkCombatAbility(",
	"can_use_kick &&",
	"!can_use_monk",
	"if (can_use_monk) {"
)

foreach ($fragment in $requiredFragments) {
	if (-not $content.Contains($fragment)) {
		throw "Missing Monk combat integration fragment: $fragment"
	}
}

if ($content.Contains("if (class_id == Class::Monk) {")) {
	throw "The base-class-only Monk combat gate is still present."
}

& (Join-Path $PSScriptRoot "..\apply-multiclass-monk-combat.ps1") -Target $resolvedSource -Check
Write-Host "Monk multiclass combat integration checks passed."
