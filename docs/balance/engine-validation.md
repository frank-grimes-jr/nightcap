# Encounter engine validation

Date: 2026-09-12
Status: event engine and isolated melee control verified; full encounter inputs incomplete

## What is executable

The command-line simulator accepts two explicitly resolved actor profiles. It
handles prioritized casts, cast time, cooldown/recovery, mana expenditure at cast
completion, failed/resisted casts, effective healing and overheal, fear interrupts
and immunity, periodic damage/healing, six-second regeneration, melee rounds,
deaths, kills, and timeouts. Seeds reproduce the full event trace. Reports separate
kill-time and death-time distributions rather than combining failed fights with
successful kill times.

The current `Melee` component is for NPC attacks. Player weapon damage tables,
weapon bonuses, passive procs, criticals, and riposte damage are not implemented.
Defender avoidance, mitigation AC, shielding, and damage modifiers are resolved
inputs, not values automatically calculated from a full character yet. Basic
main-hand and off-hand NPC rounds support the active live-rounds rule and the
legacy alternative. Pet flurries and rampage remain outside this component.

## Native arithmetic proof

`melee-formula-oracle.json` records 5,000 controlled-input comparisons against
three extracted functions from active `zone/attack.cpp`: `RollD20`,
`CheckHitChance`, and `MeleeMitigation`. All three outputs match in every case.
The inputs include automatic hit/avoid precedence, sitting, varied offense and
mitigation, level differences, and the optional level-difference damage rule.
The native oracle does not boot a zone or connect to the database.

This proves the specified math given resolved inputs. It does not verify
inventory/AA/buff resolution, casting AI, combat scheduling, or complete combat.
The exact native source hashes are stored with the comparison.

## Nagafen melee integration control

The fixture uses NPC 32040's captured 85–218 damage, level 55, 1.8-second delay,
STR 174, ATK 100, and Accuracy 100, with skill values from the frozen skill caps.
These produce offense 431 and accuracy 680. The NPC double-attack skill override
is 250, giving a 305/500 double-attack check under the active live-rounds rule.
There is no innate off-hand flag in its captured special abilities. Equipped
NPC loot weapons and item bonuses are excluded from this unbuffed control.

The defender has artificial fixed defenses and effectively unlimited HP. It
does not attack. This isolates melee timing and arithmetic; it is not a player,
a full BiS loadout, or a complete Nagafen encounter.

Across 1,000 seeded one-minute trials:

| Measurement | Exact expectation | Observed mean |
|---|---:|---:|
| Attack rounds | 34 | 34 scheduled |
| Swings | 54.74 | 54.733 |
| Total damage | 3,135.94 | 3,142.49 |

The damage difference is 0.446 sample standard errors. Every run reaches the
control duration, and inflicted damage matches the defender's HP loss. This
checks event integration against exact discrete hit/DI expectations. It does not
establish the server's actual encounter DPS against any equipped character.

Artifacts: `nagafen-melee-control.json` contains all results and the first trace;
`nagafen-melee-control-check.json` contains the analytical comparison and hashes.

## Important source observations for the next adapter

- The active `Combat:UseLiveCombatRounds` value is true. Treating the old NPC
  triple/quad logic as current would give the wrong swing distribution.
- `npc_types.attack_delay` is multiplied by 100 during loading. The stored
  `attack_speed=-17` field is not consumed by the active `SetAttackTimer` /
  `GetHaste` path reviewed here; do not apply an invented 17% haste adjustment.
- Base Warrior receives a -5 percentage modifier on the variable damage part;
  worn shielding reduces the additive minimum-damage part. These are separate.
- `Roll0(max)` excludes `max`. Hit rolls use a 50% tie breaker.
- `BuffProcess` applies a tick before decrementing the remaining counter and
  expires below zero. The content adapter must resolve actual tick counts and
  spell landing behavior; a database duration alone is not sufficient.
- Read-only PEQ creation check: Human/Warrior/Agnostic uses allocation 58. Base
  STR/STA/DEX/AGI/INT/WIS/CHA is 85/85/75/80/75/75/75; the default allocation adds
  25 STA. The Classic start-zone combination is zone 1 with expansions_req=0.
  Query: `SELECT * FROM char_create_combinations WHERE race=1 AND class=1 AND deity=396;`
  and the matching `char_create_point_allocations` row. No player data was read.

## Remaining fidelity work

1. Complete legal character/gear/effect/AA/buff inputs and combat-oriented BiS
   optimization. The existing candidate sets remain candidates.
2. Resolve player mitigation/avoidance, regeneration, spell resists, native spell
   bases, focus/critical effects, and complete weapon/pet combat.
3. Connect NPC spell-list inheritance, healing thresholds, cast chances/timers,
   breath, fear, resists, fleeing, summoning, and encounter scripts. Vox's Cleric
   parent list and mana pool must be included.
4. Validate content adapters against the engine, then run the requested full
   Vox/Nagafen builds and cap/HP/progression sweeps.

The event engine currently uses a documented conservative tie order (ticks,
melee, completed casts, decisions; enemy before player within an event type),
a fixed global tick phase, and 100ms decision polling. It does not model fizzle,
push interrupts, movement/pathing, adds, pets, procs, death-delay AAs, or revival.
These assumptions must be resolved or sensitivity-tested before balance decisions.
The full user objective remains active. No numerical balance recommendation,
live tuning, runtime restart, or branch promotion follows from these controls.
