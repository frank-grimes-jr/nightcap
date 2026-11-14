# Heroic INT and WIS by cast origin

The original spell methods applied the direct heroic bonus to a client’s procs, combat-skill effects, item clicks and reflected damage. The excess was present even when the player had no gem cast in progress. Direct activated AAs already received the bonus. The correction preserves it for the original gem cast or activated AA while identifying the origin of each individual landing. [June 12 THJ combat notes](https://www.reddit.com/r/TheHeroesJourney/comments/1lamtdc/)

Each build ran 190 paired damage/heal observations across 38 cases and five heroic INT/WIS combinations. A synthetic level-50 caster had 40 effective Spell Damage and 60 effective Heal Amount in every row. For base damage/healing of 100, the zero-heroic controls produced 140 damage and 160 healing. Heroic INT and WIS change those magnitudes independently at 0.1% per point, with integer truncation. [THJ heroic-stat guide](https://github.com/P1xt/thj-wiki/blob/main/classes-and-abilities/heroic-stats.md)

| Origin or condition | Before, damage / healing | After, damage / healing |
|---|---:|---:|
| Memorized gem, 100 heroic INT / 200 heroic WIS | 154 / 192 | 154 / 192 |
| Activated AA, both timed and instant cases | 154 / 192 | 154 / 192 |
| Item click, proc, discipline, or combat skill effect | 154 / 192 | 140 / 160 |
| Same-ID proc nested inside the original delivery | 154 / 192 | 140 / 160 |
| Original cast after nested proc returns | 154 / 192 | 154 / 192 |
| Reflected damage at 50% effectiveness | 99 damage | 90 damage |
| DoT / HoT ticks on a duration-eight spell | 120 / 107 | 120 / 107 |
| Pet cast with no inherited caster critical bonus | 140 / 160 | 140 / 160 |
| Forced critical on the original gem cast | 308 / 384 | 308 / 384 |

The table uses positive damage magnitudes. JSON records native damage as negative and healing as positive. Every row uses 100 heroic INT and 200 heroic WIS except where the text identifies the zero-heroic control. On a 50% partial resist, a gem still dealt 99 after item damage and heroic INT. An item-mod opt-out held at 100 damage / 100 healing. Disabling the heroic-scaling rule produced 140 / 160.

## Test coverage

The driver compiles the native origin classifier, the target gate, the target-to-effect handoff, the ordinary CurrentHP handler and the full damage, reflected damage, healing, DoT and item-bonus methods. The probes vary (INT, WIS) independently as (0,0), (100,0), (0,200), (100,200) and (250,350). Every check calculates the expected magnitude from its own zero-heroic row. Baseline source was preserved before editing from dev at `7e40a79c162439bfc6a262d2363f17c66f93cad5`. Each receipt includes the compiled engine-source fingerprints.

- **Activation and re-entry.** Both AA controls use a rank mapped to the delivered spell. The driver checks that completed timed casts forward their AA rank and the instant Bard AA path passes its rank directly. A missing rank, a mismatched rank, an unmemorized spell, a mismatched caster or spell ID, and calls without an original cast lose the heroic bonus. Item clicks/procs retain ordinary item scaling.
- **Repeated and nested effects.** A group-style gem and AE-style AA each deliver to two distinct synthetic recipients within the same original targeting scope. Both recipients receive the same heroic delta. Nested probes include same/different spell IDs, a proc directly entering the target path, a scripted effect bypassing it, and the original cast resuming afterward.
- **Later delivery and ticks.** The fixture models a queue frame using the production raid delivery and heroic scope types. Gem and AA bolts and opening rain waves retain the original bonus. Mismatched bolt/target or rain/caster identity, later rain waves and periodic damage/heal ticks do not. The bolt test preserves the native proc flag used for impact aggro. Synthetic identities and controlled scheduler callbacks exercise these branches without a running zone.
- **Boundaries.** The fixture substitutes the spell table, AA rank lookup, memorized slot, stats, focus/critical controls, target enumeration, HP sink and scheduler. The spell dispatcher runs over synthetic CurrentHP effects of each sign. The paired healing probe on a reflected context is a defensive test. The reflected-damage row above is the gameplay-facing measurement. Nothing in this experiment records a player cast on a running server, network timing, visible logs or class-build acceptance.

## Reproduce

Run from the candidate checkout. The baseline argument verifies the original broad applicability. The candidate run verifies the corrected origin policy.

```powershell
python tools/tests/test_heroic_cast_origin.py --baseline --source <baseline-checkout>/server-mods/code --output before.json
python tools/tests/test_heroic_cast_origin.py --source <candidate-checkout>/server-mods/code --output after.json
python -m unittest discover -s tools/tests -p test_thj_spell_scaling.py
```

[Before](before.json) · [After](after.json) · [Measurement driver](../../../tools/tests/test_heroic_cast_origin.py) · [Fixture](../../../tools/tests/heroic_cast_origin_fixture.cpp) · [In-game QA](QA.md)
