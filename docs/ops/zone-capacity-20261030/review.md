# Independent timer-safety review — October 30, 2026

Reviewed source: feature/zone-capacity-20261030 based on origin/main
989a464c345fb2c3799f5b769090442039a1d35e. The production quest inspection was
read-only. `quest-review.json` records capture time, SHA-256 fingerprints and
bounded timer/dependency excerpts for 269 installed scripts in the seven initially
proposed zones, three global dispatcher candidates and five initialization/plugin
dependencies. These are inspected files, not a new blanket claim that the local
native overlay exactly matches the deployed executable.

## Accepted narrow timer policy

| Zone, public version 0 | Empty retention | Reason |
|---|---:|---|
| ecommons | 300 seconds | Native services persist their own data. Market/chatter helpers are ambience; the longer Sergeant Ragus 600-second callback only shouts. |
| rivervale | 300 seconds | Inspected long callbacks are dialogue, emotes and signals for dialogue, not rewards or encounter stages. |
| feerrott | 600 seconds | Provides margin beyond corrupted spirit's 300-second depop and the short druid trap callback chain. |
| commons | 900 seconds | Exceeds Duggin Scumber's 600-second finite depop with five minutes of margin. |
| eastkarana | 1800 seconds | Exceeds Vance Bearstalker's 1200-second depop and Althele's 90/120/600-second epic stages/cleanup. |

This policy is appropriate for ordinary empty-zone travel, subject to the
activation/state-preservation gates and in-game QA. It reduces accumulation
without claiming unlimited capacity or exact preservation of ambient chatter
phase. No quest script is changed. The migration must restrict exact row IDs,
short names, version 0 and the captured one-hour preimage; preserve all other
row fields and versions.

Preserve Misty Thicket: its `script_init.lua` unconditionally loads
`encounters/Misty.lua`, a seasonal encounter with volatile phase state and
registered spawn/combat/timer handlers. A direct top-level-only scan would miss
this. No claim was established that the encounter's NPC/content gates make it
inactive, so the safe policy leaves its one-hour timer untouched.

Preserve Highpass Hold: Stanos Herkanor's ten-minute depop is explicitly paused
in combat. A fifteen-minute wall-clock allowance cannot prove a paused timer
finishes before unload. Preserve public Fear, Sky and other dungeons and the
special long timers. Fear's Cazic Thule spawn callback schedules a public
spawn-condition reset after five seconds. Sky has long timed services and
encounters. A blanket one-hour-row cap is not justified by this review.

## Why the mixed finite windows can finish while empty

In the local full-source `zone/main.cpp:598–622`, a loaded zone runs
`entity_list.MobProcess()` and then independently runs
`quest_manager.Process()` on the quest timer tick. `zone/questmgr.cpp:84–123`
dispatches enabled quest timers and queued NPC signals without a player-count
gate. `zone/entity.cpp:507–525` suppresses ordinary NPC AI when idle but still
checks `GetDepop()`. Therefore a timer callback can mark an NPC for depop while
the zone is idle, and the entity loop removes it before the later zone unload.
Longer policy durations exceed the reviewed finite callbacks; they do not bound
paused timers, which is why Highpass is excluded.

Quest timers themselves are not serialized by saved-state code. Restoring a
dynamic public NPC runs `EntityList::AddNPC` and its `EVENT_SPAWN` callback
(`entity.cpp:688`). An unfinished finite depop can restart on a reload. The
mixed durations avoid shortening normal finite windows in the included zones;
they are not a general solution for arbitrary future scripts or indefinite
events. Future content imports or quest changes require revisiting the allowlist.

## Persistence and refresh requirements

- `server-mods/code/zone/zone.cpp:1593–1597` unloads an expired dynamic zone only
  when `numclients == 0`; static zones bypass this path.
- `zone.cpp:879–880` saves loaded zone state before normal shutdown. Keep
  `Zone:StateSavingOnShutdown=true` and
  `Zone:KillProcessOnDynamicShutdown=false`; line 940 otherwise exits the worker,
  which restarts the entire production runtime under the current supervisor.
- `zone_save_state.cpp:699–818` records public spawn/NPC state, loot identity,
  buffs/variables and NPC corpses. Public death deadlines persist separately via
  `spawn2.cpp:470–525`. Managed runs use transactional checkpoints and durable
  death/corpse records in `dungeon_service.cpp:892–959`; dungeon timers are not
  changed by this patch.
- Public saved-state replacement is delete then insert without a transaction or
  successful-save gate (`zone_save_state.cpp:799–818`). Adequate disk space and a
  verified fresh backup are mandatory before increasing unload frequency. Do
  not erase saved states or restore old player snapshots as rollout shortcuts.
- `zonedb.cpp:2686` reads the process-local `ZoneStore` row. `zone.cpp:1840`
  adopts it at boot; `ResetShutdownTimer` at 1869 reuses the old duration. Local
  `worldserver.cpp:4690` ZoneData reload refreshes cache/config but does not reset
  the timer and is zone-dependent. SQL plus natural zone unload alone cannot
  prove every idle worker picked up the new values. A controlled whole-game
  recreation for the worker count and data policy provides clean cache activation.

