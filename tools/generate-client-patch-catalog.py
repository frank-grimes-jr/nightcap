"""Check proxy verifier/catalog agreement and refresh the launcher's embedded copy."""
import argparse
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
source = (root / "eq-client-dll/tests/verify-exact-client-patch-sites.ps1").read_text()
raw = (root / "eq-client-dll/config/patch-sites.json").read_bytes()
catalog = json.loads(raw)
assert raw == json.dumps(catalog, separators=(",", ":")).encode(), "catalog must be canonical"
sites = []
for rva, body, label in re.findall(r"Assert-Bytes \$image (0x[0-9A-Fa-f]+) \(\[byte\[\]\]\(([^)]+)\)\) '([^']+)'", source):
    sites.append({"name":label,"rva":int(rva,16),"original":bytes(int(x.strip(),0) for x in body.split(",")).hex()})
assert len(sites) > 0 and sorted(sites,key=lambda x:x["rva"]) == catalog["sites"], "proxy verifier and catalog differ"
# Names already consumed by the proxy. Keeping these declarations generated
# binds launcher preflight and runtime original-byte guards to one catalog.
symbols = {
 0x1374AC:("kTrainerClassRva","kExpectedTrainerClass"),
 0x1BAEC0:("kTrainerCapRva","kExpectedTrainerCap"),
 0x1BAA20:("kTrainerLevelRva","kExpectedTrainerLevel"),
 0x185890:("kTrainerBuyCapRva","kExpectedTrainerBuyCap"),
 0x18590B:("kTrainerBuyLevelRva","kExpectedTrainerBuyLevel"),
 0x381811:("kTrainerButtonLevelRva","kExpectedTrainerButtonLevel"),
 0x381EE4:("kTrainerDisplayCapRva","kExpectedTrainerDisplayCap"),
 0x38201F:("kTrainerDisplayCap2Rva","kExpectedTrainerDisplayCap2"),
 0x381F29:("kTrainerDisplayLevelRva","kExpectedTrainerDisplayLevel"),
 0x381F6B:("kTrainerDisplayLevel2Rva","kExpectedTrainerDisplayLevel2"),
 0x3824E6:("kTrainerListLevelRva","kExpectedTrainerListLevel"),

 0x2F3A90:("kUIMerchantNotifyRva","kExpectedUIMerchantNotify"),
 0x265430:("kLootItemIconCacheRva","kExpectedLootItemIconCache"),
 0x265A60:("kLootItemIconRva","kExpectedLootItemIcon"),
 0x21BAEE:("kLootItemIconDecalsRva","kExpectedLootItemIconDecals"),
 0x6A60:("kModelAnimationRva","kExpectedModelAnimation"),
 0x248200:("kSpellMenuBuildRva","kExpectedSpellMenuBuild"),
 0x2488A0:("kSpellMenuFrameRva","kExpectedSpellMenuFrame"),
 0x3DB210:("kSpellMenuProfileRva","kExpectedSpellMenuProfile"),
 0x2A39CE:("kInspectionClassesRva","kExpectedInspectionClasses"),
 0x2A39E0:("kInspectionLevelRva","kExpectedInspectionLevel"),
 0x2A6D11:("kInspectionClasses2Rva","kExpectedInspectionClasses2"),
 0x2A6D21:("kInspectionLevel2Rva","kExpectedInspectionLevel2"),
 0x11FCE0:("kLootCommandRva","kExpectedLootCommand"),
 0x45F070:("kLootConstructRva","kExpectedLootConstruct"),
 0x45DCF0:("kLootChildrenRva","kExpectedLootChildren"),
 0x4DBB3B:("kLootAllocateRva","kExpectedLootAllocate"),
 0x619828:("kLootTableRva","kExpectedLootTable"),
 0x27C9A0:("kLootDestroyRva","kExpectedLootDestroy"),
 0x45EAD0:("kLootNotifyRva","kExpectedLootNotify"),
 0x465F20:("kLootFrameRva","kExpectedLootFrame"),
 0x465290:("kLootShowRva","kExpectedLootShow"),
 0x11FB0:("kLootTextRva","kExpectedLootText"),
 0x460EF0:("kModelProfileRva","kExpectedModelProfile"),
 0x10A440:("kModelRegisterRva","kExpectedModelRegister"),
 0x10A2D0:("kModelTagRva","kExpectedModelTag"),
 0x934AC:("kModelImportsCallRva","kExpectedModelImportsCall"),
 0x8CB80:("kModelImportsTargetRva",None),
 0x310800:("kUIPetNotifyRva","kExpectedUIPetNotify"),
 0x30EA00:("kUIPetAvailableRva","kExpectedUIPetAvailable"),
 0x35DF6A:("kScribeCanUseRva","kExpectedScribeCanUse"),
 0x35E084:("kScribeLevelRva","kExpectedScribeLevel"),
 0x296095:("kScrollPlacementCanUseRva","kExpectedScrollPlacementCanUse"),
 0xAF700:("kSpellLevelRva","kExpectedSpellLevel"),
 0x2F0D9E:("kMerchantLevelMaskRva","kExpectedMerchantLevelMask"),
 0x2F0E00:("kMerchantUsableMaskRva","kExpectedMerchantUsableMask"),
 0x3AFFA0:("kItemTypeRva","kExpectedItemType"),
 0x3AFFF0:("kItemSpellRva","kExpectedItemSpell"),
 0x95DB5:("kUIExplicitSkinRva","kExpectedUIExplicitSkin"),
 0x95E0B:("kUISavedSkinRva","kExpectedUISavedSkin"),
 0x293490:("kUIInventoryNotifyRva","kExpectedUIInventoryNotify"),
 0x468330:("kUIChildRva","kExpectedUIChild"),
 0x363640:("kUILabelRva","kExpectedUILabel"),
 0x11F1A0:("kUIChatRva","kExpectedUIChat"),
 0x119750:("kUIStateRva","kExpectedUIState"),
 0x209F90:("kUIAARva","kExpectedUIAA"),
 0x405DE0:("kUIStringAssignRva","kExpectedUIStringAssign"),
 0x453680:("kUIRowDataRva","kExpectedUIRowData"),
 0x4575B0:("kUICellTextRva","kExpectedUICellText"),
 0x11DCD0:("kUISendRequestRva","kExpectedUISendRequest"),
 0x43F90:("kCasterClassTableRva","kExpectedCasterClassTable"),
 0x18238C:("kCombatAbilityClassTableRva","kExpectedCombatAbilityClassTable"),
 0x181E96:("kMaxManaNonCasterReturnRva","kExpectedMaxManaReturn"),
 0x318E93:("kPlayerManaPredicateCallRva","kExpectedPlayerManaPredicateCall"),
 0x151B59:("kHotButtonSkillPredicateCallRva","kExpectedHotButtonSkillPredicateCall"),
 0x5B33E:("kUseSkillValueCallRva","kExpectedUseSkillValueCall"),
 0x28CA21:("kHotButtonSkillActivationCallRva","kExpectedHotButtonSkillActivationCall"),
 0x1A2FD0:("kSpecialAttackSkillPredicateCallRva","kExpectedSpecialAttackSkillPredicateCall"),
 0x1A5000:("kSpecialAttackSubmitRva",None),
 0x4A1B0:("kCharacterHasSkillRva",None),
 0x49C80:("kCharacterGetBaseSkillRva",None),
 0x49FE0:("kCharacterGetSkillRva",None),
 0x1BAB10:("kSkillIsCombatRva",None),
 0x1BABD0:("kSkillIsActivatedRva",None),
 0x18359C:("kEquipCanUseItemCallRva","kExpectedEquipCanUseItemCall"),
 0x4C46D:("kEquipClassMaskCallRva","kExpectedEquipClassMaskCall"),
 0x4C430:("kCanUseItemRva","kExpectedCanUseItemEntry"),
 0x3B4CE0:("kItemClassesRva","kExpectedItemClassesEntry"),
}
def byte_list(data):
    return ",".join(f"0x{x:02X}" for x in data)
