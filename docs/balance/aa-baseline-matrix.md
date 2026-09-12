# AA progression in encounter baselines

Date: 2026-09-12. Explicit owner requirement added during calculator development.
Status: required comparison matrix; AA-equipped fights have not been run yet.

The owner requested level-50 full-BiS comparisons at zero, 100, 200, 500, and all
AAs. Interpret the numeric stages as spent AA points, not unspent banked points
or a count of purchased ranks. The current native equipped-stat report is the
zero-AA control; it does not represent the other stages.

## Controlled comparison

For each representative class combination and boss, hold level, legal BiS gear,
buff/consumable policy, encounter mechanics, cap settings, and seeds constant.
Change only the AA allocation and the resulting legal action repertoire:

| Stage | Budget and interpretation |
|---|---|
| 0 | No purchased AAs; innate class abilities remain explicitly separate |
| 100 | Build-appropriate legal purchases totaling at most 100 points |
| 200 | Build-appropriate legal purchases totaling at most 200 points |
| 500 | Build-appropriate legal purchases totaling at most 500 points |
| All | All compatible ranks actually available at level 50 under active rules |

Record actual points spent, unused budget, ability/rank IDs, individual and
cumulative costs, prerequisites, level/expansion/race/class gates, and unlock
limitations. Do not grant higher-level ranks or assume every numeric budget is
spendable. If incompatible choices exist, model an explicit compatible allocation
instead of stacking mutually exclusive effects under the label "all."

Choose purchases for the build's encounter objective, with a documented progression
path. Check reasonable offense-versus-durability alternatives at material choice
points so one arbitrary allocation does not dictate a balance recommendation.
Record which bonuses still use base-class checks despite held-class AA access.

Passive AA bonuses and activated abilities both matter. Model activation policy,
cast/resource costs, duration, reuse timer, shared cooldowns, and ability conflicts.
Separate a prepared attempt with cooldowns ready from sustained/repeated encounter
performance. Include effects on pets, healing, mana efficiency, crits, mitigation,
avoidance, and death prevention where legal; unsupported effects must remain
visible and prevent certification of that scenario.

## Evidence and tuning standard

For Vox and Nagafen, report success/death/timeout rates, kill-time distributions,
damage/healing, mana exhaustion, minimum HP, cooldown use, and reasons for failure.
Cross-check AA eligibility and resolved bonuses with native engine paths. Keep
residual in-game QA explicit for behavior the calculator cannot establish.

Use the matrix to identify progression breakpoints and excessive combinations.
Do not tune solely around full AA power or require all AAs for every worthwhile
encounter. Zero AA does not imply every endgame boss must be immediately soloable;
earned AA progression should matter while supported earlier stages remain viable.
Spell/heal caps and NPC HP remain adjustable only after this combined evidence.
