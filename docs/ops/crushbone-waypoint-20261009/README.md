# Crushbone entrance waypoint — October 9, 2026

Owner-authorized relocation to the existing entrance safe point:
**world X=158, Y=-644, Z=4, heading=0**, or **`/loc -644, 158, 4`**.
Implementation prepared for OVH production; deployment evidence will be added
after activation. Manual rendering, discovery and recall acceptance remains open.

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

Evidence: `/opt/nightcap/backups/crushbone-waypoint-entrance-20261009/`.
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
