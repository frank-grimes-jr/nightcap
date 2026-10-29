# Private Hate layout migration

Applied to production October29 under the owner's explicit paired-release
authorization. `release/open-receipt.json` verifies open admissions,51 schema and
650 content predicates, and102 saved-state tables. The176 private rows,47 grids and
255 waypoints are installed; no player snapshot was restored. Local inverse
evidence remains a rehearsal artifact, not a live rollback instruction.

`tools/hate_layout_migration.py` compiles the reviewed population into an additive
transaction: 176 `nightcap_dungeon_spawns` rows for zone186, 47 `grid` rows for
zone186 IDs9001–9047, and 255 corresponding `grid_entries`. It changes no public
spawns, NPC definitions, loot, tasks, zone definitions, or player/run state.
The 85 generated runtime predicates authenticate all installed rows, the exact
cardinality of each reserved scope, and the original175 public spawn policies
(including respawn variance, conditions, expansion flags and group identity).

For a future authorized release, stop admissions and the game through the supported
whole-runtime procedure, take the release backup, and capture fresh preimages
with `hate_layout_migration.capture(query)`. `desired(before)` rejects any occupied
reserved scope. Inspect public content, quest/map/client pairing and the native
release manifest separately. Pair the new native contract with `forward.sql`;
quest or rules reload alone does not activate the native layout. The SQL refuses
non-InnoDB tables, unexpected triggers, occupied reserved rows, and repeated
installation, and rolls back on a later statement failure.

Local evidence is in `rehearsal.json`. Reproduce with:

```text
python tools/hate_layout_migration.py
python -m unittest discover -s tools/tests -p test_hate_layout_migration.py -v
python tools/tests/rehearse_hate_layout.py
```

The rehearsal creates a new `nightcap_dungeon_rehearsal_<12 hex>` database in the
local `akk-stack-mariadb-1` container and retains it. Public schemas are cloned
without their rows; dungeon tables use the reviewed native schema with its foreign
keys because the local PEQ baseline predates dungeons. All player, inventory,
earned reward, run, corpse and timer fixtures are synthetic. The runner can only
address the disposable database name or `information_schema`. No production
connection is used and PEQ is never written.

`inverse-rehearsal.sql` is an exact inverse of the normalized rows observed in
that isolated database. It rejects changed rows before deleting anything and is
not a live recovery script. Once real successor runs, checkpoints or corpses
exist, keep their content and run state; disable new admissions or ship a paired
forward repair. Never restore old player snapshots or run the isolated inverse
against active successor runs. Existing classic76 content and earned state remain
present throughout both directions of the isolated rehearsal.

This evidence proves migration boundaries and preservation, not rendered actors,
navigation in a running zone, encounter balance, or owner gameplay acceptance.
