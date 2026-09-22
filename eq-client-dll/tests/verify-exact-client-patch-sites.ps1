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
Assert-Bytes $image 0x310800 ([byte[]](0x6A,0xFF,0x64,0xA1,0x00,0x00,0x00,0x00)) 'UIPetNotify'
Assert-Bytes $image 0x30EA00 ([byte[]](0x8B,0x44,0x24,0x04,0x83,0xF8,0x22)) 'UIPetAvailable'
# The hidden native hotbuttons keep their per-character configured meaning.
# Decode the pinned switch jump table, rather than assuming UI slot == command.
$petCommands = @(0,1,2,3,4,5,6,9,31,12,15,18,21,24,27,28,29,30)
for ($index = 0; $index -lt $petCommands.Count; $index++) {
	$tableOffset = $textFileOffset + 0x30F26C - $textRva + 4 * $index
	$caseRva = [BitConverter]::ToUInt32($image, $tableOffset) - $imageBase
	if ($index -eq 0) {
		Assert-Bytes $image $caseRva ([byte[]](0x33,0xC0,0xC2,0x04,0x00)) 'Pet command zero'
	} else {
		Assert-Bytes $image $caseRva ([byte[]](0xB8,$petCommands[$index],0x00,0x00,0x00,0xC2,0x04,0x00)) 'Pet command mapping'
	}
}
Assert-Bytes $image 0x293490 ([byte[]](0x6A,0xFF,0x68,0xA8,0xA3,0x98,0x00)) 'UIInventoryNotify'
Assert-Bytes $image 0x468330 ([byte[]](0x53,0x8B,0x5C,0x24,0x08,0x56,0x57,0x8B)) 'UIChild'
Assert-Bytes $image 0x00363640 ([byte[]](0x55,0x8B,0xEC,0x6A,0xFF)) 'UILabel'
Assert-Bytes $image 0x0011F1A0 ([byte[]](0x64,0xA1,0x00,0x00,0x00,0x00)) 'UIChat'
Assert-Bytes $image 0x00119750 ([byte[]](0x8B,0x44,0x24,0x04,0x89,0x81,0xC8,0x05,0x00,0x00)) 'UIState'
Assert-Bytes $image 0x00209F90 ([byte[]](0x6A,0xFF,0x68,0x1A,0x13,0x98,0x00)) 'UIAA'
Assert-Bytes $image 0x00405DE0 ([byte[]](0x55,0x8B,0xEC,0x8B,0x45,0x08,0x56,0x57)) 'UIStringAssign'
Assert-Bytes $image 0x00453680 ([byte[]](0x8B,0x44,0x24,0x04,0x85,0xC0,0x78,0x23)) 'UIRowData'
Assert-Bytes $image 0x004575B0 ([byte[]](0x8B,0x44,0x24,0x04,0x85,0xC0,0x78,0x5B)) 'UICellText'
Assert-Bytes $image 0x0011DCD0 ([byte[]](0x6A,0xFF,0x68,0x48,0x84,0x97,0x00)) 'UISendRequest'
Assert-Bytes $image 0x00043F90 ([byte[]](0,1,1,1,1,1,0,1,0,1,1,1,1,1,1,0)) 'caster table'
Assert-Bytes $image 0x0018238C ([byte[]](0,1,0,0,0,1,0,0,0,1,1,1,1,1,0,0)) 'combat-ability table'
Assert-Bytes $image 0x00181E96 ([byte[]](0x33,0xC0,0x5E,0xC2,0x04,0x00)) 'Max_Mana return'
Assert-Bytes $image 0x00318E93 ([byte[]](0xE8,0xF8,0x6C,0xE8,0xFF)) 'CPlayerWnd mana predicate call'
Assert-Bytes $image 0x00356D2D ([byte[]](0xE8,0x7E,0x34,0xCF,0xFF)) 'Actions non-combat skill predicate call'
Assert-Bytes $image 0x00356DA5 ([byte[]](0xE8,0x06,0x34,0xCF,0xFF)) 'Actions combat skill predicate call'
Assert-Bytes $image 0x00151B59 ([byte[]](0xE8,0x52,0x86,0xEF,0xFF)) 'hotbutton held-skill predicate call'
Assert-Bytes $image 0x0005B33E ([byte[]](0xE8,0x9D,0xEC,0xFE,0xFF)) 'UseSkill adjusted-skill value call'
Assert-Bytes $image 0x0028CA21 ([byte[]](0xE8,0xAA,0xE8,0xDC,0xFF)) 'hotbutton skill activation call'
Assert-Bytes $image 0x001A2FD0 ([byte[]](0xE8,0xDB,0x71,0xEA,0xFF)) 'special-attack held-skill predicate call'
Assert-Bytes $image 0x001A5000 ([byte[]](0x6A,0xFF,0x68,0xD3,0xBF,0x97,0x00)) 'EQPlayer special-attack submitter'
Assert-Bytes $image 0x0005D92F ([byte[]](0xE8,0xCC,0x76,0x14,0x00)) 'stock UseSkill special-attack submit call'
Assert-Bytes $image 0x0005D93C ([byte[]](0x8B,0x7C,0x24,0x1C,0x8B,0x0D,0x10,0x46,0xE6,0x00,0x6A,0x00,0x57,0xE8,0x52,0xD4,0x15,0x00)) 'stock special-attack reuse sequence'
Assert-Bytes $image 0x0004A1B0 ([byte[]](0x8B,0x44,0x24,0x04,0x50,0xE8,0x26,0xFE,0xFF,0xFF)) 'CharacterZoneClient::HasSkill'
Assert-Bytes $image 0x00049C80 ([byte[]](0x8B,0x41,0x04,0x8B,0x50,0x04,0x8D,0x4C,0x0A,0x04)) 'CharacterZoneClient::GetBaseSkill'
Assert-Bytes $image 0x00049FE0 ([byte[]](0x51,0x56,0x57,0x8B,0x7C,0x24,0x10,0x8B,0xF1)) 'CharacterZoneClient::GetSkill'
Assert-Bytes $image 0x001BAB10 ([byte[]](0x8B,0x44,0x24,0x04,0x83,0xF8,0x63)) 'CSkillMgr combat classification'
Assert-Bytes $image 0x001BABD0 ([byte[]](0x8B,0x44,0x24,0x04,0x83,0xF8,0x63)) 'CSkillMgr activated classification'

