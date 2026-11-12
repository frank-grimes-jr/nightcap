# Stat augments replacing equipment icons

Status: owner-authorized deployment preparation November 12; native build and
isolated repair rehearsal pass. Activation/publication/visual acceptance remain
separate gates. Base: origin/main b7e404b2, fetched November 12,
2026. Worktree: `E:/EQ_Local_Dev/_worktrees/augment-item-icons`, branch
`codex/augment-item-icons`. The default workspace has older source and unrelated
edits and was not modified.

## Cause and correction

The owner's inventory screenshot shows equipment displaying augment artwork.
`ItemInstance::IsOrnamentationAugment` accepted any IDFile other than IT63/IT64,
including the empty IDFile on 224 of 232 captured Hunt augment definitions.
The other eight use IT63 and do not trigger that particular false-positive. The
insert/remove handlers call `UpdateOrnamentationInfo`, which then copies the
first misclassified augment's Icon, IDFile and Hero's Forge fields to the host.
RoF2 serializes the saved override, so this can persist after relogging.

The same predicate compared the AugType bitmask to the literal socket numbers
20 and 21. The correction tests bits 19 and 20, matching the type-to-bit mapping
used by `IsAugmentSlotAvailable`, and retains the existing explicit nonzero
Hero's Forge marker fallback. Empty or ordinary model IDs no longer confer
cosmetic intent. Real type-20/type-21 ornaments, combined type masks and Hero's
Forge still work; an ordinary augment earlier in the socket list cannot hide
the real ornament. Item power, stacking, socket eligibility and artwork are not
changed. No item definitions, schema, rule, cache format or client assets change.

Independent release review additionally found that unconditional recalculation
would clear a genuine mold/quest cosmetic override on stat-only operations. The
three native packet-handler calls now run only when the old target socket or an
Insert/Swap cursor item is a genuine ornament. The decision is captured before
callbacks/mutation; unrelated cursor ornaments do not affect Remove/Destroy.
The expanded actual-body/caller regression failed before these gates and passes
afterward, including transformation preservation and real ornament transitions.

## Authorized release preparation

Owner request: “Deploy the fix and repair the affected item icons, preserving
the augments and all other item data.” Owner confirmed Palwar logged out. Fresh
production probe matches the November 7 Last Lantern pair; all three native
baselines reproduce byte-for-byte. The retained overlay applies exactly two
reviewed source deltas and compiles both common-library variants and the packet
unit. Three matching candidate binaries link; ELF loaded-byte checks pass. The
actual three dependency closures cover 182 files, including 179 authenticated
source-header dependencies. See `native-build.json` and the build/audit tools.
V1's patch utility rejected CRLF context without changing production; V2 verifies
complete normalized retained/base equality before writing the exact two files.

Fresh private captures identify exactly five equipped Palwar items: slots 2, 12,
17, 18 and 19, items 404301, 404345, 204852, 404856 and 204917. Three match current
augment gem icons; chest/legs still have old Understone icon 517, authenticated
by the November 6 definition preimage for augment 940280. All five have no real
socket ornament and zero saved/base Hero's Forge and model overrides. Restore
the owner-requested base icons by changing only `ornament_icon` to zero.

`repair.py` hashes each complete SQL JSON row on the server, locks the exact
character/slot/item preimage, changes one column, and checks the full afterimage
inside one transaction. All 205 character rows and all unrelated inventory rows
are checked. The real MariaDB rehearsal proves atomic rollback, last-target
metadata drift rejection, successful five-field repair and replay refusal.
Raw player rows, backups, SQL and diagnostics remain private; none enter wiki
artifacts. `rollout.py` retains deployment/GM locks, zero-player/auth drain,
supported whole-runtime stop, fresh stopped full backup, normal saved-state and
market boot checks, native hashes, unchanged content/rules/cache/quests/client
and verified reopening. No player snapshots are restored. Rehearsal V1 used an
unsupported staging-schema prefix and stopped before row loading; V2 uses the
transport's accepted isolated prefix and passes all checks.

Independent review also found a preexisting Hero's Forge load/raw-save defect.
It is excluded from this release: naive loader changes would corrupt shorthand
values. The five repaired rows have zero saved/base HF, and every other field is
verified unchanged. Preserve this separate follow-up; do not silently broaden
the icon repair into a global cosmetic migration.

