# Native encounter runtime

Date: 2026-09-12. Status: native combat prototype and controls verified; full BiS,
AA activation policies, encounter distributions, and balance recommendations remain open.

The diagnostic now runs `Client::Process`, `NPC::Process`, and the native movement
manager under a controlled clock. It loads zone configuration, geometry, navigation,
and water maps. The player uses native auto-attack and normal spell-gem casting;
NPCs select their own attacks/spells. Spell completion, interruption, healing,
resists, fear, buffs, regeneration, and mana consumption use engine code.

## Isolation and clock

Only the separate diagnostic executable changes. A generated copy of `client.cpp`
attaches a packet sink to its existing mock constructor when runtime mode is
explicitly requested. It sets connected/finished-loading state and the RoF2 version
mask. The real network constructor and all other client methods remain intact.
Ordinary stat/direct-action probes retain the original mock state. No header layout
or production executable is changed.

GNU `--wrap` hooks `gettimeofday` and `time` only while runtime mode is active;
both use one virtual elapsed time and a fixed epoch. `Timer::SetCurrentTime` still
runs, and native movement receives the corresponding `frame_time`. The current
prototype pulses every **50 ms**; production's main loop requests 32 ms. Timestep
sensitivity is a remaining gate, not assumed immaterial. The existing explicit
native RNG seed remains unchanged.

Native death overrides record the terminal actor and omit corpse/XP/persistence
work. Native `CommonDamage` still performs divine-save/spell-on-death checks before
calling this override. Damage after a recorded terminal result is ignored. These
runs exercise terminal handling, not a separate proof of every death-save AA.

The isolated database/user/runtime and empty quest directories remain required.
Seven preflight refusals pass. After the encounter/replay runs, isolated `account`
and `character_data` still have zero rows. Runtime methods may write other test
tables; these are not read-only database tests. No live restart or tuning occurred.

## Controls and observed runs

The self-heal control starts at 2,000 ms with 2,961 HP / 4,707 mana. Native Superior
Healing finishes at 5,550 ms (3,500 ms cast plus the first 50 ms pulse past its
strict timer boundary), adds 2,100 HP, and spends 180 mana. A later native tick adds
9 HP / 6 mana. A 100-damage control removes exactly 100 HP, proving the fixture
does not retain login protection. These values agree with the earlier deterministic
direct-action sample. Persistent cooldowns expire at their second boundary while
ordinary timers fire strictly after theirs; both conventions are tested.

The initial boss attempt was invalid: the zone was not marked loaded, so the native
hate-list selector refused to return a target. Its debug report is retained as
`native-encounter-nagafen-debug.json`; it is **not a fight result**. The corrected
runner marks the isolated zone loaded after configuration/maps, and requires the
boss's native hate target to be the synthetic player. Corruption tests reject this
regression and reports with no boss attacks.

All following runs use seed 1729, level 50 WAR/CLR/WIZ, the existing Ascended
candidate, zero spent AA points including common free ranks, and no preparation
buffs or activated AAs. The controller casts Ice Comet against Nagafen,
Conflagration against Vox, and Superior Healing below 55% HP. It observes native
spell timers and an explicit raw spell-recovery delay, retries after 250 ms,
and turns toward its target when requesting a cast. It does not navigate back
after fear or optimize rotations. Spell acquisition/client UI parity is not proven.

| Prototype | Result | Time | Player HP / mana at end | Boss HP / mana at end |
|---|---|---:|---:|---:|
| Caster candidate vs Nagafen | NPC death | 251.05 s | 2,959 / 587 | terminal / 0 |
| Caster candidate vs Vox | Player death | 235.40 s | terminal / 175 | 15,258 / 39 |
| Weapon control vs Nagafen | NPC death | 241.40 s | 3,718 / 156 | terminal / 0 |

These are single-seed integration observations, **not balance estimates**. The
caster candidate holds Brain of Cazic-Thule, a non-weapon: native attacks correctly
refuse to swing it. The weapon control substitutes legal Sabertooth (Ascended),
608079, with captured drop provenance; it is not a BiS selection. Its two-minute
control produces 37 player melee events, 21 positive hits. The candidate also has
no item haste. This reinforces the need for combat-based gear selection.

Nagafen's long run casts Lava Breath 19 times and Roar 7 times. Vox casts frost
breath, roar, buffs/debuffs and heals, including three Complete Heals. Player fear
and movement occur in both caster long runs. All three two-minute controls and all
three terminal runs replay byte-for-byte with the same seed. A shared seed does
not pair random draws across gear changes, so the weapon timing difference is not
a controlled estimate of its benefit. 120 Python tests pass. Re-running all 24
earlier AA scenarios and all 491,520 direct-spell samples with the new binary gives
byte-identical results (`native-runtime-regression-check.json`).

## Evidence and next gates

- `native-runtime-{inputs,control,verification,build-manifest,guard-check}.json`:
  clock/cast/damage control and pinned binary (130 linked objects/archives).
- `native-map-manifest.json`: six copied map files and hashes. Spawn positions
  were read from PEQ on this date because the isolated clone has empty spawn tables;
  exact coordinates are preserved in encounter inputs.
- `native-encounter-*-inputs.json`, `*-prototype.json`, `*-control.json`, `*-check.json`:
  explicit inputs, actor/resource/position traces, spell attempts and packets.
- `native-encounter-*-long.json` and long input/check/replay files: terminal runs.
- `native-runtime-evidence-manifest.json`: hashes tying retained results to this run.

Before interpreting balance: finish full BiS/acquisition coverage; compare caster
items with weapon/haste/proc/focus alternatives; add preparation and legal activated
AA schedules across 0/100/200/500/all budgets and allocation policies; process any
additional actors/beacons required by those abilities; improve the controller and
client parity; test timestep and seed distributions; then run cap/HP sensitivity
sweeps. Fresh full-source/runtime parity and focused in-game QA remain separate
gates. Reused objects are pinned, not asserted to be a fresh engine build.
