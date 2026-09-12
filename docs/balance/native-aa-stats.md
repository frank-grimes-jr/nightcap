# Native AA progression diagnostics

Date: 2026-09-12. Purchase allocations and equipped resource inputs verified;
full BiS and Vox/Nagafen fight outcomes remain incomplete.

The isolated engine accepted 7,868 individual purchases across 24 scenarios:
three level-50 Human agnostic Ascended candidate sets, each at zero spent points,
100/200/500-point budgets under two progression policies, and all purchasable
ranks. All 24 HP/mana pairs agree with the calculator using native resolved stats
and item/AA resource bonuses. Acquisition coverage and combat optimization do
not yet establish that these candidate sets are full BiS.

## Observed resources

These rows use the `balanced` candidate policy. Budgets are ceilings; actual spend
is shown because the next rank may exceed the remaining points. The same items,
creation allocation, skill policy, and no-active-buff policy apply within a profile.

| Build | AA budget | Actual spend | HP | Mana |
|---|---:|---:|---:|---:|
| WAR/CLR/WIZ | 0 | 0 | 5,922 | 4,707 |
| WAR/CLR/WIZ | 100 | 98 | 6,040 | 4,707 |
| WAR/CLR/WIZ | 200 | 198 | 6,217 | 4,707 |
| WAR/CLR/WIZ | 500 | 496 | 6,689 | 4,707 |
| WAR/CLR/WIZ | All purchasable | 13,738 | 13,458 | 5,908 |
| WAR/CLR/MNK | 0 | 0 | 5,562 | 4,099 |
| WAR/CLR/MNK | 100 | 94 | 5,672 | 4,099 |
| WAR/CLR/MNK | 200 | 200 | 6,116 | 4,099 |
| WAR/CLR/MNK | 500 | 498 | 6,282 | 4,099 |
| WAR/CLR/MNK | All purchasable | 13,261 | 13,196 | 5,206 |
| MAG/NEC/SHM | 0 | 0 | 4,457 | 5,832 |
| MAG/NEC/SHM | 100 | 100 | 4,545 | 5,832 |
| MAG/NEC/SHM | 200 | 199 | 4,545 | 5,832 |
| MAG/NEC/SHM | 500 | 494 | 5,033 | 5,832 |
| MAG/NEC/SHM | All purchasable | 13,288 | 7,557 | 6,938 |

Equal HP/mana does not mean equal power: ranks also affect crits, damage, defense,
pets, efficiency, and actions. WAR/CLR/WIZ at the 500 budget has AC sum/avoidance
690/522 (`balanced`, 496 spent) versus 728/570 (`durability_first`, 495 spent).
These are internal combat inputs, not displayed AC or survival probabilities.

## Purchase policy and native gates

Every stage includes the same zero-cost ranks purchasable without paid
prerequisites. In this data, the two Knowledge of Alaran Culture abilities each
carry SPA 69 base 10; native AA calculation adds 20 flat HP. The earlier empty-AA
report remains a separate control. Grant-only veteran/quest rewards are not
awarded. Free stance/activation ranks are owned but are not activated here.

`aa_allocations.py` defines ordered milestones, resolves preceding ranks and
prerequisites, and uses a purchase prefix at each budget. Higher budgets retain
earlier purchases; points remain unspent when the next planned rank is too costly.
`balanced` advances role-specific offense, sustain, then defense;
`durability_first` advances defense first. Both include early activated abilities.
These are candidate paths, not proven optimal spending. Activation casts,
durations, shared cooldowns, and conflicts still need encounter integration.

Native use/level eligibility exports 2,304 / 2,309 / 2,149 ranks respectively.
Purchase closures contain 2,248 / 2,230 / 2,095 purchased ranks across
441 / 398 / 425 abilities. Independent post-purchase native catalog checks
confirm no further purchasable rank remains. Grant-only and unmet prerequisite
ranks are excluded. WAR/CLR/WIZ rank 12892 needs ability 509; WAR/CLR/MNK's
Mastery of the Past chain needs ability 26. All exclusions are in the audit.

The native engine ignores prerequisites whose ability object does not exist.
The audit records these references rather than repairing data or inventing
requirements. Availability uses the copied expansion rules and player expansion
mask, not historical Classic AA assumptions. Quest-granted rewards remain a
separate acquisition/activation question before interpreting these as full builds.

## Skill correction and limits

The previous report incorrectly described its skills as maximum held-class
skills: it used base-class `MaxSkill` without caster specialization constraints.
The current harness takes maximum caps across held classes and calls native
specialization/cap rules against a valid initial state. Primary specialization
is Evocation for WAR/CLR/WIZ and Alteration for the others. Secondary Forte,
when owned, enables Alteration or Conjuration respectively at 100. Other
specializations remain at 50 before native cap-raising bonuses.

This is an explicit trained-skill ceiling. Natural skill-ups still call
base-class `MaxSkill`; held-class training and practical attainment require QA.
The correction raises MAG/NEC/SHM zero-spend AC sum/avoidance from the prior
base-skill control's 436/387 to 437/405. The separate 20 HP difference comes
from free AAs. Outputs include raw skills and the skill-model label.

The mock client, reused objects, and empty quest environment retain ADR 0005's
limits. Purchasing uses native eligibility and `SetAA`, deducts exact costs,
and calls `CalcBonuses`; full purchase UI, event-log, title, save, and quest side
effects are omitted. This is not a full login simulation. Client casting access,
base-class-only effects, active buffs, pets, weapons, and boss mechanics remain
gates before drawing balance conclusions.

## Evidence

- `native-aa-catalog.json`, `native-aa-inputs.json`, `aa-allocation-audit.json`:
  native eligibility/effects/prerequisites, exact loadouts/purchases, exclusions.
- `native-aa-stats.json`, `native-aa-verification.json`,
  `native-aa-resources-verification.json`: 24 outputs, exact ledgers/costs, and
  zero HP/mana mismatches.
- `native-aa-closure-check.json`: native completeness of all/free purchase sets.
- `native-aa-gate-check.json`: six illegal purchases rejected (overspend,
  duplicate, skipped rank, grant-only, missing prerequisite, unheld class).
- `native-aa-guard-check.json`: seven early configuration/runtime refusal checks.
- `native-aa-build-manifest.json`: executable and 129 reused object/archive hashes.
- `native-aa-runtime-manifest.json`: actual runtime/input/output/cache hashes,
  copied AA/expansion rules, and confirmation that player/account tables stay empty.

106 Python tests pass, including prerequisites, cycles, free/charged ranks,
budget nesting, ledger corruption, and AA-aware resource verification.
No live characters, rules, spell/heal caps, NPC HP, or running zones changed.
