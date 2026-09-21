# Tunnel services and starting provisions

Status: implementation in progress; not deployed or manually accepted.

## Accepted scope

The owner's six requested updates cover the East Commonlands tunnel, resident
activity, auction variety and new-character provisions. Existing characters and
their equipment, wallets, binds, market purchases and AA ownership are preserved.
Normal feature -> dev -> test -> owner QA -> main policy applies to this release.

* Add ordinary food/drink and every component/focus needed by the currently
  allowed level 1-50 Classic spell catalog, including all pet summons, bone chips
  and bat wings. Derive requirements from original class access, not widened
  `spells_new.classesN` columns. Do not sell spell-created or quest rewards merely
  because they resemble reagents. Retain meaningful reagent prices.
* Provide all tradeskill disciplines (including research, alchemy, poison making,
  tinkering and fishing), their vendor supplies, portable containers and usable
  fixed stations. Crafting drops and progression are still earned.
* Place one trainer for each of 16 classes. Regroup the existing services,
  merchants, trainers and residents in irregular conversational clusters with
  clear routes to the entrance, travel doors and arrival point. Validate grounding
  and walking paths with the server map before in-game rendering checks.
* Add walkers and varied OOC from multiple residents. Use first names in channels,
  one bounded zone coordinator, silence in empty zones and avoid immediate repeats.
* Increase real finite market sellers and simultaneous offers. Advertise actual
  available items with varied phrases and randomly selected ` // `, ` -- ` or
  `, ` separators. Keep native atomic trade, stale-quote and sold-out protection.
* New characters start with exactly 100 platinum, one modest class-usable weapon
  and a robe with 10 AC and +5 to their primary class's main stat. Grant through
  character creation, not repeatable login rewards. Items must remain below the
  RoF2 item-link limit. No damage procs, heroic stats or regeneration.

## Implementation plan and proof

1. Capture the actual local content/schema; record the legal reagent/tradeskill
   catalog and collision-free IDs. Build guarded reversible migrations and
   rehearse apply, drift rejection and rollback in a disposable schema.
2. Add starter item definitions and creation-time provisions; test all classes,
   equipment compatibility and creation/reconnect behavior.
3. Extend finite offers and native announcements; test multiple offers, individual
   consumption, stale quotes, wallet/inventory failures and channel formatting.
4. Add services, stations, trainers, clusters and paths; test stock coverage,
   class mapping, separation, grounding and saved-state scope.
5. Add varied resident dialogue and bounded timers; exercise actual Perl adapters.
6. Build matching world/zone, review changes, update CHANGES/status/ADR/milestone,
   and deliver an exact owner QA checklist and rollback procedure before promotion.

The riskiest change is expanding native finite-market ownership beyond one offer
per actor. Retain transactions and trade audit; do not replace them with quest-side
money/item operations. Cosmetic fake offers and repeated login grants were rejected
because they cannot reliably deliver the requested inventory or starting package.

## Balance assumptions

Starter weapons improve on rusty weapons without replacing later dungeon rewards.
The robe receives +5 STR for martial damage classes, +5 DEX for rogue/bard,
+5 WIS for priests/beastlord and +5 INT for intelligence casters/shadowknight.
The 100pp request is literal. New-character currency farming is a known economic
effect of that request; no unrequested account restriction is added.

Local DB capture initially blocked: the original MariaDB container is stopped and
Windows denies binding port 3307. A temporary network-isolated container uses the
stopped local volume for read-only PEQ capture and separate test schemas; it has no
published ports and cannot serve players. Hosted production is unchanged.