## Dispatch and global scope

All seven candidate zone directories were recursively fingerprinted, including
the Misty encounter. Versioned directories would appear in that inventory; no
numeric version-specific candidate scripts were found. File existence and a
timer scan alone do not establish which NPC variant is active: native resolution
can choose versioned/local/global ID, name, name_ID and default scripts, with Lua
preferred over Perl. This review conservatively treats all discovered candidate
quest timers as potentially relevant rather than relying on an inactive-content
assumption.

The inspected `global/global_npc.lua` spawn hook conditionally applies Halloween
cosmetic race/size/texture/gender changes. It has no timer or encounter progression;
its additional zone-specific set is PoK/Shadow Haven/Bazaar/Guild Lobby. The
inspected global player Lua has no quest timer creation; its Perl counterpart is
not assumed active. Global script initialization imports extension modules and
does not load a shared encounter in the captured file. Tunnel scheduling helpers
were checked separately: their timers are social ambience, and the market pulse
returns immediately with no clients. No global blocker for the final five rows
was identified; this is not an exhaustive audit of every quest/plugin in PEQ.

## Verification boundary

This review establishes source reasoning and captured installed quest evidence,
not deployed behavior or owner acceptance. Before promotion, test the exact
preimage/inverse guards, exclusions, original 12-worker failure replay and new
policy replay, plus repeated travel under a documented concurrency envelope.
After authorized activation, observe an included zone unload without worker PID
exit, re-enter it, and verify saved spawn/death/loot behavior and another player's
continuous session. Exercise Duggin and the East Karana finite quest windows in
dedicated QA if those content paths are currently eligible. Record any unrelated
content gate preventing that QA. No native build or client pairing change is
required for this configuration/data-only policy; preserve the complete current
runtime and signed client pair.

## Implementation review findings

Reviewed `tools/zone_capacity.py`, its focused tests and MariaDB rehearsal,
the read-only capture helper, the shared SQL generator/predicate and the one-line
Compose worker-count change. Eight focused unit tests passed in the final review
run; `git diff --check` passed in the initial review. The main task's isolated
MariaDB receipt records eight successful rehearsal groups across all618 captured
zone rows; this reviewer inspected that receipt but did not repeat its database
execution.

The implementation changes only the five selected shutdown fields. It rejects
missing/duplicate identity and unexpected timer preimages, and generated forward
and inverse SQL lock the scoped rows, guard exact complete row contents, reject
triggers/nontransactional tables and roll back on SQL exceptions. Other zone
rows and player/checkpoint state are outside its write set. The fixed pool of20
fits the existing31-port supervisor limit. There is no production mutation in
the planner or capture helper.

Review requests resolved before final candidate handoff:

1. The MariaDB rehearsal now rejects optimized Python (`not __debug__`) before
   any Docker operation. Its afterimage/inverse assertions cannot silently
   disappear under `python -O` while producing a successful receipt.
2. The new sustained-travel test retains13 other destinations and cycles eight
   destinations20times at two-minute intervals. The old one-hour policy fails
   with the same20workers; the mixed policy passes. This proves a benefit from
   retention independently of merely increasing the worker pool. The scenario
   is a documented finite concurrency/travel envelope, not an unlimited-capacity
   guarantee.

The new `activation_blockers()` rejects captures older than one hour or from the
future, requires the safe default rules and rejects unsafe overrides, checks
stopped/OOM services and cgroup OOM evidence, and applies resource budgets.
`--require-safe-resources` fails before producing a plan when these checks fail.
This is a necessary preflight, not complete rollout authorization. Activation
still requires current service/native identity verification and explicit
maintenance/backup/space gates. No activation tool or production result was
present in the reviewed scope; disk space currently blocks rollout. No remaining
blocking source finding was identified for this undeployed candidate.

## Integration review — current main into dev

Reviewed the four resolved documentation files against origin/dev and candidate
2a84b677 during the integration merge: `docs/README.md` and the Features,
Change Log and In development article JSON. The documentation index retains
the faction candidate link and adds the keyless live evidence and zoning
candidate links. Semantic HTML comparison against dev shows the faction and
augment preview text is preserved; keyless body fragments now use current-main
live wording, and zoning capacity remains explicitly not released. No production
operator is rerun by this documentation integration.

The resolution follow-up is closed: the superseded keyless source provenance
saying "tested content candidate, not deployed or published" was removed from
all three merged article `sources` lists, and the live evidence remains.
Inherited dev Hate candidate provenance also predates its live release; it was
noted as historical ledger review without silently promoting unrelated feature
candidates or widening this implementation review. Final semantic checks and
`git diff --check` passed. The integrating task reports19 wiki checks and a497-page
build passing; no publication or production activation is implied. No blocking
integration finding remains in the four reviewed resolutions.
