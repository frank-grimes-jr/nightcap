# Classic augments and Prismatic scales

The three level-50 scales fit type-7 sockets in head, arms, either wrist, hands, chest, legs and feet. Combine the listed items in a standard Jeweler’s Kit (17912). Each recipe consumes the ingredients and produces one Normal scale with no failure roll. This is a Nightcap crafting route. The original dragon drops retain their existing loot rolls and quest uses.

| Scale | Ingredients | Normal / Polished / Exalted / Ascended specialty | Ascended ability |
|---|---|---|---|
| Healing | White Dragon Scales (11602) and Black Sapphire | 5 / 5 / 10 / 10 Healing Amount | Improved Healing IV |
| Magic | Red Dragon Scales (11622) and Fire Emerald | 5 / 5 / 10 / 10 Spell Damage | Improved Damage IV |
| Dodging | White Dragon Scales (11602) and Star Ruby | 2 / 3 / 3 / 5 damage shield | Improved Dodge I |

All three grant 60 / 90 / 120 / 120 HP and 5 / 8 / 10 / 10 AC. Each grants matching mana. This Classic adaptation limits baseline stats to AC, HP, mana and the listed specialty. The later-era worksheet also lists endurance, attributes and resists. The workbook provides three quality points. Nightcap uses four tiers, rounds the specialty points, and retains the top-tier focus unlock. The Reforging Box takes 3 / 4 / 4 identical plain inputs. An Ascended scale represents 48 crafted Normal scales through that path.

## Classic stock augments

Nine stock drop families have positive, ungated paths in Classic. Existing HP and mana rise to the next multiple of ten. Healing Amount and Spell Damage advance to multiples of five, with the Ascended bonus raised from 20 to 25. Zero fields stay zero, preserving each item's resource specialty. The 36 before/after definitions are in [stock.json](stock.json). Spawn gates exclude Refined Ore of Nimbleness and Icy Bone Chip of the Elements until expansion 6. Hunt, raid trophies and expedition rewards use separate catalogs.

## Validation and player checks

A legal level-50 human cleric set has eight compatible cloth hosts, including two wristbands. Eight Ascended Healing scales contribute 960 HP, 960 mana and 80 raw Healing Amount. Eight Magic scales give the same pools and 80 raw Spell Damage. Four of each give 40 of each stat. Matching worn gear focuses use the strongest applicable effect in their category. Eight Dodging scales give 960 HP, 960 mana and 40 raw damage shield. Improved Dodge I supplies one +10 worn effect with the reviewed default additive-worn rule of zero. The live worn HA/SD caps are 750 before applicable modifiers. [Host items, routes and rules](eligibility.json).

On test, use a level-50 character. Obtain the white scales from Lady Vox in Permafrost or the red scales from Lord Nagafen in Nagafen’s Lair. Use the exact item ID in the recipe table. Try the matching gem, then try an incorrect gem or container. Forge three matching Normal scales into Polished, four Polished into Exalted and four Exalted into Ascended. Socket a scale in a type-7 Cloth Cap or Cloth Wristband. Check HP, mana, the scale icon and the host’s original icon/effect. Repeat in both wrists. Compare eligible gem heals, nukes and avoidance with zero, one and two copies of the same top-tier effect. Check a bow, shield and pet as negative controls. Confirm the type-22 chest trophy can remain equipped alongside a type-7 chest scale. For stock, inspect all four Singed Goblin Eye qualities from Solusek’s Eye. In a matched encounter record effective healing, damage, survival, and time to exhaust mana.

For recovery before reopening, use the guarded inverse while game services are stopped and restore the matching item cache. After reopening, first account for player-held scale items, recipes learned and socketed scales. Removing the new definitions while players possess them can orphan items. Prefer a forward correction that keeps every earned ID.