$callFileOffset = $textFileOffset + (0x00318E93 - $textRva)
$relative = [BitConverter]::ToInt32($image, $callFileOffset + 1)
$callTarget = $imageBase + 0x00318E93 + 5 + $relative
if ($callTarget -ne 0x0059FB90) {
	throw ('CPlayerWnd mana predicate call target mismatch: expected 0x0059FB90, got 0x{0:X8}' -f $callTarget)
}

$source = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $SourcePath).Path)
# Original-byte declarations are generated from the shared release catalog.
$catalogHeader = Join-Path (Split-Path -Parent $SourcePath) 'patch_catalog.h'
$source += "`n" + [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $catalogHeader).Path)
$compactSource = $source -replace '\s', ''
foreach ($requiredFragment in @(
	'kCombatAbilityClassTableRva=0x0018238C',
	'kExpectedCombatAbilityClassTable[16]={0,1,0,0,0,1,0,0,0,1,1,1,1,1,0,0,};',
	'kEnabledCombatAbilityClassTable[16]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,};',
	'ApplyCombatAbilityClassTablePatch(eq_base,size_ok&&hash_ok)',
	'kActionsSkillPredicateCallRvas[]={0x00356D2D,0x00356DA5,}',
	'kHotButtonSkillPredicateCallRva=0x00151B59',
	'kUseSkillValueCallRva=0x0005B33E',
	'kHotButtonSkillActivationCallRva=0x0028CA21',
	'kSpecialAttackSkillPredicateCallRva=0x001A2FD0',
	'kSpecialAttackSubmitRva=0x001A5000',
	'kCharacterHasSkillRva=0x0004A1B0',
	'kCharacterGetBaseSkillRva=0x00049C80',
	'kCharacterGetSkillRva=0x00049FE0',
	'GetBaseSkillFn)(void*,int,int)',
	'get_base_skill(character,skill,0)',
	'kSkillManagerSlotRva=0x00A64610',
	'kSkillIsCombatRva=0x001BAB10',
	'kSkillIsActivatedRva=0x001BABD0',
	'kSkillTimerIndexRva=0x001BA2B0',
	'kSkillReuseBeginRva=0x001BADA0',
	'kSkillReuseCommitRva=0x001BAC50',
	'G006_SELECTORskill=%dstock=%u',
	'HasServerGrantedSkill',
	'HasServerGrantedMonkAttack',
	'GetServerGrantedSkill',
	'ActivateServerGrantedSkill',
	'begin_reuse(skill_manager,skill,0)',
	'commit_reuse(skill_manager,skill,reuse_end)',
	'ApplyActionsSkillPredicatePatch(eq_base,size_ok&&hash_ok)',
	'constbooluse_skill_ok=ApplyUseSkillValuePatch(eq_base,size_ok&&hash_ok)',
	'ApplyHotButtonSkillPredicatePatch(eq_base,use_skill_ok)',
	'ApplyMonkAttackActivationPatches(eq_base,hotbutton_skill_ok)'
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
	'rollback_ok = FlushInstructionCache(GetCurrentProcess(), table, sizeof(original)) != FALSE &&',
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

if (-not $compactSource.Contains('CreateFileW(log_name,GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,nullptr)')) {
	throw 'DLL diagnostic log must permit live shared reads.'
}

$singleCallPatch = [regex]::Match(
	$source,
	'static bool ApplyGuardedRelativeCall.*?(?=static bool ApplyUseSkillValuePatch)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $singleCallPatch.Success) {
	throw 'Could not isolate ApplyGuardedRelativeCall.'
}
$singleCallCompact = $singleCallPatch.Value -replace '\s', ''

foreach ($requiredSafetyFragment in @(
	'memcmp(site,expected,5)',
	'VirtualProtect(site,5,PAGE_EXECUTE_READWRITE',
	'boolpre_write_signature=false',
	'constboolwrite_attempted=pre_write_signature',
	'if(write_attempted&&!wrote)',
	'FlushInstructionCache(',
	'rollback_ok=FlushInstructionCache(GetCurrentProcess(),site,5)!=FALSE&&',
	'boolprotection_restored=VirtualProtect(',
	'if(!protection_restored)',
	'constboolretry_restored=VirtualProtect('
)) {
	if (-not $singleCallCompact.Contains($requiredSafetyFragment)) {
		throw "Single-call patch helper is missing safety behavior: $requiredSafetyFragment"
	}
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

$monkActivation = [regex]::Match(
	$source,
	'extern "C" __declspec\(noinline\) void __fastcall ActivateServerGrantedSkill.*?(?=// Entered only from)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $monkActivation.Success) {
	throw 'Could not isolate ActivateServerGrantedSkill.'
}
$monkActivationCompact = $monkActivation.Value -replace '\s', ''
foreach ($requiredActivationFragment in @(
	'if(!IsMonkCombatAttack(skill)){use_skill(character,skill,target);return;}',
	'GetServerGrantedSkill(character,nullptr,skill)<=0',
	'player,100,skill,target',
	'begin_reuse(skill_manager,skill,0)',
	'commit_reuse(skill_manager,skill,reuse_end)'
)) {
	if (-not $monkActivationCompact.Contains($requiredActivationFragment)) {
		throw "Monk activation wrapper is missing stock-path behavior: $requiredActivationFragment"
	}
}

$monkPredicate = [regex]::Match(
	$source,
	'extern "C" __declspec\(noinline\) BYTE __fastcall HasServerGrantedMonkAttack.*?(?=// Preserve the stock adjusted value)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $monkPredicate.Success) {
	throw 'Could not isolate HasServerGrantedMonkAttack.'
}
$monkPredicateCompact = $monkPredicate.Value -replace '\s', ''
foreach ($requiredPredicateFragment in @(
	'constBYTEstock=stock_has_skill(character,skill)',
	'if(stock||!IsMonkCombatAttack(skill))',
	'returnget_base_skill(character,skill,0)>0?1:0'
)) {
	if (-not $monkPredicateCompact.Contains($requiredPredicateFragment)) {
		throw "Monk execution predicate is missing narrow fallback behavior: $requiredPredicateFragment"
	}
}

$monkPatch = [regex]::Match(
	$source,
	'static bool RestoreGuardedRelativeCall.*?(?=// MQ2/the client environment)',
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $monkPatch.Success) {
	throw 'Could not isolate held-Monk activation patch and rollback.'
}
$monkPatchCompact = $monkPatch.Value -replace '\s', ''
foreach ($requiredPatchFragment in @(
	'memcmp(site,replacement,5)',
	'VirtualProtect(site,5,PAGE_EXECUTE_READWRITE',
	'memcpy(site,expected,5)',
	'FlushInstructionCache(',
	'constboolprotection_restored=VirtualProtect(',
	'if(!activation_ok)',
	'constboolrollback_ok=RestoreGuardedRelativeCall('
)) {
	if (-not $monkPatchCompact.Contains($requiredPatchFragment)) {
		throw "Held-Monk activation patch is missing rollback safety: $requiredPatchFragment"
	}
}

# #13 equipment caller and class accessor, plus exact native entry signatures.
Assert-Bytes $image 0x0018359C ([byte[]](0xE8,0x8F,0x8E,0xEC,0xFF)) 'Equip CanUseItem call'
Assert-Bytes $image 0x0004C46D ([byte[]](0xE8,0x6E,0x88,0x36,0x00)) 'CanUseItem class accessor'
Assert-Bytes $image 0x0004C430 ([byte[]](0x55,0x56,0x57,0x8B,0x7C,0x24,0x10)) 'CanUseItem entry'
Assert-Bytes $image 0x003B4CE0 ([byte[]](0x55,0x8B,0xEC,0x83,0xEC,0x44)) 'Item class accessor entry'
foreach ($fragment in @(
    'kEquipCanUseItemCallRva=0x0018359C',
    'kEquipClassMaskCallRva=0x0004C46D',
    'kCanUseItemRva=0x0004C430',
    'kItemClassesRva=0x003B4CE0',
    'ApplyEquipSubmissionPatches(eq_base,size_ok&&hash_ok)',
    'result=original(character,item_ref,use_required_level,output)',
    'constuint32_tstock=original(item,flag1,flag2)',
    'returnnightcap::EquipClassMask(stock,item,flag1,flag2)'
)) {
    if (-not $compactSource.Contains($fragment)) {
        throw "Missing scoped equipment contract: $fragment"
    }
}
$equipWrapper = [regex]::Match($source,
    'BYTE __fastcall CanUseItemForEquip.*?(?=static bool ApplyEquipSubmissionPatches)',
    [System.Text.RegularExpressions.RegexOptions]::Singleline)
$equipWrapperCode = $equipWrapper.Value -replace '//[^\r\n]*', '' -replace '\s', ''
if (-not $equipWrapper.Success -or -not $equipWrapperCode.Contains('__finally{nightcap::SetActiveEquipItem(previous);}')) {
    throw 'Equipment wrapper must restore the previous item scope in __finally.'
}
Write-Output 'PASS: exact RoF2 client, B2/G006 and G013 equipment patch sites verified.'

# Native UI-load skin assignment, covering explicit and saved/default branches.
Assert-Bytes $image 0x00095DB5 ([byte[]](0xE8,0x26,0x00,0x37,0x00)) 'UI explicit skin assignment'
Assert-Bytes $image 0x00095E0B ([byte[]](0xE8,0xD0,0xFF,0x36,0x00)) 'UI saved skin assignment'

Assert-Bytes $image 0x000AF700 ([byte[]](0x8B,0x44,0x24,0x04,0x8D,0x50,0xFF)) 'Spell class level entry'

Assert-Bytes $image 0x002F0D9E ([byte[]](0xE8,0x3D,0x3F,0x0C,0x00)) 'Merchant spell level class mask'

Assert-Bytes $image 0x002F0E00 ([byte[]](0xE8,0xDB,0x3E,0x0C,0x00)) 'Merchant usable class mask'

Assert-Bytes $image 0x003AFFA0 ([byte[]](0x8B,0x01,0x8B,0x50,0x08,0xFF,0xD2,0x0F,0xB6,0x80,0xD4,0x01,0x00,0x00,0xC3)) 'Item type accessor'

Assert-Bytes $image 0x003AFFF0 ([byte[]](0x55,0x8B,0xEC,0x8B,0x01,0x8B,0x50,0x08,0xFF,0xD2,0x8B,0x4D,0x08,0x83,0xF9,0x06)) 'Item spell accessor'

Assert-Bytes $image 0x0035DF6A ([byte[]](0xE8,0xC1,0xE4,0xCE,0xFF)) 'Spellbook scribe CanUseItem'

Assert-Bytes $image 0x00296095 ([byte[]](0xE8,0x96,0x63,0xDB,0xFF)) 'Scroll inventory placement CanUseItem'