header = ["// Generated by tools/generate-client-patch-catalog.py; do not edit.", "#pragma once",
          f"static const DWORD kExpectedEqgameSize = {catalog['client_size']};",
          "static const BYTE kExpectedEqgameSha256[32] = {"+byte_list(bytes.fromhex(catalog["client_sha256"]))+"};"]
by_rva = {site["rva"]:site for site in sites}
for rva, (rva_name, bytes_name) in symbols.items():
    site = by_rva[rva]
    header.append(f"static const uintptr_t {rva_name} = 0x{rva:08X};")
    if bytes_name:
        data = bytes.fromhex(site["original"])
        if rva == 0x619828:
            # Signed launcher sites remain <=64 bytes. The runtime needs the
            # entire contiguous native vtable including its RTTI locator.
            chunks = [bytes.fromhex(by_rva[rva+i*64]["original"]) for i in range(6)]
            assert all(len(chunk) == 64 for chunk in chunks)
            data = b''.join(chunks)
        # Decimal tables retain the established source-verifier representation.
        values = ",".join(str(x) for x in data) if rva in (0x43F90,0x18238C) else byte_list(data)
        header.append(f"static const BYTE {bytes_name}[{len(data)}] = {{"+values+",};")
header.append("static const uintptr_t kActionsSkillPredicateCallRvas[] = {0x00356D2D,0x00356DA5,};")
header.append("static const BYTE kExpectedActionsSkillPredicateCalls[][5] = {")
for rva in (0x356D2D,0x356DA5):
    header.append("    {"+byte_list(bytes.fromhex(by_rva[rva]["original"]))+"},")
