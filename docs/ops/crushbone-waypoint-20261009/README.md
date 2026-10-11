# Crushbone entrance waypoint — October 9, 2026

Owner-authorized relocation to the existing entrance safe point:
**world X=158, Y=-644, Z=4, heading=0**, or **`/loc -644, 158, 4`**.
Deployed to OVH production on **October 11, 2026**, from main commit
`e8f40d1b1e63fe4471c1b85f04e50d539e7be6d1`. Manual rendering, discovery and recall
acceptance remains open.

## Production verification — October 11

The approved migration committed the entrance coordinates to the waypoint,
marker spawn and its matching saved marker row. All columns in the
scoped waypoint, Crushbone spawn and Crushbone saved-state snapshots matched
the expected result after commit and again after game startup. Existing gateway
and game containers restarted successfully; all five services are running,
game/database are healthy, and all 12 native zone workers are available.

Eight automated tests passed. Live MariaDB forward, exact inverse and stale-row
rollback rehearsals passed before commit. The verified full PEQ backup contains
449,093,530 uncompressed bytes. Backup SHA-256:
`2d1a516bcfce98fc679db2cd721f80bd062ebeea85ae9b9631a5289fa33ecbe2`.

[Machine-readable deployment result](deployment-result.json). Full private
backup, snapshots, payloads and exact rollback are retained in the evidence
directory below. The original failed-attempt backup is preserved separately.
No client, quest or binary update was required. Player acceptance steps remain
listed below; database and runtime checks do not replace them.

## Scope and cause

The original July 16 setup (`5ae4f7b`,
`eq-solo-gm/scripts/waypoints_setup.sql`) used outdoor spell eligibility
(`zone.castoutdoor`) to classify dungeons. Crushbone permits outdoor spells,
so its waypoint was placed at the farthest native spawn: world 610,292,2,
exactly overlapping orc spawn 85. The live waypoint and spawn records matched.

The correction changes only Crushbone's destination row, marker spawn 3266061
(NPC 999240, group 999240, version 0), and matching non-corpse marker states in
base instance 0. The waypoint metadata becomes `is_dungeon=1`; the zone's
outdoor-spell setting is preserved. Existing character discoveries, other
waypoints, native orcs, corpses, other instances, HP, loot and buffs are retained.
No new gameplay power, item, currency or reward is introduced. Entrance recall
avoids skipping to the distant orc spawn; attunement becomes accessible on entry.

## Apply and recovery

Run `python -I docs/ops/crushbone-waypoint-20261009/run.py check` for syntax and
SQL scope tests. `apply` is the explicitly authorized production operation. It
requires the implementation commit to be on `origin/main`, uses the existing
SSH agent/key, and sends the exact checked-in SQL/helper to OVH.

The operation refuses online players, acquires the shared deployment lock,
stops only gateway/game, and takes a verified full PEQ backup with both stopped.
Production has `Zone:KillProcessOnDynamicShutdown=true`, so a zone unload is
not a process-preserving alternative. The approved maintenance restart uses
the existing containers and installed binaries; it does not pull/recreate them.

The runner locks the scoped database rows, requires the exact old durable
coordinates and entrance safe point, and rehearses forward, exact inverse and
stale-preimage failure before committing. It compares every column in all
waypoint rows, Crushbone spawn rows and Crushbone saved-state rows against the
expected result. Only marker coordinates and classification may differ.

Evidence: `/opt/nightcap/backups/crushbone-waypoint-entrance-20261011/`.
It contains the full dump, before/after snapshots, exact saved-state inverse,
SQL payloads, service snapshots and result. If an operation fails, inspect
`result.json` and live data before retrying; the runner refuses to overwrite
evidence. On failure, the runner retains the deployment lock and restores services only
when the database matches a complete original or relocated snapshot; it checks
again after game startup. Mixed or unknown outcomes keep the gateway closed. Do not rerun partial SQL blindly.

For rollback, close gateway/game during an empty-server window, take a fresh
backup, verify the relocated rows, and use the durable inverse plus the exact
saved-state inverse for the captured checkpoint. After players resume, capture
current state and reverse only marker coordinates; never restore stale whole
zone-state rows. Preserve current HP, loot, corpses, discoveries and receipts.
The full PEQ dump is disaster recovery, not the normal rollback mechanism.

## Verification and in-game QA

The SQL tests exercise unrelated waypoints/orcs, saved corpses, other instances,
NPC and placeholder states, repeat execution, stale durable preimages and
inverse placement. Production rehearsal additionally checks MariaDB transaction
and CHECK-constraint behavior against actual rows and float values.

After service recovery:

1. Enter Crushbone from Greater Faydark with an unattuned ordinary character.
   Find `a waypoint` / `Stand Here to Attune` near `/loc -644, 158, 4`.
   Check grounding and that approaching it does not bounce through the zone line.
2. Walk into its 25-unit horizontal / 30-unit vertical proximity. Verify one
   attunement message, a Crushbone discovery and the expected discovery count.
3. Leave and return. Verify no duplicate discovery or reward.
4. Use Waypoint Master travel to Crushbone. Verify arrival at the entrance,
   correct grounding, no unintended zone crossing and no immediate hostile spawn.
5. Check an already-attuned character: Crushbone remains available and uses the
   new arrival. The old orc at world 610,292,2 remains normal, without a waypoint.

Database/restart verification does not constitute these player acceptance checks.

## October 11 verification repair

The first October 11 attempt used the original `...-20261009` evidence directory.
Its full backup passed, but a forward rehearsal assertion failed. The SQL was
rolled back and automatic recovery verified the original snapshots before and
after game startup, then reopened the gateway. No waypoint row was committed.

Temporary copies of the live MariaDB tables proved that every resulting field
was correct; sorting serialized rows compared integer `0` with float `0.0` and
changed row order. The verifier now sorts by each table's primary identity and
still compares every field. A regression fails on the original comparator,
six tests pass after correction, and the same temporary-table reproduction now
passes. The retry uses the separate `...-20261011` directory above.

The next retry aborted before maintenance when native zone status included
non-UTF-8 bytes after its completed summary. Source inspection found that the
native status sender passes an unterminated `fmt::memory_buffer` to a `strlen`
API. The helper now decodes only through the explicit terminal, validates the
entire summary and requires matching row totals and unique server IDs. This is
bounded to the current small status response; malformed intermediate chunks
still fail closed. Eight tests and an exact live read-only check pass.
