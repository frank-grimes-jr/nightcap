# Instance Keeper readiness repair — November 6 authorized release

The owner reports that Raid and Grind fail in Crushbone with “Dungeon schema,
catalog or item cache does not match this release.” This is a shared admission
failure, before allocation/enrollment writes. Do not reset runs to work around it.

## Cause and evidence

Read-only production capture at 18:39 UTC against the **actual retained November6
augment build** passes all51 schema checks and669 of671 content checks. Only
`vigil/items/0` and `compact/items/0` fail: each matches4 instead of8 records.
Their SQL predicates and native `CacheMatches` still expect the pre-November6
Chapterhouse/Kael augments. The augment rollout's rehearsal adjusted operator
expectations but did not update these compiled native admission guards.

The first comparison against main's selective mirror also found historical Hate
drift. That mirror still has650 checks/176placements; it is not the live source.
The retained deployed header SHA256 is
`dfc7aadabc49f94c800070079ad5fa3a97d81ece107b6a59579b68ec318ffc81` and has671
checks/223placements. Both the November4 and November6 retained build headers
match it. The copied106 Hate layout/density/landmark checks are byte-equivalent
as parsed SQL records to that authenticated retained header. Preserve them.

The corrected target passes **all51 schema and671 content checks** against live
production at18:45UTC (`production-target-contract.json`). This was read-only:
it does not establish that the new binary is installed or that a player entered.
The native fixtures and build manifest record their separate results.

## Scope and verification

`tools/dungeon_refresh_contract.py` overlays only the eight reviewed expedition
augment deltas from `docs/audits/augments-20261106/item-preimages.json` onto the
historical content compilers and SQL checks. It rejects compiler/SQL preimage
drift and requires one exact item predicate per delta. Existing reward rows
in the same batches remain. Active Kael focus effects also check their native
Type/Level/Level2. No expectations are learned from mutable production values.

Relative to the retained deployed contract, exactly two SQL checks and eight
native item cases change. All schema, all669 other content checks, other cache
cases, Hate placements/bosses, revisions and earned run state remain. Re-running
the generator produces identical JSON/header bytes. Historical setup SQL stays
frozen; **do not rerun a dungeon/augment migration**.

The dungeon regression suite also corrects its stale pre-November6 loot-order
assertion: dungeon cleanup precedes Hunt awards so it cannot remove new augments.
Native gameplay code/order does not change in this repair.

Run from this checkout:

```powershell
python -B tools/dungeon_refresh_contract.py
python -B -m unittest discover -s tools/tests -p 'test_dungeon_*.py' -v
python -B -m unittest discover -s tools/tests -p 'test_augment_*.py' -v
python -B tools/build_dungeon_readiness.py
python -B tools/relink_dungeon_current.py
```

The native builder is an isolated, one-use build against retained sources and
authenticated objects. It reproduces augment zone`bc88a468` before linking the
replacement dungeon TU. The mandatory current-baseline relink then authenticates
and retains the newer deployed report command archive, reproduces current
zone`ea6ad532` (automatic Stats window), and relinks that baseline with the repaired dungeon object. The
second manifest`native-build-current.json` owns the deployable candidate pairing;
the first build alone would omit the newer automatic Stats release. Both preserve the
same dungeon source and compiled contract baseline. It tests the real ItemData/CacheMatches with all eight
released afterimages: old guards reject them, repaired guards accept them, and
changed icons/healing/focus metadata still reject. It preserves every other
cache case and validates stripped ELF identity. Failed attempt directories are
evidence; do not overwrite/replay them without choosing a new isolated path.

## Activation boundary and recovery

**Owner authorized main/OVH promotion for live QA.** See
`deployment/AUTHORIZATION.md`; activation receipts establish actual deployment.
Owner entry/gameplay acceptance remains open.

This is a **zone-binary-only** repair, paired with the current November6 content,
shared item cache, world/shared_memory and signed0.13.4/2026110603 client. No SQL, cache
regeneration, quest/rule reload or client update is needed. The unrelated
automatic Stats/#augstats follow-up deployed during investigation is preserved by the
mandatory current-baseline relink. Never deploy an older augment-only candidate
over it or treat a selective source mirror as the complete runtime.

After authorization, prepare a fresh guarded release chained to the November6
automatic Stats operator. Before stopping, verify live binary/image/source pins, all corrected
contract checks, exact current item/cache hashes, services, rules, client/wiki
publication, zero players and free space; take deployment/GM locks. Close
admissions, stop the whole game using its supervisor, verify native shutdown,
take a fresh stopped full backup and retain all saved-state fingerprints. Install
only the new zone image layer. Verify all12 worker hashes, health, no native/DB/
quest errors, unchanged caches/content/rules/quests/client, modeled normal boot
expiry and exactly one native market rotation before opening. Retain the UUID
ledgers, corpse envelopes, timers, claims and all player state.

Failures hold admissions closed. A pre-opening rollback can select the exact
compatible current automatic Stats image, preserving current data; it returns to the known
Keeper failure and is not a fix. After opening, capture fresh state and recover
forward. Never restore an old player/run snapshot, repop a live run or kill one
zone process: production child exit restarts the entire runtime.

## Exact owner QA after authorized activation

1. In **public Crushbone58**, hail **Instance Keeper998801** within50units.
   With no unexpired run, choose **Grind**. Expect entry, its Tasks checklist and
   Keeper Status; the schema/catalog/cache error must be absent.
2. Kill an ordinary enemy and a required boss; check normal Grind respawn,
   personal boss credit and retained credit after leaving/re-entering. Check
   `#instances`, Enter and grouped Join with an eligible enrolled leader.
3. Test **Raid** with a separate eligible character/run. Expect harder stats,
   permanent defeated spawns, six Crushbone objectives and the final-boss gate.
   Do not erase an active run just to alternate modes. Reset only an explicitly
   disposable run after leaving it and verifying no players/pending entries or
   recoverable player corpses remain.
4. Level50 campaign testers should enter Chapterhouse from the West Commonlands
   Keeper998820 and Kael from Everfrost Keeper998860. Expect their existing
   personal story/dungeon journals and earned claims to remain. Ember healing
   and Cinder focus/icon values must match the already-released augment guide.
5. Resume an existing Hate run through Commonlands Keeper998812. Preserve
   progress/HP/timers/loot; verify223points and the organ/Hand/throne landmarks.
   New player gameplay, full clears and balance acceptance remain separate QA.

Whole-wiki impact decisions and candidate release labels are in`wiki-review.json`.
Deployment/publication receipts separately establish runtime and wiki state.
