# Visible equipment ornaments

November 21, 2026 feature candidate. The East Commonlands Ornament Artisan takes one unequipped donor and returns a statless appearance augment to inventory. Players can also loot a design from any eligible NPC corpse. The independent roll is 1% with equal weight per active catalog definition across all zones, levels and expansions. Pets, restored corpses, noncombat bodies and the artisan do not roll. Existing ordinary loot, raid rewards and zone hunt rolls retain their own probabilities.

## Equipment and custody

RoF2 uses type 21 for head, arms, wrists, hands, chest, legs and feet. Primary and secondary items, shields and ranged bows use type 20. Native socket checks and RoF2 packets project the same socket, including on already-owned equipment. A matching socket takes priority, followed by an empty socket. On a full layout with a misclassified cosmetic socket, the artisan design uses that position. Stat sockets and their installed augments retain their indices. Both wrists accept compatible ornaments. RoF2 displays one wrist material from the first wrist slot.

The donor supplies the visual definition, icon and fit. New item records start from database defaults and an explicit visual field list. Their price, stats, damage, spells and effects are empty. Augmenting a host retains its weapon skill, damage, delay, proc and bonuses. Armor keeps its original material, elite material and built-in color in the design. Existing character armor tint still applies. Slot and weapon-family restrictions apply during insertion, and shields and bows each require their own designs.

Trade the artisan one item with no coin and a free place in the pack. A successful hand-in consumes the donor permanently, including charges. Existing augments, mold overrides, player dye, evolving or scaling items, custom instance metadata, multiple items and stacks larger than one cause a return. The exchange locks the saved inventory preimage, consumes the trade row, inserts the reward and records a claim in one transaction. An ambiguous commit requires reload from saved inventory. The quest fallback returns hand-ins on an older worker.

## Catalog and verification

The November 21 local PEQ export has 308,940 item definitions. All 138,647 visible hosts have room for a compatible socket. 137,281 equipment definitions have a donor appearance the local asset scan could resolve. The plan produces 14,691 statless designs across gear, existing ornaments, transformation molds and the client armor tags. Qualities sharing appearance, icon and fit use one design. The 1,366 other host rows still receive sockets. Their donor models are absent, placeholders or incompatible with the audited client.

Of the 3,092 stock ornament and mold rows examined, 1,221 supply a usable design directly. The other 1,871 lack a usable mapping. For example, the Old Heroâ€™s Forge Cloth Chest Ornament has a placeholder ID file and a zero armor model. The armor tag catalog independently supplies 556 slot models with verified attachment meshes. Another 147 tag IDs reference meshes absent from the scanned archives. The named PEQ row alone does not establish which tag belongs to it. Generic scene objects and individual armor mesh components have no independent wearable slot. The local counts describe this client and export. Rebuild the catalog from the destination database before activation.

Run the following from the feature checkout. Export the query as raw, tab-separated UTF-8 with column headers. Use a maintenance window for content changes.

```powershell
python tools/ornament_catalog.py --query
python tools/ornament_catalog.py --client PATH_TO_ROF2 --items PATH_TO_TSV --output PATH_TO_PLAN_SQL
python docs/items/visible-ornaments/rehearse.py --sql PATH_TO_PLAN_SQL
python docs/items/visible-ornaments/rehearse.py --native
python -X utf8 tools/tests/test_visible_ornaments.py
python -X utf8 tools/tests/test_classic_socket_stacking.py
python -X utf8 tools/tests/test_augment_ornament_native.py
python -X utf8 tools/tests/test_zone_hunt_native.py
python -X utf8 tools/tests/test_advanced_loot_inventory.py --root . --output PATH_TO_TEST_RESULTS_JSON
```

The plan checks an export fingerprint, assigns stable RoF2-linkable IDs through a persisted visual key and rejects occupied IDs or ambiguous spawn anchors. Re-running it refreshes the active drop and donor mappings while preserving existing definitions for inventory. Preserve the design registry across updates.

For an authorized release, back up content, build the matching world and zone binaries from the integrated source, pair the generated item definitions with a refreshed shared item cache and install the numbered quest in ecommons. Reboot the game runtime through the supported supervisor to load the new binaries, cache, spawns and world pool. The protected client requires no edit. Source changes, local object builds and disposable SQL rehearsals do not establish production deployment or player acceptance.

To suspend acquisition, clear the active flag on the design registry, disable the dedicated artisan spawn and reload the affected zones through the supported maintenance path. Preserve definition and registry rows for held and socketed ornaments. Re-enable using the reviewed plan and spawn. Coordinate any binary rollback with saved cosmetic custody.

## In-game QA

1. At the East Commonlands tunnel find the Ornament Artisan beside the Epic Forgemaster. Hail, leave pack space and hand in a spare Fine Steel Long Sword. Verify one donor disappears, one type 20 ornament arrives, and its inspection lists no stats or effects.
2. Socket it in a compatible one-handed slashing weapon. Compare damage, delay, skill, procs, worn stats and an existing stat augment before and after. Verify your weapon and its appearance on a second client. Try it on a shield and a bow. Both should reject it.
3. Repeat with a shield and a bow. Inspect the shield in the off hand and fire the bow. Check the held bow during the draw animation, the unchanged arrow, and the original damage and range.
4. Repeat with armor for each visible slot, including a robe, a tinted stock chest, both wrists and a client-tagged Heroâ€™s Forge piece. Change zones, log out to character select, log back in and inspect from another character. Distill or destroy the ornament and confirm the host's original appearance returns.
5. Hand in two items, an augmented item, coin, a stack or a donor with no pack space. Verify the originals, attached augments and money come back. Check an ordinary quest NPC still takes its own hand-ins.
6. In East Commonlands and a private dungeon, inspect the server-authorized QA corpse rolls and take a world ornament through Advanced Loot. Each qualified death gets at most one roll against the same pool. Confirm ordinary loot is still present when its own roll succeeds. A short dry streak is expected at 1%.

Owner visual QA, linked release binaries and activation remain open.
