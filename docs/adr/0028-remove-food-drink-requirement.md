# ADR 0028: Remove character hunger and thirst

Date: 2026-10-11. Status: accepted and deployed for owner QA; native client acceptance pending.

The owner requested complete removal of food/drink requirements, their penalties
and empty-food/water text. The existing EnableFoodRequirement rule guards hunger
predicates but does not prevent depletion or low stamina packets. Changing only
that rule or setting FoodLossPerUpdate to zero also leaves old empty profiles and
quest setters capable of triggering client warnings.

Nightcap therefore permanently reports full nutrition and false hunger/thirst/
starvation predicates. Normalize before the initial profile and through the
existing stamina/setter paths. Consume requests restore full meters without
deleting items. Retain script API signatures and legacy rule catalog entries for
compatibility; their nutrition behavior is retired. Avoid bulk DB updates and
client string edits, neither of which fixes every runtime path.

Optional food/drink item bonuses, recipes and quest items remain. Stat food has
no consumption cost; no new stats or higher caps are introduced. Nutrition-only
spells/AAs become redundant, consistent with removal of the system. This is a
server build change deployed under explicit owner approval for live QA; manual
client acceptance remains pending.

Evidence and exact QA: [food/drink release](../qa/2026-10-11-food-drink-removal.md).
