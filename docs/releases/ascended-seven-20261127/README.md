# 7% Ascended chance on ordinary drops

Every newly generated, eligible ordinary drop has a 7% chance to be Ascended when its Ascended item exists. The same chance applies to weapons, armor, shields, jewelry, other equipment and bags. An NPC's base loot table still determines whether it drops the underlying item. Already-generated loot keeps its original roll. Hunt augments, dungeon rewards, quests and reforging use separate reward paths.

| Quality | Rolls per 10,000 eligible drops |
|---|---:|
| Normal | 6,800 |
| Polished | 2,000 |
| Exalted | 500 |
| Ascended | 700 |

The server reads the three chances from the active ruleset. This release removes the extra armor and shield band and changes ruleset 1's `Zone:LootTierLegendaryChance` from 100 to 700. The active Polished and Exalted rules are 2,000 and 500. Fresh installations now seed those same three values. A missing tier variant returns the base item.

## Verification and in-game QA

The native test executes the loot selection block across all 10,000 possible rolls for a weapon, armor, shield, jewelry and bag. It checks missing variants, ineligible and already-tiered items, and disabling Ascended through the rule. A separate assertion checks all three fresh-install SQL values. Run `python tools/tests/test_loot_quality_rates.py` from the checkout root.

In Unrest or Befallen, loot newly spawned ordinary NPCs. Count eligible base drops by category and quality. Inspect and equip an Ascended weapon and an armor piece. The 7% is per eligible drop, so an individual NPC's per-kill chance can be lower. Compare its weapon or armor entry in the Loot Finder. Player acceptance is open.
