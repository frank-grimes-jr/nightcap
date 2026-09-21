# ADR 0044: guarded tunnel services and creation-time provisions

Status: implemented candidate; owner in-game acceptance pending. September 21, 2026.

The owner requested a complete, more natural Commonlands service hub and improved
starting provisions. Keep the existing approved Classic spell/tradeskill pools,
add every legal spell component, and split large vendor stocks into nearby NPCs.
Use native trainers, existing client crafting assets and short patrol grids.
Capture exact target preimages and emit guarded transactional content changes;
local captures are rehearsal evidence only. Price the otherwise free Plains
Pebble explicitly at 100 copper base. Rollback restores its old price.

Expand actual finite offers to two per trader and use (npc_id,item_id) ownership,
with (epoch,npc_id,item_id) audit identity. Preserve native transactional money,
item and stock changes. A single zone coordinator varies OOC/auction with first
names, bounded timers and silence without players. Fake cosmetic offers and one
timer per NPC were rejected because they misrepresent availability or flood chat.
Keep expanded audit keys during rollback; restore the original rotation routine.

Grant the requested 100pp and class robe/weapon in character creation. The native
wallet insert is necessary because a creation profile's platinum field is not
wallet persistence. Consume the approved name reservation and reject existing
wallet/inventory/initialized profiles before any writes. Do not add a repeatable
login grant or retroactively change existing characters. Preserve unknown
race/deity starting rewards by failing creation if equipped slots differ from
the audited baseline. Retain custom item definitions after rollback for owners.

Consequences: paired world/zone, shared-memory regeneration, supervisor, schema
and quests must be deployed together. Procedure replacement is nontransactional
DDL and must be verified before world boot. New-character currency farming is an
explicit consequence of the requested 100pp, not silently constrained per account.
Automated evidence covers policy, selected native failures, SQL rollback and map
geometry. Actual RoF2 models/windows/movement and balance remain owner QA gates.
See the release README and QA checklist for exact steps and limits.
