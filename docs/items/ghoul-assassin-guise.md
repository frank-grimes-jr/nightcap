# Guise of the Deceiver in Lower Guk

Each fresh `a_ghoul_assassin` (NPC 66171) in Lower Guk gets one independent 20% chance for Guise of the Deceiver (2469). A success adds one copy through the ordinary item-quality roll. The 20% covers all qualities combined.

All four Guise qualities use Class ALL and Race ALL following the [November 20 item correction](guise-all-classes/README.md). Equip the item in the face slot and right-click for its Dark Elf illusion.

Local PEQ on November 14, 2026 showed that table 14195 awards Mask of Deception (2472) or Serrated Bone Dirk (7502) at 80/20 per equipment roll. It also has a separate Black Pearl/Topaz pool. The default global loot multiplier of four repeats those table rolls. The bonus uses one spawn event so the multiplier cannot repeat it. The existing four Guise definitions supply the item and its Dark Elf illusion.

## Installation and recovery

The spawn-bonus source is [the Lower Guk quest for NPC 66171](../../server-mods/quests/gukbottom/66171.lua). Install it as `quests/gukbottom/66171.lua` in the active quest tree. Check for an existing ID, name, version-specific or default NPC quest before installing into another environment. Merge handlers if necessary. For an active Lower Guk worker use `#reload quest` in that zone, or let a fresh zone load it. This quest installation needs no SQL, server build, item-cache regeneration or client download. The separate [ALL/ALL item correction](guise-all-classes/README.md) uses guarded SQL and an item-cache rebuild. An already spawned assassin keeps its loot.

To withdraw the bonus, remove this spawn handler and reload quests. Existing corpses, saved NPCs and player-held items retain their loot. The Fabled assassin (66176) and the camp placeholder (66019) have separate NPC IDs.

## Verification and player QA

The local akk-stack container sees the source-identical quest. [The Lua 5.1 regression](../../tools/tests/ghoul_assassin_guise.lua) runs all 100 integer outcomes with each stock equipment item. It checks one roll, the exact item and quantity, both coexistence cases, and zero rolls when a saved NPC resumes. Run `lua5.1 tools/tests/ghoul_assassin_guise.lua` from the repository root. The zone binds `Random.Roll` to its integer percentage roll and `NPC:AddItem` to the quality-aware `NPC::AddLootDrop` in [loot.cpp](../../server-mods/code/zone/loot.cpp). The automated test exercises the quest with controlled NPC and RNG inputs. OVH installed the main PR 471 quest at 20:55 UTC on November 14, 2026. The installed file matched main and passed the same Lua regression inside the production game container. The world roster showed zero Lower Guk workers before and after installation. All twelve zone workers and five services retained their identities. The next Lower Guk boot loads the quest. Owner in-game QA remains open. [Production receipt](../releases/ghoul-assassin-guise-20261114/verified.json).

1. Enter Lower Guk (`gukbottom`) and go to the assassin camp near `/loc 620, -753, -109`. The local camp has a 29-minute respawn and a 30% assassin spawn weight.
2. Kill newly spawned **a ghoul assassin** and inspect the corpse. Record the Guise at any quality alongside the usual loot. Confirm the usual mask or dirk also drops when the bonus misses. Count actual assassins when checking the rate.
3. Loot a Guise and use its Dark Elf illusion. Kill a camp placeholder and check that it has only its own loot. A database-only loot simulation omits this scripted roll.

## Wiki impact

The Lower Guk page describes the source and chance. Loot finder and Change Log link to it. The finder calculates database drops, so its generated rates do not include this scripted bonus. Hunt catalog values, dungeon completion rewards, commands and the Home and Features directories have no corresponding change. The source review flagged historical branch drift along with the new quest. The shared review ledger was left at its last audited revision. Public publication is pending.
