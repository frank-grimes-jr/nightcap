# Equipment race policy — October 16, 2026

Status: **candidate; not merged or deployed; owner gameplay QA pending**.
The owner confirmed Forged Javelin works with signed client 2026101501, then
reported Bronze Knuckles still failing. The screenshot shows the server's
race/class/deity rejection and resynchronization from cursor 33 to primary 13.

## Root cause and accepted policy

Bronze Knuckles 30981 and its quality variants 230981/430981/630981 have classes
16448 (Monk/Beastlord), races 62219 (excluding Half Elf), slots 8192 (primary
only), deity 0 and required level 0. Palwar's selected Monk matches; the race
mask was the remaining blocker. This is distinct from the previously corrected
client class projection. No character-class repair is needed.

The owner chose **class match allows any race**, then explicitly chose to keep
non-player equipment unavailable. `common/equipment_race_policy.h` projects
effective `Races=65535` only for common items having at least one playable class
and race bit, and either a worn slot (0..22) or a nonzero AugType. It runs in
`SharedDatabase::LoadItems` after restrictions are read. SQL remains unchanged.
Zero masks and unsupported-only masks such as 65536 stay unchanged. Do not
replace this with `Races != 0`: that would enable pet/Shadowed definitions.

This is a global effective item policy, so bots and other consumers see the
same playable masks. The existing pet transfer policy is separate. Classes,
deity, required/recommended level, slots, weapon conflicts, augment socket/type
and AugRestrict, trade/LORE/resale and every other field remain unchanged.
InventoryProfile::SwapItem retains its checks in both directions. Bronze
Knuckles stays primary-only; green means eligibility, not permission to use
every slot or ignore a two-handed weapon conflict. Required-skill coloring and
augment target fit also retain native context checks.

RoF2 serializes the effective mask directly. Existing proxy 0.9.1-dev supplies
held-class eligibility; **no new DLL, signed client release, SQL migration or
ItemData layout change is needed**. A loader/cache refresh requires the
supported whole-game restart; rule/quest reload alone is insufficient.

## Catalog audit

Bounded read-only production catalog evidence at 2026-10-16 09:58 UTC covers
254,315 wearable/augment definitions, including quality variants and content
outside the active era. It is not a count of currently obtainable items.

- 90,852 definitions would have race masks changed by this policy.
- 1,535 no-playable-class/race definitions are preserved; 1,499 have no playable
  race, including 432 with unsupported high bits instead of a zero mask.
- 17,171 definitions matching PAL/WAR/MNK would cease failing Half Elf race
  eligibility. All other requirements still apply.

`catalog-audit.json` contains only item aggregates/examples and derived scope.
Private character diagnostic details remain in the task workspace, outside Git.

## Verification

- The initial compiled loader regression failed on Half Elf eligibility before
  the policy was added, then passed. `tools/tests/test_equipment_race_policy.py`
  compiles the actual loader restriction block and actual SwapItem function:
  420 class/race/type combinations, all 23 worn slots, augments, non-player
  sentinels, and both move directions with class/deity/level/slot controls.
- `eq-client-dll/tests/equipment-native.cpp`: 78 checks pass against the pinned
  exact RoF2 image, production hooks and actual native race/equip/inspection
  instructions. Raw Bronze Knuckles fails; projected data passes primary and
  green inspection for all 16 playable races. Offhand, unheld/non-player items,
  worn armor and two-handed conflicts retain rejection. Inventory access and
  object lifetime are fixtures; deity/level/required-skill helpers remain
  controlled fixtures. Server SwapItem tests independently exercise those gates
  except required skill. These are not live gameplay acceptance claims.
- Seven client runtime groups and adjacent FreeTrade (6), DisableLore (2),
  divine-summon (3), equipment (2), cache-corruption (4) test groups pass.
- The retained divine-summon archive and pinned link inputs must first relink
  to the exact deployed loader `139194a9…`. Only `shareddb.cpp.o` is replaced;
  126 other archive members are identical. The full native candidate links,
  resolves its runtime libraries and preserves the 1,332-byte ItemData ABI.
  Exact source/input/binary fingerprints are in `build-manifest.json`.
- `rehearse_cache.py` exercises actual old/new/old loaders against a uniquely
  named disposable local content DB. `cache_check.py` checks every loaded race
  mask against raw SQL and policy, and hashes the complete cache excluding only
  intended race fields (including headers, lookup entries and record order).
  Require all preserved hashes equal and rollback cache byte-identical. The
  final tested binary and counts are recorded in `cache-rehearsal.json`.
- Independent review found a retained-archive provenance gap, now addressed by
  the mandatory baseline relink. No functional policy/test defect was found.
  The owner declined an optional second-model review.

## Rollout and rollback boundary

No production writes, service restart, main merge or client publication were
performed for this candidate. Obtain scoped owner approval for promotion and
the server restart. The earlier client-publication approval covered a different
release. Preserve the latest AA-duration zone `19cd3387…`, current world/login/
UCS and signed client 2026101501; never replace them with older retained builds.

Use the current staged activation/recovery procedure from
`../aa-temporary-buffs-20261015/deployment/rollout.py`, scoped to shared_memory,
with this release's full-cache checks. Pin a fresh baseline and complete
manifest; hold deployment/GM locks, verify a fresh backup and retain the current
immutable image. Close gateway, stop the whole game cleanly, snapshot player/
custom checksums, replace only the loader in a layer on the current image, and
let startup regenerate the item cache. Before reopening, verify all 12 zones,
unchanged other binary hashes, unchanged SQL/player/custom/rules/content/public
assets and identical normalized old/new cache hashes. Recheck the signed client
pair and healthy restart count. Persist evidence before reopening.

Before access opens, a failed check restores the exact previous image/cache;
never restore an old player DB. A lost gateway acknowledgment or post-open
failure holds access closed for reconciliation without replaying old inventory
or uncertain activation. Rollback reintroduces ordinary race restrictions and
must account for gear equipped after this policy was active.

## Owner QA after authorized deployment

1. Relog through the existing current launcher/client; equip Polished Bronze
   Knuckles in primary while the shield remains secondary. No rejection/resync.
2. Try secondary: it remains prohibited because its Slots mask is primary-only.
3. Check one held Monk-only wearable and one genuinely unheld-class item in
   inventory/inspection. Eligible gear is green; unheld equipment stays red.
4. Check an excluded pet-only item, deity mismatch, above-level item, two-handed
   conflict and augment fit restriction remain prohibited.
5. Verify javelin ranged/ammo still works, relog retains equipment, and releasing
   Monk removes eligibility for Monk-only equipment after identity refresh.

Record actual results separately from native fixtures and rollout health.
