# Existing healing/mana focus category leak

Confirmed on the current shipping zone, not introduced by the stock-item candidate.

| Level-20 PAL/WAR, Light Healing, no AAs | Selected healing focus | Selected mana focus | Mana cost |
|---|---:|---:|---:|
| Neither | 0% | 0% | 28 |
| Improved Healing I only | 20% | 0% | 28 |
| Mana Preservation I only | 0% | 10% | 26 |
| Both | 20% | **20%** | **23** |

The same character, spell, gear and production rules are used in all four cases.
Direct native calls also return 20 for healing-as-mana and 10 for mana-as-healing.
The category-presence flag prevents cross-category selection until that category
exists somewhere in the loadout. This explains why examining one item in isolation
misses the interaction.

`Client::CalcFocusEffect` in `server-mods/code/zone/spell_effects.cpp` groups
`ImprovedHeal` and `ReduceManaCost`, then accepts either requested focus type.
The proposed correction skips a slot unless its actual effect matches the requested
category. The surrounding limits, random/static selection, strongest-source logic,
AA ranks, spell amounts and item definitions remain unchanged. A multi-effect focus
spell still evaluates each matching slot.

The small proposal is saved in
`E:/EQ_Local_Dev/artifacts/classic-focus-coverage-20261120/proposed-focus-category.patch`.
It has **not** been applied. Independent source review found the approach sound.
Required validation before any deployment: reproduce the current shipping binary;
compile the full changed translation unit; native neither/heal-only/mana-only/both
controls; mixed item/augment/worn sources; a focus spell containing both effects;
modern and Classic focus modes; rerun legal progression and full endgame pressure
comparisons. Then stage the corrected binary together with the item migration.

This is a global engine correction. It would preserve healing strength and Greater
Healing but remove unintended mana savings from existing combinations, including
items outside the proposed 19 stock families. The owner scope decision is pending.
Do not describe the 10% stock spell definition as independently enforced by the
current engine, and do not publish the prepared guide or deploy the gear candidate
as though this gate were resolved.

Evidence: `focus-controls-input.json`, `focus-controls-results.json`, the isolated
diagnostic source and build pins in this directory. These are native method tests,
not player acceptance or a claim that a full raid encounter was simulated.
