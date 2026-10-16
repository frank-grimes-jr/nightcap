# Multiclass equipment and inspection — October 15, 2026

Status: **merged and published as signed game release 2026101501; owner confirms
javelins work; broader gameplay QA pending**.
Proxy 0.9.1-dev corrects cursor placement and inspection eligibility. This is a
client-only change merged in PR #202 (`f1c9271`); no server restart, cache
refresh, item definition edit, character update or database migration is needed.

October 16 follow-up: Bronze Knuckles revealed a separate server race restriction.
See the [race-policy audit and candidate](../equipment-race-policy-20261016/README.md).
That follow-up does not invalidate the javelin correction or imply full owner QA.

## Report and diagnosis

The owner reported that Palwar (Paladin/Warrior/Monk) cannot equip Forged Javelin
and sees other unusable items colored green in inventory/item inspection.
An explicitly authorized SELECT-only production check at 09:09 UTC confirmed
the three held classes. Forged Javelin 21508 and its three quality variants have
class mask 33225 (including Warrior and Monk), race mask 65535, deity 0,
required level 0 and slots 4196352 (ranged/ammo). These restrictions permit this
combination. The private diagnostic remains in the task workspace, not Git.

Two distinct client paths caused contradictory behavior:

- Cursor placement at RVA `0x296095` was routed through a scroll-only wrapper.
  Ordinary equipment kept the primary Paladin mask check, blocking the javelin.
- `CanEquipItem` at `0x183550` is also called by item inspection. The old
  item-scoped hook widened every nonzero class mask to all sixteen classes,
  making unheld equipment pass the inspection loop and become green.

## Implementation and boundaries

`equipment_scope.h::EquipClassMask` now projects the primary class bit only when
the original item mask intersects the current held-class mask. The accessor in
`dllmain.cpp` requires matching current player identity; absent/stale metadata
keeps the native primary behavior and requests the existing bounded refresh.
Zero masks, native item data, other items/threads and accessor flags stay intact.
Nested scopes restore through SEH `__finally`.

`CanUseInventoryItem` dispatches scrolls to the existing canonical spell policy
and equipment to held-class eligibility. The cursor call and direct inspection
call at `0x2A9D82` use it. The native type selector at `0x2A9D07` chooses between
the slot loop and direct path for two-handed weapons, shields and augmentations.
The new direct call is covered by the signed catalog's exact five-byte guard.
Race, deity, level, slot and other native predicates retain their arguments and
results. The server remains the final authority through `GetEquipClassBitmask`
and `InventoryProfile::SwapItem`; no widening of stored item masks is needed.

## Verification

- Before the fix, the mapped exact-client regression failed six checks, including
  Forged Javelin cursor placement, unheld-item rejection/color and class release.
- The corrected test executes actual native CanUseItem, CanEquipItem, inspection
  type dispatch and color writes with production hooks: **37 checks pass**.
  Native restriction helpers are controlled fixtures, not full gameplay claims.
  Covers ranged/ammo/wrong slots, all five direct-path item types, held/unheld
  classes, class release, stale/missing identity, canonical scroll placement,
  and preservation of non-class restriction failures.
- Equipment scope tests cover **4,096 primary/held/item combinations**, item,
  thread and flag isolation, nesting, zero/high masks and invalid metadata.
- Full x86 proxy and 19 runtime fixture builds pass. All **7 runtime groups**,
  including trainer, spell, tradeskill, pet and failure-injection controls, pass.
  Run the suite with TEMP/TMP inside an accessible task scratch directory; the
  sandbox default temporary directory prevents native file creation/cleanup.
- All **95 exact-client catalog guards** and generated launcher catalog checks
  pass. The reference eqgame.exe remains unchanged. Launcher tests and final
  review evidence are recorded in `verification.json`.
- Independent review found no production defect and identified a forced-branch
  test gap. The fixture now starts at native item-type dispatch with realistic
  types. The owner declined an optional second-model review.

Commands from the repository root:

```powershell
eq-client-dll/tests/run-equipment-native-tests.bat <read-only-eqgame.exe>
eq-client-dll/tests/run-equipment-scope-tests.bat
eq-client-dll/build.bat
eq-client-dll/tests/build-runtime-tests.bat
python eq-client-dll/tests/test_runtime.py --eqgame <read-only-eqgame.exe> -v
eq-client-dll/tests/verify-exact-client-patch-sites.ps1 -EqgamePath <read-only-eqgame.exe>
python tools/generate-client-patch-catalog.py --check
# In eq-launcher/:
go test ./...
```

## Publication and recovery

The owner explicitly authorized push, main merge and signed client publication.
PR #202 merged tested source `55d6b43` as `f1c9271`. Game release **2026101501**,
proxy **0.9.1-dev**, was published October 16 on `play.nightcapgame.org`. Its
production-key signature and all **106 hosted assets** verify over HTTPS. Only `dinput8.dll`
and `nightcap-patch-sites.json` changed from fresh live release 2026101304;
104 other assets, launcher minimum 0.6.0, prior notes and tombstones are preserved.
Desktop channel, stable starter, guide and all five service identities/start
times/restart counts remain unchanged. No server restart or database write.

The publisher holds the shared deployment lock, refuses public/service drift,
verifies immutable assets before channel replacement, and fsyncs every nested
directory deepest-first before publishing. All **13 recovery tests** pass;
independent review of the publication flow has no remaining actionable findings.
Evidence: `deployment.json`, `published.json`, `hosted-verification.json`,
`publication-diff.json`, `signed-release-audit.json` and `verification.json`.
Metadata expires **2026-11-14T09:47:47Z**; future renewal uses a new signed counter.
The initial upload was interrupted before staging or channel publication. The
next-day baseline refresh found only an independent healthy game restart on the
same image; public bytes were unchanged. The final publication retained that
refreshed runtime, without restarting any service.

Use `docs/ops/permanent-patcher.md`. Upload immutable assets before replacing the
signed channel; verify the signature and every hosted file. No native server or
database operation belongs to this release. Close EQ and use launcher Play after
publication. Rollback is the previous matching DLL/catalog in a newly signed
release with a higher counter; preserve all items and subsequent player activity.
The unsigned candidate delta is build evidence, not a manual-install release.

## Owner gameplay QA — pending after launcher update

1. Close EQ, update through launcher Play, log in Palwar and confirm the inventory
   class labels read PAL/WAR/MNK. In East Commonlands inspect Forged Javelin
   21508 (or an owned quality variant): it should be green and retain its original
   printed class list. Move it from a bag/cursor to ranged, then ammo. Both valid
   placements should succeed. Chest placement must fail without losing the item.
2. Inspect and attempt an actual unheld-class item, such as a Necromancer-only
   robe legal for the character's other restrictions. Expect red and rejection.
   Record the exact item ID so its original mask and restrictions can be checked.
3. Inspect legal off-primary two-handed weapons and shields, and corresponding
   unheld-class controls. Verify colors and equipment; retain normal conflicts
   between two-handed primary weapons and an occupied secondary slot.
4. Check wrong-race, deity-restricted and above-required-level equipment, an
   invalid augment combination and wrong-slot placement. They must stay blocked.
5. Zone and relog after legal off-primary equipment; verify retained inventory,
   stats and ranged use. Use a disposable QA character for class release and
   re-adoption; close/reopen inspection after each change and verify eligibility.
   Do not release Palwar's classes as part of this test.
6. Confirm held-class scroll scribing, unheld scroll rejection, trainer purchases,
   offhand equipment and Craft All still work. Runtime fixtures do not establish
   live rendering, transport, class-refresh timing or owner acceptance.
