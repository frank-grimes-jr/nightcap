# Reusable item upgrades

Release candidate; not deployed or accepted in game.

Artisan Veyra supplies a free, reusable Reforging Box in the East Commonlands
tunnel workshop beside the Epic Forgemaster. Keep it in a main inventory slot,
put four identical Polished items inside, and press Combine for one Exalted item
inside the same box. Four identical Exalted items become one Ascended item for
legacy loot or one Ascension item for Classic zone rewards. The owner selected
this container design on October 12, 2026.

Both tier systems are supported. There is no fee, random failure or tradeskill
requirement. Base/top-tier items, mixed inputs and customized instances reject
intact. Remove augments, dyes and ornaments first; evolving/scaling items are
excluded. Bags cannot nest inside the box. Four stackable units count as four
copies; the result is exactly one unit. Bound inputs keep the output bound.

The existing `#zoneforge` base-to-Polished recipe remains three copies; its
Polished and Exalted recipes require four to prevent a cheaper alternate path.
Sixteen Polished copies yield one top-tier item. Item strength, drop rates,
class access and combat caps are unchanged. Progression balance needs game QA.

## Implementation and verification

Box item 900620 uses native four-slot combine behavior. NPC/spawn/spawngroup
999820 occupy ecommons version 0 at X=-385, Y=-1818, Z=3.75. Consumption, output
and an audit receipt commit in one transaction after all inventory preimages
are validated. Uncertain commits quarantine the session. The NPC only supplies
the box; unintended hand-ins are returned normally. Legacy targets require the
expected ID band and same-family names; zone rewards use the explicit catalog.
Disabled or mismatched feature revisions reject combines.

Passed: compiled policy tests; actual inventory translation-unit tests covering
all transitions, binding, stacks, rejection, stale state, replay, SQL failures
and exceptions; 24 disposable MariaDB checks; six Perl quest assertions; all
three changed native object compilations; native floor/headroom/approach probes.
Independent review's stackable quantity finding was corrected and covered by a
target with MaxCharges=20 that must still yield one unit. See `mariadb.json`,
`inventory-native.json`, `native-build.json` and `geometry.json`. Object
compilation does not constitute a linked binary or real client acceptance.

```powershell
python -m unittest discover -s tools/tests -p test_item_upgrade_policy.py
python tools/tests/test_advanced_loot_inventory.py --root . --output docs/releases/item-upgrades-20261012/inventory-native.json
python tools/tests/rehearse_item_upgrades.py --release docs/releases/item-upgrades-20261012
perl tools/tests/test_reforging_box.pl
```

## Activation and rollback

1. Promote through dev and test with [exact client QA](QA.md). Main/production
   promotion requires owner sign-off under AGENTS.md.
2. Inspect the target supervisor/deployment layout, take a fresh backup, and
   confirm IDs 900620/999820 and template definitions. Installation deliberately
   refuses collisions and repeated application.
3. During controlled downtime, apply `install.sql`. It adds box/NPC/state/receipts
   at revision 2026101201, disabled. Build/link and install the matching native
   zone and `quests/ecommons/999820.pl`. Regenerate shared item memory, then
   start the matched runtime. No rule catalog changes are included.
4. Verify hashes, cached box, NPC spawn and disabled state. Apply `activate.sql`
   and require its returned row to be `(1,2026101201,1)`. Verify both container
   and zone-forge costs and record deployment evidence. Production child exits
   restart the entire runtime; do not kill one zone as an improvised refresh.
5. `rollback.sql` disables new box combines while retaining boxes, earned outputs
   and receipts. Never restore old player inventory. This SQL does not revert
   the native zone-forge price change; that needs a matched earlier binary.

All install/build/database rehearsal resources were isolated and local. No
running game binary, live database or production server was changed.
