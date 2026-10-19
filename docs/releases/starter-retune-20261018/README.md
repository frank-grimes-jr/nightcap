# Starter bands — revised October18 candidate

**Current owner direction:** allow reductions to ordinary Normal starter gear.
The earlier preserve-Normal rule and35-AC entry-dungeon proposal are superseded.
Bronze must remain starter gear at every quality; dungeon/endgame rewards must
provide meaningful progression. Finished cultural crafted armor remains the
separate direct-Ascended exception.

**Status:** implemented offline proposal; not deployed, not encounter-balanced.
No live item/compiler/cache/binary/client changes. The proposed numbers below
are implementation candidates, not a claim of owner gameplay acceptance.

## Explicit scope and numbers

`docs/items/starter-retune-reference.json` captures209 explicit families /836
definitions across all four ordinary qualities. It includes the reviewed Cloth,
Leather, Bronze plate/brigandine sets, Small/Large variants, kilts, duplicate
Cloth Cap, Splinted Bronze Cloaks, the separately named Large Plate Girdle, and
Rusty/Bronze weapon identities. Names do not dynamically select items. The planner pins the complete209-ID allowlist and Rusty profiles independently of input captures; unlisted/cultural substitution is rejected. Zero
overlap with the944-item cultural armor catalog was verified.

| Chest | Normal | Polished | Exalted | Ascended |
|---|---:|---:|---:|---:|
| Bronze, all three sizes |6 AC|7 AC|8 AC|9 AC|
| Entry dungeon, level20 |12 AC|13 AC|not a dungeon quality|16 AC|
| Endgame dungeon, level50 |24 AC|27 AC|not a dungeon quality|32 AC|

Dungeon Normal chest budgets are12/16/20/24 AC at levels20/30/40/50. Other slots
have their own explicit entry budgets; this is not one flat armor value.
Dungeon rewards retain their existing three-quality system.

Bronze Long Sword becomes4/5/6/7 damage at32 delay; Bronze Knuckles2/3/4/5 at22.
Every reviewed starter weapon gains exactly one damage per quality. Normal
starter damage uses rounded75% of its captured base (Rusty50%), constrained so
even Ascended remains strictly below every comparable Normal dungeon ratio.
One-handed, two-handed and bow roles are separate. Delay never changes.

Starter armor Normal AC uses rounded6/17 of captured AC, at least1 for positive
armor, constrained by the entry reward budget; each quality adds1 AC. Starter
HP/mana/endurance base budgets are capped at3, primary stats/resists at1 and
advanced offense/regeneration bonuses at0. Positive pool/stat values use rounded
100/110/120/135% by quality. Negative drawbacks remain. Starter SpellDmg/HealAmt
are0/1/2/3 and heroic bonuses are zero. Effects/haste references are rejected.

Dungeon AC follows the slot budget plus4 per level band, then existing quality
scaling. One-handed dungeon damage gains1 at Normal before quality scaling.
Dungeon spell/heal budgets are4/6/8/10 across level bands; weapon endurance is
5/10/15/20. Current larger values are preserved. Bags, identities, wear/level
restrictions, delay and resale behavior remain unchanged.

`candidate.json` lists821 changed starter definitions and292 changed dungeon
definitions. Some Normal starter definitions are reduced; existing owned items
would display/use the changed definitions after an approved item-cache release.
No player inventory rewrite is proposed. This is not retroactively changing an
item's quality or converting existing Normal cultural armor into Ascended.

## What is proved and what remains

Eight tests verify all209 starter families against every comparable Normal dungeon
reward: strict AC or damage/delay ordering, one damage gained at each quality,
all size variants, unchanged identity/delay, bounded spell/heal/heroic stats,
immutable source inputs and rejection of catalog identity drift. Cultural and
dungeon regression suites remain separate. Native encounter outcomes are not
proved by these catalog comparisons.

This is an explicit starter cohort, not complete item classification. Fine Steel,
named/quest drops, bows, jewelry and other ordinary families still need reviewed
bands. Do not infer a complete game hierarchy, or change unlisted gear by name.
Armor weight, procs, multiclass abilities, AAs, pets, sustain and acquisition cost
also matter. The combined legal-build encounter sweep at levels20/30/40/50 and
owner in-game acceptance remain gates before promoting numeric balance.

## Deployment boundary and QA

No production SQL is emitted by this proposal. Before activation, capture full
item preimages (all columns, not only these comparison fields), add a guarded
forward/inverse migration for exactly the approved definition/field set, rehearse
it with stale-data rejection and preserve the cultural recipe exception. Rebuild
the item cache with the current paired runtime and use a supported full-runtime
restart. No client ABI/download change is expected. Do not kill a single zone.

QA must inspect Normal/Polished/Exalted/Ascended Bronze Breastplates in all three
sizes, Splinted Bronze Cloaks and Large Plate Girdle; all must match the proposed
catalog. Compare entry and endgame dungeon chest values, and Bronze Knuckles/
Long Sword damage and unchanged delay. Check existing owned instances after
reconnect, equipped bonuses, reforging outcomes and cultural-crafted Ascended
armor exclusion. Measure melee/tank/caster/healer/pet builds for incoming burst,
survival, kill time, healing efficiency and mana recovery. Report gear, legal AA
pool/spend and multiclass combinations; catalog tests do not replace these checks.

Rollback restores item definitions with fresh guards and matching cache reload,
not old player snapshots. Existing inventories, quality identity and earned
progression records must stay intact.

Reproduce from repository root:

```powershell
python -B tools/starter_retune.py --output artifacts/cultural-armor/starter-retune-report.json
python -B -m unittest tools.tests.test_starter_retune tools.tests.test_dungeon_catalog tools.tests.test_cultural_armor
```

Whole wiki review covers21 maintained guides and432 generated routes. Candidate
direction notices are updated; live Features/home, commands and catalog numbers
remain unchanged. Publication is not claimed.
