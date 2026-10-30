# Power Source item experience — implementation plan

Status: verified source candidate, 2026-10-30. Disabled by default. The paired
build and independent source review pass; real-client/custody checks, measured
pacing and owner acceptance remain pending. Not deployed or enabled.

Dev integration preserves its existing regular-combat Hunt augment and zoning
capacity candidates. integration-resolution.json records the 13 merge resolutions
and independent review. The merged item-XP, Hunt, capacity and wiki checks pass.
integration-native-build.json records the selective Hunt compile/relink against
the completed paired build; retained inputs first reproduce its zone byte-for-byte.
These artifacts do not authorize deploying the unrelated dev candidates.

## Accepted intent

Add item advancement through combat experience while an item occupies the Power
Source slot. Preserve the Reforging Box and its existing recipes. The owner chose
roughly 4–8 hours of eligible combat for one Normal-to-top item on October 30.
Ordinary gear retains Normal / Polished / Exalted / Ascended identities; Hunt
families retain Base / Polished / Exalted / Ascension. Do not invent cross-family
conversions or new tiers.

## Proposed behavior and checks

- One training item at a time. Its normal equipment slot is unavailable while it
  trains. Suppress its stats, focus, worn effects and equip-only clicks in the
  Power Source slot; preserve actual power sources.
- Earn additional item progress from eligible combat XP before AA allocation and
  level-cap clamping; do not consume character or AA XP. Exclude gray, resurrection,
  GM and noncombat awards. Retain existing group/raid award attribution.
- Later tier transitions cost progressively more. Calibrate an explicit curve
  against current NPC rewards and representative combat rates; report assumptions
  and estimates separately from measured player acceptance.
- Reuse verified successor catalogs and item definitions. Exclude separate epic
  and dungeon reward systems without an explicit existing upgrade route.
- Persist exact item-instance progress through movement, zoning, relog, death,
  trading and existing upgrade routes. Repair and regression-test native multi-key
  custom_data loading before relying on it for XP alongside grip metadata.
- Commit progress and tier changes under exact inventory preimage checks before
  publishing the replacement. Retain GUID, charges, binding, augments and cosmetics
  where the successor supports them. Fail closed and quarantine uncertain writes.
- Box upgrading remains usable. Partial XP is discarded when copies are consumed;
  the fresh output starts its tier at zero. Never pool or duplicate partial XP.

## Source investigation

Isolated checkout: E:/EQ_Local_Dev/_worktrees/power-source-item-xp,
branch feature/power-source-item-xp, freshly fetched origin/main baseline.
The default workspace contains unrelated edits and is not the implementation target.

- common/item_upgrade_policy.h and zone/advanced_loot_inventory.cpp own successor
  checks and existing atomic box conversion.
- zone/exp.cpp::CalculateExp has modified normal XP before AA allocation;
  AddEXP identifies Kill/Quest/Task and passes the source NPC.
- common/item_instance.cpp::IsEquipable / IsSlotAllowed gate native placement;
  common/patches/rof2.cpp::SerializeItem transmits the equipment slot mask.
- zone/bonuses.cpp::CalcItemBonuses includes equipment slots; training must not
  create an extra stat slot. Audit all other equipped-effect consumers.
- zone/inventory.cpp::AscendPaladinEpic and common/paladin_weapon_grip.h provide
  exact saved-preimage, same-instance replacement and quarantine examples.
- inventory GUID persists, but uniqueness/reuse and all custody transfer paths
  was audited: runtime serials regenerate on login, so a GUID-keyed side table is
  rejected. Inventory/corpse/trade/Bazaar already carry custom_data.

## Completed foundations and remaining decisions

- Native metadata regression first failed on actual SetCustomDataString. The
  loader now accepts existing double-separated and compact key/value encodings,
  preserving empty values; malformed/duplicate keys do not partially apply.
  The actual-method test and all five Paladin weapon-grip test groups pass.
- common/item_xp_policy.h implements overflow-safe normalized awards and three
  increasing costs: 80/160/240 million micro-units. One reference kill is one
  million units, based on native level-squared XP at the dated 0.65 normal rate.
  Native tests cover levels1–255, tiny/maximum awards and every tier boundary.
- tools/item_xp_calibration.py records modeled level and zone/rate examples.
  This is not production measurement or in-game balance acceptance.
- Integrated: strict metadata version/current-ID validation; exact saved-row
  atomic UPDATE preserving saved GUID; complete four-tier family validation;
  pre-AA combat XP hook, slot projection, automatic upgrades, #itemxp progress;
  grip/augment/dye preservation, box compatibility and equipment-effect guards.
