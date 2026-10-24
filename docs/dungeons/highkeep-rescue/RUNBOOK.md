# High Keep prison-break candidate

2026-10-24. Implemented for review; not installed or activated. The user requested
the encounter redesign, not production promotion. Keep native gameplay acceptance
separate from source, build, database and map evidence.

## Release unit

Pair the rebuilt native **zone** with `server-mods/sql/20261024_highkeep_rescue.sql`.
No new world contract, rule name, shared item layout, quest script, cache, DLL,
spell file or client archive is introduced. Retain the deployed world/client pair.
The two new InnoDB tables are mandatory for High Keep Raid operations once this
zone is installed, even while enrollment is disabled. Missing/drifted storage
fails closed instead of silently turning a rescue into the old boss checklist.

`nightcap_highkeep_state` revision 2026102401 starts disabled. Only new Raid runs
created while enabled receive a `nightcap_highkeep_runs` row. Existing unmarked
runs, Grind and public High Keep keep their prior encounter layout and rewards.
The flag pauses enrollment; it does not disable already enrolled runs.

The native run projection relocates Boshinko spawn10145 to XYZ(-108,-11,3.75)
and McCabe spawn10117 to(-513,-3,-10.13), clearing their paths. It suppresses
10109/10210/10132/10156 only in enrolled Raid runs. No public spawn SQL is changed.
Saved alive populations receive the same projection; corpses and earned state
retain their normal authority. Rescue actors use NPC type0 and run/attempt tags.

## Authorized installation procedure

1. Obtain main/server approval under AGENTS.md. Refresh the live source, schema,
   supervisor and content baseline; reconcile concurrent releases. Do not install
   a binary built against an older retained source over a newer native release.
2. Hold gateway admission, stop the entire supervised game cleanly, and capture
   a fresh verified backup plus exact preimages. Never kill one production zone:
   the supervisor interprets a native child exit as a whole-game restart.
3. Check that both rescue tables are absent. Apply the additive migration once
   with enabled=0; inspect schema, keys, constraints and absence of triggers.
   A collision or partial DDL install requires examination, never DROP/replay.
4. Install the verified zone and start the controlled runtime with admission
   still held. Verify every running zone hash and existing health contracts,
   preserve all player/inventory/receipt/run state and other content, then test
   a managed High Keep boot. Confirm the map/navigation assets match the review.
5. Activate only after paired verification: set enabled=1 for id1/revision2026102401
   with an exact disabled precondition. Record affected rows and a release receipt.
   Reopen admission only after all preservation checks pass. Perform QA.md.

## Recovery

Before enrollment, keep enabled=0 while repairing a failed release. Once a rescue
run exists, retain its compatible native implementation and both tables. Setting
enabled=0 safely pauses new rescue runs while active rescues finish or expire.
**Do not boot old dungeon code over active rescue runs:** it completes rewards on
the fourth boss, bypassing extraction. An emergency downgrade needs a separately
reviewed admission/expiry policy; do not erase or restore earned player state.

Alarm and extraction commit with the existing no-retry run transactions. Any
database uncertainty suspends that zone's coordinator. Restart/reconnect reads
the durable outcome; existing inventory receipts deliver earned rewards once.
Never retry a claim by replacing inventory or deleting receipts. Unfinished
escorts return to the cell after reboot; alarm and boss deaths remain. Death or
90 seconds without a nearby living guide resets only the attempt after20seconds.

## Evidence

- `SPEC.md`: encounter, scope and reward contract.
- `QA.md`: exact owner gameplay gates and automated evidence limits.
- `sql-rehearsal.json`: actual migration and native eligibility SQL in a new
  network-isolated disposable MariaDB, removed after testing.
- `terrain.json`: seven positions/five samples each against map SHA-256
  `0640d5c11de83e128facb5b77331bf599b3d495e66974d22d8396527f9562a4b`.
  Point clearance is not navigation connectivity or visible client acceptance.
- `navigation.json`: native FindRoute connects all four legs in both directions
  using normal path flags, with no partial paths or teleport links. Actual
  movement through doors and combat remains an in-game check.
- `native-build-manifest.json`: full zone build passed, SHA-256
  `692cacd6852857fce1b0ac6f4e125f2d0267cde8a7c3728446ee6c4345fadba4`;
  retained source matches the final changed files. Isolated; never installed.

`tools/build_highkeep_candidate.py` verifies the retained Chapterhouse source
manifest before building. All seven edited pre-existing native files also match
the tracked ebeb6591 baseline after newline normalization. Final deployment must
repeat this comparison against its then-current live source.
