# ADR 0066: Guaranteed Ascended rewards for substantial class-armor quests

Date: 2026-10-22. Policy accepted by the owner; implementation is a candidate.

## Context

Palwar received Normal Crafted armor from the Meadowgreen quests. The October 18
proposal excluded every repeatable quest, unintentionally excluding substantial
Classic class-armor quests. The owner clarified that those quests should qualify
even when repeatable, while cheap/basic hand-ins remain excluded.

## Decision

Use an explicit audited catalog of terminal armor rewards, not a global item-grant
hook or an item-name heuristic. The first reviewed catalog contains 37 rewards:
Crafted, Lambent, Darkforge, Ivy Etched and Totemic. Change only their terminal
grant literals to the verified existing ordinary Ascended definitions (+600000).
Keep all reward requirements, consumptions, XP, faction, dialogue and return paths.
Preserve a downstream Shadow Knight epic dependency by accepting Normal or
Ascended Darkforge Helm/Breastplate/Greaves at Kurron Ni, including mixed sets.
Its platinum threshold, legacy cash return, faction and letter gating remain.
Repeated completion requires another complete set of inputs and has the same
reward quality. Ordinary tier terminology is **Ascended**, separate from Hunt
Ascension and epic forging.

An item being an ingredient does not itself exclude the final armor: Totemic
uses basic Banded armor but requires additional hunted components. Its Banded
inputs are not upgraded. Prepared Lambent gems and other intermediate outputs
also remain unchanged. Future catalog additions require separate branch/input/
target review. Armor of Ro's tradeskill finish, mixed Temple cleric branches,
weapons, epics and unaudited quests are not implemented by this first catalog.

## Consequences

These are intentionally stronger rewards for substantial journeys. The unchanged
trade policy permits farming and trade; no new one-time lock is invented. Existing
Ascended item stats remain untouched, and dungeon/Hunt progression still needs
owner balance QA. No blanket migration of owned items is implied.

The alternative of excluding all repeatable quests is superseded by the owner's
clarification. A global SummonItem/QuestReward hook was rejected because returns,
materials and other grants share those APIs. The reward-only delta is smaller and
auditable. The candidate requires source promotion and authorized quest reload;
tests do not establish deployment or player acceptance.

See [catalog](../items/quest-armor-catalog.json) and
[evidence and QA](../releases/quest-armor-20261022/README.md).