- Passed: 35 actual AddEXP checks, 369 existing AA checks, native metadata/policy/
  eligibility/box/SQL guards, six Paladin grip groups and four Bazaar groups.
  Bazaar reconstruction now exercises actual current metadata methods, including
  XP plus grip. Disposable MariaDB verified two native-generated statements,
  replay refusal, all 16 non-GUID stale-field predicates per statement, saved-GUID
  preservation, NULL metadata and rollback. This used a synthetic inventory
  schema, not a claim of fresh production-schema verification.
- Initial isolated 11 translation units passed; native-compile-initial.json
  retains the exact source/object hashes. Subsequent attunement, raw AC, equip
  event, default-color and same-lore-group replacement fixes supersede portions
  of that compile. All13 equipment/lore units passed in stageb; evidence is
  native-compile-equipment.json. Stagec records the final hex-normalization fix
  with complete compiler dependency hashes. Both are isolated in
  akk-stack-eqemu-server-1. Do not restart a live compile merely on an observation
  timeout; inspect/poll its active handle or process first.
- Shared local MariaDB had long-standing metadata/query-cache locks; only this
  task's blocked test was interrupted. Separate disposable test container:
  nightcap-item-xp-db-20261030, localhost3318, schema item_xp_test, task label
  power-source-item-xp. It contained only synthetic data and was removed with its
  anonymous volume after verifying the task label, port and mounts. The shared
  database was untouched. Test driver: E:/EQ_Local_Dev/artifacts/item-xp-testdeps.
- Actual AwardItemExperience failure-injection harness passes: save failures,
  stale/multiple rows, exceptions and publication failure quarantine; no duplicate
  award; lore/augment incompatibility refuses; dye/binding/charges remain. It
  exposed lowercase metadata hex rejected by the reused SQL validator, now fixed
  and covered by native and MariaDB regressions. Actual native slot methods pass
  rule-on/off, removal, augment, evolving/stackable and real Power Source cases.
- QA.md records exact player checks, pacing measurements and safe disable/recovery.
  Seven wiki guides have Not released previews; all19 wiki/refresh checks pass
  with a workspace-owned temporary directory. The old global wiki ledger still
  reports historical source drift; it has not been blanket-advanced.
- Actual bonus dispatch and raw AC checks pass; training never reaches normal
  or additive-worn bonuses, while real Power Sources retain behavior. The full
  focused suite reports9 tests,8passed and the opt-in DB test skipped; that DB
  test separately passes against the disposable synthetic database.
- Final13-unit compilation passes with9726dependency records. The complete paired
  world/zone/shared_memory build passed at /tmp/nightcap-item-xp-full-c4802fa0a9ad,
  via tools/build_item_xp.py, from2848authenticated candidate source files based
  on retained faction-release sources. native-build.json records the exact pins,
  commands, binary hashes and successful dependency resolution. All three retained
  binaries were rehashed against that manifest. No services were installed or restarted.
- Whole-wiki impact evidence is in wiki-review.json; installed skill candidate
  guidance, item-xp source routing and47reviewed fingerprints validate. REVIEW.md records the author audit
  and owner-authorized independent review: no blocking finding for the disabled
  candidate;8native groups passed independently, DB opt-in skipped. Existing box
  recipe policy and all10Perl quest checks also pass. Real custody/client/effect
  and pacing checks remain manual acceptance.
  No promotion, public publication or production deployment has occurred.
- Old binaries cannot
  safely load new multi-key XP/grip metadata: paired rollout is required.

## Implementation order

1. Resolve persistence/custody and client slot projection; document the final ADR.
2. Add tested pure eligibility/progression policy and reproducible XP calibration.
3. Add guarded persistence and actual native award/replacement tests with MariaDB.
4. Integrate placement, effect suppression, progress feedback and box coexistence.
5. Build matched native targets; verify RoF2 drag/drop and progress display through
   the managed client flow. Never modify Client_RoF2_Dev.
6. Independent review, regressions, CHANGES/status, wiki impact and installed skill
   references/fingerprints. Promote only through authorized branch boundaries.

## Required QA

Normal through each successor; top-tier stop; each family; unsupported item refusal;
zero stats/focus/click exploit in training slot; 0/50/100 percent AA and level cap;
gray/GM/rez rejection; solo/group/raid attribution; tiny XP carry/large awards;
move/relog/zone/death/trade/bazaar/box; augmented and grip metadata; injected save,
commit and packet failures; no duplicate upgrade after reconnect. Owner in-game
balance acceptance and main/production promotion remain separate gates.
