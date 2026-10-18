# Proposed guaranteed Ascended quest rewards

Accepted direction, October 18: final quested armor and weapons should grant
their top ordinary quality automatically; **repeatable/easily farmed quests are
excluded**, per the owner's explicit clarification. Ordinary quality is named
Ascended; Ascension is the distinct hunt quality/epic forging name.

This is a design decision for review, not a deployed reward conversion.

## Eligibility contract

Use an explicit catalog of audited terminal rewards, keyed by installed quest
path, NPC identity, reward branch and original item ID. Each entry must document
the full acquisition chain, completion/replay gates, active era, and why it is
neither repeatable nor easily farmed. Do not infer eligibility from item name,
equippable slots, a quest API call, or an item's presence in a reward index.
Unknown or unaudited entries retain their current reward.

For eligible ordinary armor/weapons, verify the exact existing Ascended item
definition (normally base ID +600000), corresponding family/name, usable slots,
class/level requirements and RoF2 ID ceiling before changing the reward. Preserve
the quest's inputs, flags, XP, faction, cash and completion behavior. If no valid
variant exists, flag catalog work rather than inventing an ID or losing the reward.

Exclude repeatable hand-ins, merchant exchanges, tradeskills, starter/free/hail
gear, intermediate quest components, returned items, summon spells, bags,
augments and dungeon/hunt rewards. Do not globally intercept SummonItem or
QuestReward: those APIs also deliver returned inventory and nonreward grants.
No retroactive conversion of owned items is implied by automatic future rewards.

Epics need a separate explicit decision: existing class-epic upgrades use
+800000 and their own forge/essence/platinum progression. Do not accidentally
bypass that system with the ordinary +600000 conversion.

## Concrete evidence from the local quest mirror

These are source examples, not proof of current production script identity:

- `rathemtn/Hasten_Bootstrutter.lua`: Journeyman's Boots (2300) are granted by
  QuestReward after a component/currency hand-in, with no completion guard in
  the script. Excluded as repeatable under the accepted rule.
- `soltemple/Vurgo.pl`: Harvester (5316) and Words of Darkness (10527) are
  repeatable component rewards. The same script returns rejected items with
  summonitem. A global grant hook would upgrade returns and break exclusions.
- `soltemple/Blaize_the_Radiant.pl`: four armor rewards (4921–4924) have component
  checks but no one-time completion guard. These also remain excluded unless
  the owner later changes the policy for substantial repeatable chains.
- `soltemple/Genni.pl`: gemstone and galvanized-platinum exchanges are intermediate
  quest components, not terminal armor/weapon rewards.
- Tracked `server-mods/quests/ecommons/Epic_Forgemaster.pl`: separate +800000
  class-epic conversion, also using summonitem for rejected-item returns.

Many traditional Classic equipment quests are technically repeatable. Applying
the exclusion literally will leave those normal; it is not enough to classify
only visibly cheap quests. A reviewed catalog must establish actual eligible
one-time rewards before any quest implementation or promotion.

## Required implementation proof

Capture current production scripts with hashes and Perl/Lua/ID precedence,
identify qualifying quests and verify target definitions read-only. Test the
exact success branch, failed/partial hand-in returns, repeated completion,
component-only branches, inventory-full behavior and separate epic paths.
Pair script changes with supported quest reload; new item definitions would
add cache/restart requirements. Publish exact NPC/zone/item player QA with the
candidate. Keep the feature unreleased until implemented and activated.