header.append("};")
header_raw = ("\n".join(header)+"\n").encode()
header_path = root / "eq-client-dll/src/patch_catalog.h"
if args.check:
    assert header_path.read_text().encode() == header_raw, "regenerate proxy patch_catalog.h"
else:
    header_path.write_bytes(header_raw)
target = root / "eq-launcher/internal/preflight/catalog.json"
if args.check:
    assert target.read_bytes() == raw, "run tools/generate-client-patch-catalog.py"
else:
    target.write_bytes(raw)
print(f"PASS: {len(sites)} catalog sites match proxy verifier and launcher")

runtime = ["// Generated by tools/generate-client-patch-catalog.py; do not edit.",
 "#pragma once", "#include <cstddef>", "#include <cstdint>", "namespace nightcap {",
 "enum RequiredFeature : size_t {" + ",".join("Feature_" + x for x in catalog["required_features"]) + "};",
 "static const char* const kRequiredFeatures[] = {" + ",".join(json.dumps(x) for x in catalog["required_features"]) + "};",
 "static const size_t kRequiredFeatureCount = sizeof(kRequiredFeatures) / sizeof(kRequiredFeatures[0]);",
 "static const uint32_t kRequiredMask = (uint32_t(1) << kRequiredFeatureCount) - 1;",
 "static_assert(kRequiredFeatureCount > 0 && kRequiredFeatureCount < 32, \"feature mask capacity\");",
 "static const char kCatalogSHA256[] = "+json.dumps(hashlib.sha256(raw).hexdigest())+";",
 "static const char kProxyVersion[] = "+json.dumps(catalog["proxy_version"])+";",
 "static const unsigned kRuntimeSchema = "+str(catalog["runtime_schema"])+";", "}"]
# This first runtime supports precisely the optional diagnostic survey.
assert catalog["optional_features"] == ["mq2_survey"], "update runtime optional feature handling"
runtime_raw = "\n".join(runtime)+"\n"
runtime_path = root / "eq-client-dll/src/runtime_contract.h"
if args.check:
    assert runtime_path.read_text() == runtime_raw, "regenerate runtime_contract.h"
else:
    runtime_path.write_text(runtime_raw, encoding="utf-8")
