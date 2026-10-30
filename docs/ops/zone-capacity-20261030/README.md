# Zoning capacity correction — October 30, 2026

Status: tested candidate; **not deployed**. Production still has 12 workers and
the original timers. Main promotion, maintenance activation and player QA are
pending. The October 30 capture found only 512 MiB free on the 72 GiB host disk;
the resource preflight correctly refuses rollout. Do not relax that gate.

## Problem and selected solution

Palwar's October 29 19:43:33 EDT Fear transfer failed because all 12 workers were
holding previously visited zones. World emitted `failed to boot a zone for
[Palwar]`; the client returned to Feerrott at 19:43:37. Misty freed the first
worker at 19:53:42. See the read-only incident record at
`E:/EQ_Local_Dev/docs/ops/fear-entry-20261030/README.md` and its retained evidence.

The candidate increases the supervised pool to **20**, within the existing
7000–7030 private port range, and changes these exact public version-0 rows:

| Zone | Previous retention | Candidate retention |
|---|---:|---:|
| East Commonlands | 60 minutes | 5 minutes |
| Rivervale | 60 minutes | 5 minutes |
| Feerrott | 60 minutes | 10 minutes |
| West Commonlands | 60 minutes | 15 minutes |
| East Karana | 60 minutes | 30 minutes |

Only `zone.shutdowndelay` changes, under full captured row, identity, version,
engine, trigger and transaction guards. All other fields and 613 zone rows remain
unchanged. Occupied dynamic zones do not unload at expiry; static zones bypass
the empty-zone shutdown path. No respawn, instance lifetime, loot, character,
corpse, checkpoint, quest or reward row is edited. Quest timers continue while
NPC AI is idle. Mixed retention exceeds inspected finite quest cleanup windows.

Preserve Misty's stateful seasonal encounter, Highpass's combat-paused Stanos
timer, all dungeon timers, public Fear's boot-sensitive encounter, and special
Sky/Kithicor/Tacvi retention. The independent recursive installed-quest review
and exact inspected source hashes are in `review.md` and `quest-review.json`.
Future quest/content changes require reviewing this small allowlist again.

This fixes the observed ordinary-travel failure with headroom and reuse; it
cannot promise unlimited simultaneously loaded destinations. The alternatives
were rejected for concrete reasons: 24/31 workers exceed the conservative
current memory envelope, a global five-minute cap changes timed encounters,
and pressure-driven native eviction needs admission/auth/save-failure coordination
and would introduce substantially greater risk. No native rebuild is needed.

## Resource assessment

The captured 8 GiB host had about 4.05 GiB available RAM, low CPU load, no game
OOM events, game current usage about 1.09 GiB and a 1.54 GiB cgroup peak. The
unchanged game limit is 4500 MiB. Budget eight additional workers at 256 MiB each
(above the largest observed 243 MiB RSS, including shared pages): projected peak
is about 3.54 GiB, leaving about 864 MiB below the game cap. This is conservative
planning based on observed workload, not a stress-tested memory ceiling.

No RAM/CPU upgrade is indicated by this capture. Disk is the immediate blocker:
about 19 GiB is retained release evidence/builds, 8.3 GiB the deployment tree,
and roughly 960 MiB local backups. Do not prune releases, images, checkpoints,
player data or backups to force deployment. Reclaim only separately reviewed
reproducible artifacts with verified off-host copies, or expand storage.
Require at least **3 GiB free before backup** and **2 GiB free after backup**.
Public saved-state replacement is not an atomic save-success gate; insufficient
disk makes more frequent unloads unsafe.

`tools/zone_capacity.py::activation_blockers` rejects stale/future captures,
insufficient disk/game/host memory reserve, changed worker baseline, unsafe
state-saving/process-exit rules, stopped/OOM services and game OOM counters.
It is a necessary preflight, not deployment permission or proof of maintenance.

## Reproduction and verification

From this feature checkout:

```powershell
python -m unittest tools.tests.test_zone_capacity -v
python -m unittest discover -s deploy/production -p test_compose.py -v
python -m unittest discover -s deploy/production -p test_production.py -v
python docs/ops/zone-capacity-20261030/capture.py docs/ops/zone-capacity-20261030/private/fresh.json
python tools/zone_capacity.py docs/ops/zone-capacity-20261030/private/fresh.json --output docs/ops/zone-capacity-20261030/private/fresh-plan --require-safe-resources
```

The capture reads complete zone definitions plus only non-secret resource/rule
metadata. Raw captures and generated SQL are ignored. The planner never applies
SQL and refuses changed preimages. Never reuse the historical capture to deploy.

The unit model reproduces the original 12-worker rejection, passes that route
under the candidate, and completes 160 two-minute travel transitions across eight
destinations while retaining 13 other destinations. The same 20-worker model
with one-hour travel retention fails: the timer change earns its place. This is
a capacity model, not a substitute for native client or resource load testing.

