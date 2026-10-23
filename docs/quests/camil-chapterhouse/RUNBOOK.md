# Chapterhouse candidate operations

Not installed. Source tests, native build, SQL rehearsal, map probes and arena
calibration are separate from production and player QA. Local-preimage SQL must
not be applied to production without fresh capture and target rehearsal.

## Reproduce

Run Chapterhouse, dungeon, Classic dungeon, Hunt and inventory receipt tests.
Generate with `chapterhouse_migration.py`; run `tests/rehearse_chapterhouse.py`,
then `dungeon_catalog.py`, `dungeon_refresh_contract.py` and
`chapterhouse_geometry.py`. `build_chapterhouse_candidate.py` verifies the retained
complete October23 source, overlays an explicit list and builds paired world,
zone and shared_memory under `/tmp/nightcap-chapterhouse-v1`, without installation.
Compare current input hashes to its manifest before promotion.

`chapterhouse_balance.py prepare` clones only an existing synthetic
fixture into a new database, refusing overwrite. No PEQ character data is copied.
Refresh its public definitions with `chapterhouse_balance_capture.py capture`
(SELECT-only production) then `restore` (allowlisted synthetic DB only). Use
`chapterhouse_balance.py diagnostics`, `build` and `chapterhouse_capstone.py`
with its separate `--controls` run. Do not use the stale October18 clone without
refreshing it. NPC 32040 is the diagnostic arena slot containing each authored boss row; live
Nagafen is unchanged. The runner excludes quest Perl and Chapterhouse navigation.

## Future authorized activation

1. Take a current backup and fresh bounded capture of zone 760, reservations,
   affected content, task/item references, active instances, engines and triggers.
   Rebuild and rehearse a target-specific guarded migration. Preserve concurrent
   releases and confirm the actual integrated source, not an older local overlay.
2. Back up and invalidate only zone 760 / instance 0 non-corpse saved spawn rows.
   The installer refuses those rows. Keep player corpses and unrelated states.
   Never enable Rain of Fear globally or edit the protected reference client.
3. Install both new campaign tables before the paired runtime. Its dungeon
   contract expects 45 schema and 532 content checks, including Chapterhouse.
   Apply guarded content atomically. Campaign state starts disabled. Install
   generated catalogs, matching world/zone/shared_memory, item cache and exact-ID
   scripts together. Remove no unrelated scripts; ensure no stale Chapterhouse
   default.pl/default.lua shadows global Keeper/waypoint handlers.
4. Verify all content/cache contracts, helmet 990500, disabled stock flag, public
   saved-state isolation, exits, level requirement and script hashes. Only then
   enable `nightcap_vigil_state.enabled=1` in an authorized maintenance release.
5. Production's supervisor restarts the whole runtime on any native child exit.
   Use supported maintenance/restart procedures, never the local kill-zone recipe.
   Verify all affected processes after boot. Current managed RoF2 assets supply
   Chapterhouse and waypoint models; no new client asset/DLL is authored here.
   Archive presence/map probes do not establish client-visible acceptance.

This runbook grants no production permission. Follow [QA](QA.md) before claiming
accepted gameplay/balance. The current AA-level wiki, finder and Build Lab must
be preserved; review the candidate wiki patch before separate publication.

## Pause and rollback

Disable new Vigil expeditions first, keeping matching schema/runtime/content for
recovery. Earned helmet claims and history remain accessible through Camil while
disabled. Retain campaign rows, receipts, items, dungeon runs, allocation
generations and corpses. A binary rollback removes the claim handler: record
pending entitlements and retain them for its restoration. Never recover grants
from an old player snapshot. Removing content is a separate guarded maintenance
operation using exact preimages after references/runs are accounted for. There
is deliberately no automatic drop-tables rollback that could erase earned state.

## Local test incidents, not production

The first isolated-schema rehearsal on shared local MariaDB 10.5.4 crashed its
parser in `negate_expression` / `MYSQLparse` while creating a routine containing
nested `IF NOT (NOT EXISTS ...)`. The development DB container restarted and
recovered; no PEQ writes were issued. Guards now use `IF (condition) IS NOT TRUE`.
Later rehearsals use a dedicated no-network 512-MiB MariaDB container with tmpfs
data, isolating parser failures from the shared development DB.

October23 continuation found Docker stopped and startup blocked by inaccessible
Windows Unix-socket reparse files. The verified socket-only LocalAppData
`Docker/run` and `docker-secrets-engine` directories were preserved with
`.chapterhouse-recovery-*` suffixes and recreated together. Docker then started
the local stack. No container data, settings or secrets were deleted. Rehearsal
readiness now requires the final daemon to own PID 1; old logs and temporary
initialization-server queries are insufficient after restart.
