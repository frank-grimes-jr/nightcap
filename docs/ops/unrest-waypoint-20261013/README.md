# Unrest entrance waypoint — October 13, 2026

Owner-approved PR #198 is merged and deployed on October 13. The controlled
restart completed and player access is open. No client update, quest change or
native rebuild. Owner portal/discovery/recall acceptance remains pending.

## Deployment result

Deployed commit `2e8cee8711c829b5b73f163bd1c7b718c9296b85` with the current runtime
image retained. Fresh stopped full backup, precision-preserving isolated restore,
exact forward/inverse rehearsal, fresh-preimage commit, closed-access preservation
checks and all twelve zone-worker health checks passed before reopening access.
The marker and recall destination are now DB XYZ `52,-38,3`, beside the unchanged
Keeper. The saved base marker pose moved with them; no discovery records changed.
The 68 local SQL, placement, visual, generator and recovery checks passed and
independent review found no blockers. [Sanitized production receipt](production.json)
records current positions, health, preservation counts and verification boundary.
Private backup and full snapshots remain only on OVH under
`/opt/nightcap/releases/unrest-waypoint-20261013/`.

## Cause and intended behavior

The reported eye is Instance Keeper 999228 at DB XYZ `52,-38,3`, the existing
Unrest safe point. Waypoint 999240 (spawn2 3266123) and the recall destination
are at `118,881,3.75`, about 921 units away. Standing by the eye therefore never
enters the marker's 25-unit discovery box. Both installed global quests match
the accepted visual releases; the bounded one-hour log check found no quest
errors. The read-only inspection found no saved rows for those two NPC types
in Unrest at that moment; activation must recapture after a clean shutdown.
See [sanitized inspection](inspection.json); no player records or raw logs were
exported. This establishes a placement mismatch, not rendered-client evidence.

The forward migration places the waypoint and recall at the existing Keeper
location, `/loc -38, 52, 3` (EQ displays Y,X,Z). It updates only the matching
non-corpse, non-metadata, instance-zero saved marker's pose, including dormant
NPC ID zero records. Other instances, corpses, unrelated NPCs, discoveries,
Explorer progress, dungeon classification, loot, HP and all nonposition state
remain unchanged. Existing private-instance saved markers retain their old
positions; new instances without saved state inherit the new spawn2 location.
The Keeper retains its eye appearance and interaction at the same position.

## Validation

Run from the checkout:

```
python tools/tests/test_unrest_waypoint.py
python tools/tests/test_crushbone_waypoint.py
perl tools/tests/waypoint_visuals.t
perl tools/tests/instance_keeper_visuals.t
```

The new placement reproduction first failed with the observed `118,881,3.75`
position. Five focused tests now pass, covering marker/recall alignment,
neighbor and progress preservation, rollback after newer NPC state, missing
saved state, and atomic refusal of drift in marker, destination or Keeper.
Eight adjacent placement tests and all 29 visual/discovery/Keeper assertions
pass. SQLite removes only MariaDB's transaction/locking/temp-table syntax;
native MariaDB rehearsal is separately recorded. Seven checks pass on local
MariaDB 10.5.4: forward alignment/discoveries, inverse with newer activity,
three preimage refusals, repeat refusal and absent state. Run
`python docs/ops/unrest-waypoint-20261013/check_mariadb.py` with the existing
`akk-stack-mariadb` image to recreate the disposable, network-isolated fixture.
[Native SQL results](mariadb-checks.json) use synthetic data and do not substitute
for the required fresh production-backup rehearsal. No gameplay acceptance yet.

## Activation after approval

`run.py stage`, `preflight`, `activate`, and `report` package the committed
release and run the verified operator. The operator adapts the current workshop
deployment's locks, backup/restore precision companion, runtime preservation and
activity-safe recovery. `tools/unrest_waypoint.py` generates the same reviewed
pose change from fresh full-row preimages, using the existing `content_patch`
transaction engine to reject engine/trigger/count/row drift. Static SQL remains
the readable migration contract; the operator executes the stronger generated
transaction. Six generator contract tests and 13 operator recovery tests pass.
Run them with `python tools/tests/test_unrest_waypoint_content.py` and
`python docs/ops/unrest-waypoint-20261013/ops/test_rollout.py`.

1. Promote the reviewed change through the repository's approval gate. Acquire
   `/opt/nightcap/deploy/production/.deployment.lock` and check current services,
   active native image, quest hashes and the player's opportunity to log out.
2. Stop gateway and game cleanly using Compose. Do not kill a zone process:
   OVH's supervisor restarts the entire native runtime on child exit. Capture
   fresh stopped state and take the standard full backup on the host; keep
   player data private. Verify all three affected tables use InnoDB.
3. Rehearse forward/inverse using a disposable restore before live SQL. Verify
   only pose changes on marker, waypoint and exact saved-state identities;
   preserve unrelated rows and all player data. Retain backup float-precision
   handling from the current workshop runbook when comparing full checksums.
4. Feed the freshly generated `evidence/forward.sql` to **one fail-fast MariaDB
   connection without `--force`**. Its exact preimage and Keeper guards abort stale/partial/repeated
   application. An error requires disconnect/rollback and inspection; never
   continue individual statements manually. Maintain the lock and closed access.
5. Compare fresh afterimages and preservation fingerprints before starting game.
   Start game, verify world and all zone workers, service health and absence of
   new quest errors. Confirm installed quests are unchanged and then open access.
   A controlled game restart loads new spawns and reruns the existing marker
   spawn handler (portal plus discovery box). Quest reload alone cannot move it.
6. Record hashes, backup/rehearsal result, deployed revision, exact positions and
   QA boundary here and in status/CHANGES and installed Nightcap knowledge.

## Recovery

Before SQL, leave the original placement and recover the original services.
After commit, prefer verified completion or the checked inverse. Capture a
**fresh stopped** state, take a new backup and run `rollback.sql` through the
same guarded one-connection procedure. It returns marker/recall/matching base
saved marker pose to `118,881,3.75`; it preserves newer HP/loot/buffs and player
activity rather than restoring historical full rows. Existing instance state
is retained. Drift or uncertain transaction acknowledgement requires inspection
with access closed. Never restore a stale player/database snapshot as rollback.

## Exact owner QA

1. Enter ordinary Unrest and approach the eye at `/loc -38, 52, 3`. Confirm the
   waypoint portal and nameplate are visible beside the targetable Keeper.
2. On a character without Unrest attunement, enter the 25-unit horizontal /
   30-unit vertical box. Expect one attunement message and one progress update.
   Leave/re-enter: no duplicate message. Previously attuned characters remain
   silent by design; do not delete their discovery records for this check.
3. Hail the Waypoint Master in East Commonlands and recall to Unrest. Expect the
   entrance coordinates. Hail the eye and confirm its Unrest menu still works.
4. Leave and return while another player keeps the zone running. Verify late
   arrival visibility, then verify the same location after a fresh zone boot.
   Test new-instance inheritance separately; existing saved private instances
   intentionally retain their current pose.
