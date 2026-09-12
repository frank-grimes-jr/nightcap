# Calculator evidence and remaining work

Date: 2026-09-12
Status: foundational calculations and input fixtures verified; encounter model incomplete

## Proven so far

- `GetExtraSpellAmt` port: 2,792 boundary/random differential cases match the
  extracted actual C++ function. `spell-formula-oracle.json` records source hashes.
- 94 Python tests cover caps, timing boundaries, duration splitting, integer
  truncation, snapshot/query gates, and gear legality/assignment. Assignment results
  match exhaustive enumeration on 50 small random matrices, including cases where
  a greedy per-slot choice is wrong.
- RoF2/SoD base/max HP and mana agree with eight extracted engine functions in
  2,896 boundary/random cases (four outputs each; zero mismatches), recorded in
  `resource-formula-oracle.json`. This includes floating-point truncation and
  best held-class selection. Inputs are resolved stats and bonuses; this is not
  proof of complete inventory/AA/buff resolution. Ancillary heroic/stat helpers
  have unit coverage and source review, not this differential coverage.
- The seeded event engine now runs casts, heals, mana exhaustion/recovery, fear,
  periodic effects, regeneration, melee rounds, deaths, kills, and timeouts with
  resolved diagnostic inputs. It has analytically solvable timing tests.
- Hit/DI/mitigation arithmetic matches 5,000 native C++ cases. A 1,000-trial
  Nagafen melee control matches exact expected damage within 0.446 standard
  errors. The defender is artificial and spells are omitted; this is an event
  integration control, not a full boss fight. See `engine-validation.md`.
- The v2 snapshot (`classic-20260912-v2.json.gz`) freezes 5,797 item rows, three
  bosses, their actual spell lists and immediate parents, 1,373 spells including
  referenced item effects/recourses, Human creation data, base data, skill caps,
  rules, and 124,161 drop provenance records. Missing references fail validation.
  The original fixture stays immutable for existing resource and melee proofs.
- Stored spell formulas/durations match 12,224 native cases; ordinary resists
  match all 201 rolls for 1,500 resolved inputs (301,500 rolls). Unsupported
  formulas remain explicit. Spell application, fear/CHA, focus/AA resist checks,
  physical/PvP paths, root/charm breaks, and AI integration are outside that proof.
  See `spell-resolution.md` for captured boss dependencies and remaining limits.
- `candidate-builds.json` contains complete 20-slot shield loadouts for WAR/CLR/WIZ,
  WAR/CLR/MNK, and MAG/NEC/SHM across Base/Polished/Exalted/Ascended. The declared
  additive score is globally optimized over each captured tier pool with lore
  constraints. Server-side equipment legality is checked; client submission parity
  remains a separate existing multiclass issue.

These are candidate loadouts, not certified full BiS. The search excludes quest,
merchant, global-loot, conditional/flagged content, epics, augments, and gear above
recommended level. Haste/procs/focus/AA/buff interactions are not in the objective.

## Findings that affect the next step

- Full candidate Ascended sets supply 400 spell damage/healing before caps. The
  existing 250 cap clips them; a cap above 400 supplies no additional benefit to
  these sets without another stat source. At 400 effective bonus, an eligible
  direct spell has 5x the base-only contribution, versus 3.5x at 250. This is not
  a prediction of final damage, encounter difficulty, or a recommendation to raise it.
- DoT/HoT bonuses split over duration. For base 100/tick, bonus 250 and ten ticks,
  the isolated item contribution yields 125/tick, not 350/tick. Crit/focus/other
  effects still need separate handling. Long-lived self HoTs require particular
  attention because the duration-splitting code calls `CalcBuffDuration`.
- The pool represents this server's current Classic-zone data. It includes later
  items and Fabled GrimFeather (NPC 13118), whose North Karana spawn 5809 has a 5%
  entry, no expansion/flag gate, and no disabled-spawn row. Parent loot gates were
  checked as well. Do not silently classify that loot as historical Classic or
  arbitrarily exclude an enabled source to make test builds weaker.
- Vox has a 5,000 mana pool, inherited Cleric spell list, cold resistance 1,000,
  and fire resistance 70. Nagafen has fire resistance 425 and cold resistance 70.
  An HP-only dummy model or identical nuke rotation would miss material mechanics.

## Next implementation requirements (not completed)

1. Extend acquisition coverage and optimize against functional build objectives
   before certifying full BiS. Resolve referenced item/spell/AA effects explicitly.
2. Produce character HP/mana, capped stats, mitigation, hit/avoidance, melee damage,
   regeneration, haste, and resists from actual formulas and gear/buff/AA inputs.
   The active build uses SoD base data for RoF2; do not use the older class-factor
   HP equation. Some heroic effects still inspect the base class, which must be
   represented faithfully rather than assuming intended future multiclass parity.
   HP/mana arithmetic is now verified; connecting it to complete legal character
   creation, inventory effects, and buff/AA inputs remains pending. RoF2 creation
   allocations come from `char_create_point_allocations` / combination data loaded
   in `world/worlddb.cpp`, so do not substitute the legacy hardcoded race table.
3. Prefer actual engine calculations or C++ differential oracles. Existing
   `zone/cli/tests/cli_npc_handins.cpp` demonstrates a mock `Client()` and real
   NPC construction; `zone/tune.cpp` has native melee sampling. A native test
   command must run against an isolated content/database copy, since zone boot
   and existing CLI tests can write state. Do not run write-capable zone tests
   against the live gameplay database.
4. Implement seeded event simulation: enemy swings, spell casting, Vox healing,
   breath/fear, resists, player rotations, healing thresholds, resource exhaustion,
   pets/DoTs/control, deaths, kills, and timeouts. Include buffs and explicit AA
   budgets, including powerful combinations. Test analytically solvable fixtures
   and differential-check core engine math before interpreting real encounter runs.
5. Run Vox/Nagafen (plus controls) at multiple gear stages, caps, and HP settings;
   report distributions and sensitivity to remaining assumptions. Select balance
   changes only from these results. Produce focused residual in-game QA.
6. Complete baseline runtime reload/QA and branch promotions within the existing
   working agreement, then continue the remaining backlog. The overall goal remains
   active; none of these pending requirements is satisfied by the checks above.

The initial mirrored RoF2 capture preserves 17 existing mixed-indent warnings in
`rof2.cpp`; those were not reformatted to manufacture a clean source hash match.
No C++ gameplay implementation changed in the calculator slice.
