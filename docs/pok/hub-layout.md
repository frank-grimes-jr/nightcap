# PoK arrival hub — deployed layout

Status: deployed September 15, 2026 for owner live QA. SQL placement and stale
custom NPC cache repair are verified; terrain and interaction acceptance remain
open. See [combined release](../releases/live-qa-20260915/README.md).

The guide stands north of the arrival point, with two rows of eight class
merchants flanking an open center aisle. Existing nearby NPC positions were
checked; exact ground, line of sight, and walking clearance still need in-game QA.
The current arrival point is x=-285, y=-148, z=-159. Deployed merchant rows are
x=-325 and x=-245, y=-204 through -92 in 16-unit steps. The guide is placed at
x=-285, y=-74. Deployed z=-158.875 uses the nearby native NPC ground height.

The stock plan preserves all 1,229 currently available unique scrolls, retains
item prices, and sorts each merchant by original class level then name. Shared
spells can appear at more than one appropriate class merchant. Each class fits
one merchant window; no II/cont. overflow NPC is needed for this inventory.

| Class | Stocked items | Merchant label |
|---|---:|---|
| Warrior | 4 | Warrior: Tomes |
| Cleric | 164 | Cleric: Spells |
| Paladin | 66 | Paladin: Spells |
| Ranger | 64 | Ranger: Spells |
| Shadow Knight | 66 | Shadow Knight: Spells |
| Druid | 236 | Druid: Spells |
| Monk | 5 | Monk: Tomes |
| Bard | 63 | Bard: Songs |
| Rogue | 4 | Rogue: Tomes |
| Shaman | 165 | Shaman: Spells |
| Necromancer | 176 | Necromancer: Spells |
| Wizard | 204 | Wizard: Spells |
| Magician | 181 | Magician: Spells |
| Enchanter | 275 | Enchanter: Spells |
| Beastlord | 71 | Beastlord: Spells |
| Berserker | 3 | Berserker: Tomes |

The migration occupies NPC/spawn-group range 997900-997915 and merchant IDs
99300-99315; these were empty before deployment. Future changes must respect them. The initially
considered 999260 range contains existing pet NPCs and must not be repurposed.
Existing merchants all use faction 0; migration must preserve source pricing
settings and item prices. The guide keeps its quest-bound name and gains the
Choose / View Classes label and Find-window visibility.

Five version-0 Forgemaster records were compared column by column; only their
IDs differ. The migration keeps 3266028 and removes 3266043, 3266047, 3266048, and
3266124, with all five preimages preserved for rollback.

Five utility services form a row at y=-232, z=-158.875, facing the hub: Bags at
x=-337, Epic Ascension at -311, Blessings at -285, Premium Blessings at -259, and
Waypoint Travel at -233. Existing quest-bound NPC names and pricing are retained.
These ground positions remain provisional until the in-game walk/LOS check.

Guarded forward/rollback SQL, transactional restock, and era preflight are now
implemented. Four planner/migration tests, 14 MariaDB controls, and PowerShell
preflight checks pass. See verification.md for preparation evidence and QA.md
for outstanding in-game acceptance. Do not replay the historical migration
as a substitute for checking current deployed state.

Regenerate the proposal from tools/:

    python pok_hub.py --audit ../docs/pok/hub-stock-audit.json --output ../docs/pok/hub-merchant-plan.json

Run the planner checks from tools/:

    python -m unittest discover -s tests -p test_pok_hub.py -v
