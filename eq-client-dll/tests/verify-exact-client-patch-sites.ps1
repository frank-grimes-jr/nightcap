param(
	[string]$EqgamePath = (Join-Path $PSScriptRoot '..\..\Client_RoF2_Dev\everquest_rof2\eqgame.exe'),
	[string]$SourcePath = (Join-Path $PSScriptRoot '..\src\dllmain.cpp')
)

$ErrorActionPreference = 'Stop'
$expectedSize = 8774656
$expectedSha256 = '2A8702AD9F722704F01355C0750BE7D6F164A8B9C9128BA0CF286EA32B405B0E'
$imageBase = 0x00400000
$textRva = 0x00001000
$textFileOffset = 0x00000400

function Assert-Bytes {
	param(
		[byte[]]$Image,
		[uint32]$Rva,
		[byte[]]$Expected,
		[string]$Label
	)

	$fileOffset = $textFileOffset + ($Rva - $textRva)
	for ($i = 0; $i -lt $Expected.Length; $i++) {
		if ($Image[$fileOffset + $i] -ne $Expected[$i]) {
			throw ('{0} signature mismatch at RVA 0x{1:X8} byte {2}' -f $Label, $Rva, $i)
		}
	}
}

$resolvedPath = (Resolve-Path -LiteralPath $EqgamePath).Path
$file = Get-Item -LiteralPath $resolvedPath
if ($file.Length -ne $expectedSize) {
	throw "eqgame.exe size mismatch: expected $expectedSize, got $($file.Length)"
}

$sha256 = (Get-FileHash -LiteralPath $resolvedPath -Algorithm SHA256).Hash
if ($sha256 -ne $expectedSha256) {
	throw "eqgame.exe SHA-256 mismatch: expected $expectedSha256, got $sha256"
}

$image = [System.IO.File]::ReadAllBytes($resolvedPath)
Assert-Bytes $image 0x00043F90 ([byte[]](0,1,1,1,1,1,0,1,0,1,1,1,1,1,1,0)) 'caster table'
Assert-Bytes $image 0x0018238C ([byte[]](0,1,0,0,0,1,0,0,0,1,1,1,1,1,0,0)) 'combat-ability table'
Assert-Bytes $image 0x00181E96 ([byte[]](0x33,0xC0,0x5E,0xC2,0x04,0x00)) 'Max_Mana return'
Assert-Bytes $image 0x00318E93 ([byte[]](0xE8,0xF8,0x6C,0xE8,0xFF)) 'CPlayerWnd mana predicate call'
Assert-Bytes $image 0x00356D2D ([byte[]](0xE8,0x7E,0x34,0xCF,0xFF)) 'Actions non-combat skill predicate call'
Assert-Bytes $image 0x00356DA5 ([byte[]](0xE8,0x06,0x34,0xCF,0xFF)) 'Actions combat skill predicate call'
Assert-Bytes $image 0x0004A1B0 ([byte[]](0x8B,0x44,0x24,0x04,0x50,0xE8,0x26,0xFE,0xFF,0xFF)) 'CharacterZoneClient::HasSkill'
Assert-Bytes $image 0x00042110 ([byte[]](0x83,0xC1,0x04,0xE8,0xF8,0x90,0x39,0x00)) 'EQ_Character::GetBaseSkill'
Assert-Bytes $image 0x001BAB10 ([byte[]](0x8B,0x44,0x24,0x04,0x83,0xF8,0x63)) 'CSkillMgr combat classification'
Assert-Bytes $image 0x001BABD0 ([byte[]](0x8B,0x44,0x24,0x04,0x83,0xF8,0x63)) 'CSkillMgr activated classification'

$callFileOffset = $textFileOffset + (0x00318E93 - $textRva)
$relative = [BitConverter]::ToInt32($image, $callFileOffset + 1)
$callTarget = $imageBase + 0x00318E93 + 5 + $relative
if ($callTarget -ne 0x0059FB90) {
	throw ('CPlayerWnd mana predicate call target mismatch: expected 0x0059FB90, got 0x{0:X8}' -f $callTarget)
}

$source = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $SourcePath).Path)
$compactSource = $source -replace '\s', ''
foreach ($requiredFragment in @(
	'kCombatAbilityClassTableRva=0x0018238C',
	'kExpectedCombatAbilityClassTable[16]={0,1,0,0,0,1,0,0,0,1,1,1,1,1,0,0,};',
	'kEnabledCombatAbilityClassTable[16]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,};',
	'ApplyCombatAbilityClassTablePatch(eq_base,size_ok&&hash_ok)',
	'kActionsSkillPredicateCallRvas[]={0x00356D2D,0x00356DA5,}',
	'kCharacterHasSkillRva=0x0004A1B0',
	'kCharacterGetBaseSkillRva=0x00042110',
	'kSkillManagerSlotRva=0x00A64610',
	'kSkillIsCombatRva=0x001BAB10',
	'kSkillIsActivatedRva=0x001BABD0',
	'G006_SELECTORskill=%dstock=%u',
	'HasServerGrantedSkill',
	'ApplyActionsSkillPredicatePatch(eq_base,size_ok&&hash_ok)'
)) {
	if (-not $compactSource.Contains($requiredFragment)) {
		throw "DLL source is missing guarded combat-ability unlock: $requiredFragment"
	}
}

$combatPatch = [regex]::Match(
	$source,
	'static bool ApplyCombatAbilityClassTablePatch.*?(?=// MQ2/the client environment)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $combatPatch.Success) {
	throw 'Could not isolate ApplyCombatAbilityClassTablePatch.'
}

$combatBody = $combatPatch.Value
foreach ($requiredSafetyFragment in @(
	'BYTE original[',
	'memcpy(original, table, sizeof(original))',
	'const bool write_attempted = pre_write_signature',
	'rollback_ok = (memcmp(table, original, sizeof(original)) == 0)',
	'bool protection_restored = VirtualProtect(',
	'if (!protection_restored)',
	'const bool retry_restored = VirtualProtect('
)) {
	if (-not $combatBody.Contains($requiredSafetyFragment)) {
		throw "Combat-ability patch is missing safety behavior: $requiredSafetyFragment"
	}
}
if ($combatBody.Contains('already_applied')) {
	throw 'Combat-ability patch must not trust an all-zero table from another modifier.'
}

$actionsPatch = [regex]::Match(
	$source,
	'static bool ApplyActionsSkillPredicatePatch.*?(?=// MQ2/the client environment)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $actionsPatch.Success) {
	throw 'Could not isolate ApplyActionsSkillPredicatePatch.'
}

$actionsBody = $actionsPatch.Value
foreach ($requiredSafetyFragment in @(
	'BYTE originals[site_count][5] = {}',
	'memcpy(originals[i], site, sizeof(originals[i]))',
	'const size_t protected_span = (last_site + 5) - first_site',
	'bool pre_write_signatures = true',
	'FlushInstructionCache(',
	'rollback_ok = true',
	'bool protection_restored = VirtualProtect(',
	'if (!protection_restored)',
	'const bool retry_restored = VirtualProtect('
)) {
	if (-not $actionsBody.Contains($requiredSafetyFragment)) {
		throw "Actions skill patch is missing safety behavior: $requiredSafetyFragment"
	}
}

Write-Output 'PASS: exact RoF2 client and all guarded B2 patch sites verified.'
