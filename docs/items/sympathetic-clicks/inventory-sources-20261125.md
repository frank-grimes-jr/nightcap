# Classic sympathetic inventory sources — live for QA 2026-11-25

Deployed in main PR 534 for in-game QA. [Production verification](../../releases/sympathetic-inventory-20261125/production-verified.json). The existing two Ascended clicks become type 1 inventory clicks, and four additional Ascended stock items grant the same rank I buffs. Buff identities and strength are unchanged; copies refresh rather than stack. Normal, Polished and Exalted do not gain clicks. Two-second activation and existing item focuses remain.

| Buff | Item | Verified local named source | Spawn and loot evidence |
|---|---|---|---|
| Healing | White Gold Necklace (610147) | froglok noble, Lower Guk 66175 | spawn 62171, 25% spawn weight, 1740 seconds; loot weight 70 |
| Healing | Jagged Band (610364) | Garanel Rucksif, Unrest 63062 | spawn 7881, 20% spawn weight, 640 seconds; loot weight 80 |
| Strike | Ring of Xorbb (610215) | King Xorbb, Gorge of King Xorbb 16033 | four spawn rows, 5% spawn weight, 7200 seconds; loot weight 80 |
| Strike | Djarn’s Amethyst Ring (610366) | Efreeti Lord Djarn, Nagafen’s Lair 32062 | spawn 6444, 25% spawn weight, 640 seconds; loot weight 25 |

Local PEQ read 2026-11-25: Classic zone expansion 0; source weights are not overall drop probabilities. Production verification found all four named paths in Classic zones with unrestricted expansion bounds and empty content flags. Existing Moonstone Ring and Runed Lava Pendant remain the third source of each line. The Reforging Box provides existing quality progression where enabled.

`tools/sympathetic_content.py` generates the guarded forward, full disable and `content/rollback-inventory.sql`. Forward accepts the exact prior equipped-click state for the original two, or the blank fresh-install state; it rejects drift and checks the new item owners against spell-reference collisions. Rollback restores the two equipped clicks and clears only the four new clicks while retaining saved buff definitions. A full disable is distinct. Both require matched item cache refresh and consumers; retain existing spell cache, paired native binary and signed client. Do not restore player inventory or buffs. The original item and spell client assets require no new spell IDs. Item data refresh and reconnect are required; RoF2 right-click behavior, including bags, remains in-game QA.

Run the focused content tests and isolated typed-database rehearsal before promotion. The live receipt records six verified item-cache changes, 12 workers and open access. Actual client interaction and player acceptance remain open. Verify a backup and current item preimages before any authorized activation. The existing November 13 report records a previous release and is not proof this candidate is live.

## In-game QA on production

1. In Lower Guk, Unrest, Gorge of King Xorbb and Nagafen’s Lair verify the named NPCs and their item drop paths; ordinary random drops are not guaranteed.
2. On all six Ascended items, right-click from a general inventory slot and from a bag; verify the two-second cast, effect, repeated refresh, zoning and relog. Check lower qualities have no click and the old items no longer require equipping.
3. Confirm all existing focuses remain, both different buffs coexist, same-line copies refresh instead of stacking, and a qualifying heal or nuke receives only the established 5% capped at 48. Test worn healing precedence and partial resists.
4. Compare representative progression and geared multiclass encounters with and without the buffs, including cheapest eligible casts, effective healing and mana; retain open balance acceptance until owner sign-off.

Wiki impact: Equipment, Features and Recent changes have published instructions for the six live items; ordinary dynamic loot finder supplies stock sources. Home, commands and custom item/zone catalogs have no new custom entries. The public release 20261125-sympathetic-inventory-v1 passed all 631 HTTPS file checks and five private-path checks.
