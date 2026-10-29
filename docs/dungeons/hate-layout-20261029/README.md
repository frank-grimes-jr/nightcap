# Plane of Hate layout successor — October 29 deployed for live testing

The owner requested THJ's ground-accessible Hate layout and explicitly chose
“New layout, preserve Nightcap encounters and loot.” THJ's public teleport guide
identifies `hateplaneb` (zone186). The owner then approved main and paired
server/client/wiki delivery before manual QA. Main PR362 (`8b23d739`) and OVH
activation are complete: new Keeper runs now place the existing Nightcap population
on the ground level of186; original 76 runs remain usable. Signed client2026102901
and wiki20261029-hate-layout-v1 are published. Admissions are open. **Owner
rendering, pathing, practical difficulty and complete-run acceptance remain open.**
Exact receipts and recovery: [release/README.md](release/README.md).

## Behavior and preservation

The East Commonlands Keeper creates new Raid/Grind runs in186. A character's
unexpired 76 allocation, or a joined leader's76 allocation, continues in76.
Ambiguous or failed allocation queries fail closed. Creation rechecks the other
zone while holding the existing allocation transaction lock. An expired76 run
cannot silently create another76 run. Public spell travel and unmanaged zones
retain their existing routes and content.

Both layouts use dungeon index19, tasks9738/9739, the same four objective
NPC/spawn identities and the same six final reward IDs. Journal activities
accept both zones; history disambiguates both layouts before removing an active
task. No earned run, inventory, receipt, corpse or character record is migrated.

The176 private points comprise175 original eligible spawn groups plus the
entrance Keeper. Original NPC IDs, spawn entries/chances, loot tables, HP/damage,
spell sets, respawn intervals and randomized respawn variance are retained.
Managed186 uses76's global-loot filters, equipment hunt family/sources and experience
multiplier (1.0; public186 has1.13). The integrated October29 augment candidate
uses zone186's Blackspire Prism family on regular combat mobs at0.5%; original76
retains Spiteglass Prism. See ../../releases/zone-augments-20261029/README.md. Existing Raid modifiers/unlock gates and
Grind respawns still apply. Pure invisible ambience and the old waypoint marker
are omitted. Stock186 population and later-era epic scripts are excluded from
managed runs; public186 scripts retain their original behavior.

The Book of Souls remains item28016, with the existing count and respawn policy;
only its managed186 position changes. The native ground-spawn override does not
change either public zone's item record.47 patrols use ground-level back-and-forth
routes with10-second endpoint pauses. Their spatial pacing is newly designed;
unchanged combat stats do not prove identical pull difficulty.

## Placement and client pairing

Coordinates below use in-game `/loc` order, Y,X,Z. All four bosses and the book
have complete native navigation routes from the zone arrival; no route uses a
teleport edge or an upper floor. Terrain probes also check ground/headroom.

| Actor | /loc |
| --- | --- |
| Arrival | 656,-393,2 |
| Keeper | 656,-409,2 |
| Magi P'Tasa | 365.2,-361.9,3 |
| Hand of the Maestro | -43,-93,3 |
| Maestro of Rancor | -386,-173,3 |
| Innoruuk | -765,-451,3 |
| Book of Souls | 313,-673,3 |

`population.json` owns the reviewed placement; `navigation.json` records the
native map and Recast/Detour route evidence. `public-source.json`, `public-aux.json`,
`spawn-policy.json` and `environment-policy.json` contain only bounded public
content reads, not player data. No traps or zone points exist in these zones.
The78 successor doors have no keys, locks, destination, trigger or LDoN action.

The deployed pair contains the binaries, additive SQL, two `hateplaneb` Lua scripts and
signed client assets. The client needs `hateplaneb.s3d`, `hateplaneb_obj.s3d`,
`hateplaneb_chr.s3d`, `hateplane_chr.s3d` and the generated `hateplaneb_chr.txt`.
It also carries `hateplane.s3d` and `hateplane_obj.s3d` for retained old runs;
these two pins match the previously validated October28 local entry repair.
`tools/hate_client.py` validates source hashes and imports13 classic actors
missing from the successor archive. `client-validation.json` records actual
generated hashes; it does not establish visible RoF2 rendering acceptance.
Preserve the latest deployed launcher/proxy/catalog and all other assets when
preparing a signed release. This includes the October28 archive delivery fix
without treating the owner's local entry acceptance as acceptance of the new layout.