Source: `server-mods/code/common/item_instance.cpp`, specifically
`IsOrnamentationAugment`, `GetOrnamentationAugment`, `UpdateOrnamentationInfo`.
Other relevant paths: `zone/client_packet.cpp` insert/remove handlers;
`common/shareddb.cpp` inventory load/save; `common/patches/rof2.cpp` serialization.
The latter paths were inspected, not changed.

## Verification

`tools/tests/test_augment_ornament_native.py` compiles and executes the actual
three production methods and the actual ornament-type enum using bounded item
storage doubles. It first failed on the old implementation's acceptance of a
type-22 Hunt augment with empty IDFile; the same test passes after the correction.
The controls cover ordinary masks/model IDs, literal numeric 20/21, missing
definitions, invalid host class, six-socket selection, real ornaments behind
stat augments, Hero's Forge, removal and stale-field clearing on recalculation.
This is compiled method evidence, not a full server build or rendered-client QA.

Focused command (run from this checkout):

```powershell
$env:PYTHONPATH='tools/tests'
python -X utf8 -B -m unittest -v test_augment_ornament_native test_augment_audit test_augment_expedition_native test_augment_stats test_zone_hunt_native test_item_xp_metadata test_free_trade
```

See `verification.json` for the final test and wiki-check results. The first
23-test run passed 22 tests; one existing test used Windows cp1252 to open UTF-8
source and failed to decode it. Its isolated rerun with `-X utf8` is recorded
separately. No product/test assertion was weakened to bypass that environment issue.

## Release and already-affected items

This source change prevents new misclassification. It does **not** rewrite saved
cosmetic metadata: `SharedDatabase::GetInventory` reloads `ornament_icon` and
`ornament_idfile`. Restarting or relogging alone is not a repair for saved rows.
Do not tell players to destroy/remove augments as an incident workaround.

Before an authorized activation, build/relink all affected native consumers from
the current retained production source pair. Preserve the metadata-aware
world/zone/shared_memory baseline and newer released systems. No new client
download or item-cache regeneration is required by this predicate-only change.
OVH activation uses the supported whole-runtime shutdown/restart with fresh
stopped backup; never kill one zone process. Rule/quest reload cannot load C++.

Already-affected rows need a fresh read-only incident capture and a separately
reviewed exact forward repair. Identify the player's affected slots and compare
the full current row, current socket definitions and any known intentional
cosmetic choice. Matching an augment icon alone does not prove an override was
accidental. Preserve augments, charges, color, binding, custom data and GUID;
guard the exact preimage and change only confirmed erroneous cosmetic fields.
Do not bulk-clear ornaments or restore an old player inventory. No production
capture, inventory repair or deployment is claimed in this change.

## Owner in-game QA after authorized activation

1. Record item names, icons, sockets, bonuses and intentional cosmetics before
   testing; use expendable test items, not the owner's valuable equipment.
2. Insert a compatible type-22 Hunt augment (for example Hillside Dewstone,
   item 940024) into eligible armor. The augment keeps its own gem icon; the
   armor keeps its original icon and model, with the expected stat increase.
3. Test every supported worn armor slot and a second stat augment. Inspect the
   item, move it between equipment/bag/cursor, zone, then log out/in. Icons,
   stats, socket IDs and saved metadata remain correct.
4. On compatible ornament-enabled test equipment, combine a genuine type-20 or
   type-21 ornament with stat augments, including a later ornament socket.
   The genuine ornament wins regardless of socket order. Verify Hero's Forge
   and ornament removal restore the appropriate appearance.
5. After any separately authorized exact repair of the originally affected
   slots, verify those items retain all earned data and correct icons through
   a relog. Verify unrelated intentional ornaments are unchanged.

Full native build, deployment, saved-row repair and owner visual/gameplay
acceptance remain separate open gates.

## Wiki impact review

Reviewed all 42 authored articles, Home and Features, commands, generated item/
zone/catalog projections and current November 7 release evidence. The owning
Equipment and Zone hunt guides, In development and Change Log receive explicit
Not released candidate notes. Home/Features need no new feature entry for this
display repair; commands, rewards, item/zone values and acquisition are unchanged.
Generated pages therefore need no catalog edits. Existing release labels remain.
`wiki/check_refresh.py --repo . --ref HEAD --include-worktree` reports historical
global drift; the complete result is retained without advancing its ledger.
Local previews are not public publication. The latest reviewed publication evidence records the November 7 release; this
change does not perform a fresh public probe or authorize publication.