`tools/tests/rehearse_zone_capacity.py` reconstructs all 618 production zone rows
in a random local-only MariaDB schema, applies forward/inverse SQL, and verifies
the full exact table, replay rejection, drift rejection, unrelated-edit
preservation, trigger/engine refusal and progress sentinel preservation.
It rejects `python -O`. The 10.11 rehearsal matches production's MariaDB image;
`rehearsal.json` records eight passed groups. It does not write either PEQ DB.

## Activation after storage and approval gates

1. Obtain the repository-required main promotion sign-off and an announced
   maintenance window. Preserve the currently deployed immutable image and all
   three native binaries, quests, cache, signed client and public wiki identity.
   This release is only a Compose worker-count change plus five metadata rows.
2. Capture fresh resources/rules, complete zone rows, all service identities,
   exact current Compose bytes and their hash, native executable hashes and
   player/custom/saved-state preservation evidence. Run the strict preflight
   above before any service or DB mutation. Reconcile concurrent releases.
3. Record and close admissions using the established gateway maintenance
   procedure. Drain existing authenticated zoning and verify no players remain.
   Stop the **complete game service** gracefully; verify every native child
   flushed/exited normally. Do not kill individual workers. A zero container
   exit alone is not a successful native flush; the supervisor has a 75s limit.
4. Make and verify a fresh full PEQ backup after the clean stop, retain exact
   Compose preimage and inverse SQL off-host, and recheck at least 2 GiB free.
   Capture a fresh stopped DB preimage and regenerate the same five-field plan.
   If it differs, stop for review. Do not erase cached NPC/corpse/checkpoint data.
5. Apply generated `forward.sql` once through the existing protected DB client
   configuration. Require exact expected afterimages and preservation evidence.
   Change only `game.environment.NIGHTCAP_ZONE_WORKERS` from12 to20 in the actual
   current production Compose file, under its exact captured preimage. Do not
   upload an old full Compose template over newer production configuration.
   Resolve Compose and compare the full configuration: only this scalar changes;
   image IDs, mounts, networks, limits and credentials remain identical.
6. Recreate only the game service with `--no-deps`, using its exact current image.
   Full restart refreshes every process-local ZoneStore and newly loaded timer.
   ZoneData reload or SQL plus natural unload is insufficient. Expect the usual
   one authenticated market rotation on world startup, not an economy replay.
7. Verify all20 supervised worker PIDs and connections, unchanged binary hashes,
   required rules, five timer afterimages, unchanged613 zone rows, cache/client
   pairing, all player/custom/saved-state invariants and native health across
   at least15seconds. Check all needed private UDP ports and gateway routing.
   Historical release helpers asserting12 workers are frozen evidence: use a
   current20-worker status check rather than editing old receipts to make them pass.
8. Reopen admissions only after those checks. Record exact deployed hashes,
   runtime/service identities, DB verification and memory/disk observations.
   Monitor cgroup memory/peak/OOM counters and world boot failures during QA.
   Candidate wiki wording must be promoted/published only with this evidence.

If a write or restart acknowledgment is uncertain, stop and reconcile actual
state; do not blindly replay SQL or restore a stale player snapshot.

## Recovery

Retain the same compatible game image and earned state. If only the timers need
recovery, hold admissions, gracefully stop the complete runtime, capture current
rows, and apply the guarded inverse only if exact afterimages still match. A
later unrelated edit to a touched row deliberately blocks automatic inverse.
Restore the exact owned worker scalar to12 only if resource safety requires it;
this restores the capacity defect and must be labeled degraded recovery. Recheck
the resolved Compose diff and restart the complete game to refresh all caches.
Never restore player, inventory, checkpoint, corpse or whole-DB snapshots for
this five-field metadata rollback. No original client or native binary downgrade.

## Explicit owner QA

- As an ordinary account, repeat the incident route: East Commonlands → Misty →
  Rivervale → Kithicor → Highpass Hold → public High Keep → Keeper's High Keep
  run → Highpass Hold → East Karana → East Commonlands → Befallen → West
  Commonlands → Chapterhouse run → East Commonlands → Feerrott → Fear portal.
  Expected: no bounce to the source zone or world boot failure; Fear loads.
- Repeat ordinary travel for at least an hour, including returning through the
  five changed zones. Observe enough actual empty unloads to prove reuse rather
  than merely consuming extra workers. Keep another character elsewhere; their
  session remains connected throughout each natural unload.
- In Rivervale or East Commonlands, kill a suitable ordinary NPC, record loot
  and respawn deadline, leave for more than5minutes, and return. Verify remaining
  corpse/loot state and that the killed NPC did not respawn early. Do not use a
  named quest actor merely to test capacity. Keep the same worker PID through
  unload and require a native five-minute shutdown-timer log on boot.
- Revisit a public dungeon and a managed High Keep/Chapterhouse run with earned
  kills/rewards; their unchanged timers and saved progress remain intact.
- If eligible, check Duggin Scumber's West Commonlands10-minute cleanup and the
  East Karana Althele/Vance sequence through departure/return. Record content
  gates preventing execution rather than claiming acceptance. Preserve Misty's
  seasonal event, Stanos, Fear and Sky behavior outside this change.

Owner rendered/gameplay acceptance remains open. Wiki impact, verification and
independent review records distinguish candidate source from deployed behavior.