## Implementation and checks

The clean Clang14/C++20 world, zone and shared_memory build passed, including
an actual final dependency recompile and zone relink. All138 source overlay
hashes match; see [native build evidence](native-build/README.md).
30 focused checks,19 wiki checks,14 Go packages,38 real terrain archive checks,
31 current public preflight checks and the85-predicate migration rehearsal pass.

- Catalog/compiler: `tools/hate_layout.py`, `tools/dungeon_catalog.py` and
  `common/dungeon_{catalog,policy,contract}.h`.
- Native behavior: `zone/dungeon_service.cpp`, `zone/zone.cpp`, `zone/loot.cpp`,
  `zone/zone_hunt.cpp`, `zone/exp.cpp`.
- Migration and failure/rollback rehearsal: [MIGRATION.md](MIGRATION.md).
- Focused tests: `test_hate_layout`, `test_hate_keeper`, `test_dungeon_journal`,
  `test_classic_dungeon_private`, `test_hate_quests`, `test_hate_client`,
  `test_client_zone_archives`, `test_dungeon_current_contract`,
  `test_hate_layout_migration` under `tools/tests`.
- Independent review found no remaining gameplay blocker after respawn variance,
  allocation/history scope, loot/hunt and quest-init corrections. Review is not
  deployment approval or in-game acceptance.

## Release and recovery boundary

The owner's October29 authorization was exercised for this paired release.
Preflight, stopped backup, additive installation, two quest replacements,
native activation, signed client publication and admission reopening are recorded
in `release/`. All51 schema and650 content predicates passed with102 saved-state
tables preserved. The initial disk guard safely stopped before service changes;
one inactive historical staging executable was losslessly archived and the
authenticated preflight resumed without rebuilding. This dated authorization
does not authorize future production changes. Prepare fresh target pairing,
free-space checks and backups before any later authorized maintenance.
`tools/hate_layout_preflight.py` emits read-only original spawn policy, reserved
range, roaming, disabled-spawn, trap, exit and zone-policy checks. Re-run them
against a fresh target before installation; do not treat today's snapshot as
permanent authority. Apply the
guarded additive SQL with gameplay stopped, install the paired native/quest/client
release, validate all runtime predicates, then reopen admissions. Never kill an
individual production zone: its supervisor restarts the entire game runtime.

Before any186 activity, the isolated inverse may be adapted only after fresh
exact preimages and verification. After186 runs exist, retain the186-capable
native code and private rows until those runs/checkpoints/corpses are resolved.
Do not downgrade to code unable to recognize active186 runs, remove their patrols,
or restore an old player snapshot. A forward fix is the default recovery after
activity. Preserve prior signed client history and use a higher corrective
release number because clients can now observe2026102901.

## Required owner QA

1. Fully exit EQ and update through the paired launcher. At level46 or above,
   create a new Grind run at the Commonlands Keeper. Confirm arrival/return,
   correct actor models and all ground-level routes, including opening doors.
2. Visit the four objective locations, fight ordinary enemies, inspect normal
   drops and hunt drops, and collect the Book of Souls. Check LOS, collision,
   respawns and patrol pulls; report changes in practical difficulty.
3. Create a Raid: verify ordinary difficulty modifiers, the three-miniboss gate,
   Innoruuk unlock, personal checklist and exactly-once final reward.
4. Re-enter after zoning and a controlled instance unload. Verify new positions,
   dead Raid spawns, Grind timers, loot/corpses and journal persistence.
5. Use a retained76 run through Enter/Join/Status/Claim/Reset; confirm it finishes
   in its original layout and its earned history survives a later186 run.
6. Verify public/unmanaged behavior separately; do not interpret the managed
   layout as a change to public port spells or later-era quest availability.

References: [THJ teleport guide](https://thj.gileadgames.net/exploration-and-combat/teleport/),
[EQEmu zone list](https://docs.eqemu.dev/server/zones/zone-list/),
[THJ public quests](https://github.com/eqcodex/thj-quests/tree/main/hateplaneb).
