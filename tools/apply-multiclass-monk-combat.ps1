[CmdletBinding()]
param(
	[string]$Target,
	[switch]$Check
)

$ErrorActionPreference = "Stop"
if (-not $Target) {
	$Target = Join-Path $PSScriptRoot "..\akk-stack\code\zone\special_attacks.cpp"
}

$expectedSourceHash = "62AFDFDA2DFAB48C0B54CA24D2BDCE1ED58151D55B0EE3BF00DAB8DE31DB3716"
$expectedPatchedHash = "54CC714A0EFBB8216CD2FEBEB325EC9D1CE48DED8EE914846142AC65C26D89A5"
$resolvedTarget = [System.IO.Path]::GetFullPath($Target)

if (-not (Test-Path -LiteralPath $resolvedTarget -PathType Leaf)) {
	throw "special_attacks.cpp was not found at '$resolvedTarget'."
}

function Get-Sha256([string]$Path) {
	return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

$currentHash = Get-Sha256 $resolvedTarget
if ($currentHash -eq $expectedPatchedHash) {
	Write-Host "Monk multiclass combat overlay is applied: $resolvedTarget"
	exit 0
}

if ($currentHash -ne $expectedSourceHash) {
	throw "Refusing to patch unexpected special_attacks.cpp (SHA256 $currentHash). Expected source $expectedSourceHash or patched $expectedPatchedHash."
}

if ($Check) {
	throw "Monk multiclass combat overlay is not applied: $resolvedTarget"
}

$source = [System.IO.File]::ReadAllText($resolvedTarget)
$newline = if ($source.Contains("`r`n")) { "`r`n" } else { "`n" }

function Replace-ExactlyOnce(
	[string]$Content,
	[string[]]$OldLines,
	[string[]]$NewLines,
	[string]$Description
) {
	$oldText = $OldLines -join $newline
	$newText = $NewLines -join $newline
	$first = $Content.IndexOf($oldText, [System.StringComparison]::Ordinal)

	if ($first -lt 0) {
		throw "Could not find expected $Description source block."
	}

	if ($Content.IndexOf($oldText, $first + $oldText.Length, [System.StringComparison]::Ordinal) -ge 0) {
		throw "Found more than one $Description source block."
	}

	return $Content.Substring(0, $first) + $newText + $Content.Substring($first + $oldText.Length)
}

$source = Replace-ExactlyOnce $source @(
	"`t// Check to see if actually have skill",
	"`tif (!MaxSkill(static_cast<EQ::skills::SkillType>(ca_atk->m_skill)) && !bypass_skill_check) {",
	"`t`treturn;",
	"`t}"
) @(
	"`tconst auto skill = static_cast<EQ::skills::SkillType>(ca_atk->m_skill);",
	"`tconst auto held_classes = GetMulticlassList();",
	"`tuint16 current_cap = 0;",
	"",
	"`tfor (uint8 held_class : held_classes) {",
	"`t`tconst uint16 held_cap = MaxSkill(skill, held_class, GetLevel());",
	"`t`tif (held_cap > current_cap) {",
	"`t`t`tcurrent_cap = held_cap;",
	"`t`t}",
	"`t}",
	"",
	"`tconst bool can_use_monk = EQ::skills::CanUseMonkCombatAbility(",
	"`t`theld_classes,",
	"`t`tskill,",
	"`t`tcurrent_cap",
	"`t);",
	"",
	"`t// Check the current-level cap across every held class, not only the base class.",
	"`tif (!current_cap && !bypass_skill_check) {",
	"`t`treturn;",
	"`t}"
) "base-class skill gate"

$source = Replace-ExactlyOnce $source @(
	"`t`tca_atk->m_skill == EQ::skills::SkillKick &&",
	"`t`tcan_use_kick",
	"`t) {"
) @(
	"`t`tca_atk->m_skill == EQ::skills::SkillKick &&",
	"`t`tcan_use_kick &&",
	"`t`t!can_use_monk",
	"`t) {"
) "generic Kick route"

$source = Replace-ExactlyOnce $source @(
	"`tif (class_id == Class::Monk) {"
) @(
	"`tif (can_use_monk) {"
) "Monk dispatch gate"

$temporaryPath = "$resolvedTarget.codex-monk-overlay.tmp"
try {
	[System.IO.File]::WriteAllText(
		$temporaryPath,
		$source,
		[System.Text.UTF8Encoding]::new($false)
	)

	$patchedHash = Get-Sha256 $temporaryPath
	if ($patchedHash -ne $expectedPatchedHash) {
		throw "Generated overlay hash $patchedHash did not match expected $expectedPatchedHash; target was not changed."
	}

	[System.IO.File]::Copy($temporaryPath, $resolvedTarget, $true)
} finally {
	if (Test-Path -LiteralPath $temporaryPath) {
		Remove-Item -LiteralPath $temporaryPath -Force
	}
}

Write-Host "Applied Monk multiclass combat overlay: $resolvedTarget"
