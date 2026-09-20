# Living economy

Requested September 20, 2026. Candidate based on dev's existing EC tunnel hub.

## Experience and acceptance

- Existing city merchants receive one random, accessible named-drop item, quantity
  one, per world restart. Normal stock and player-sold stock are preserved.
- Ten player-looking traders around the EC tunnel offer six WTS and four WTB
  listings. Hail gives a linked item, exact price and actionable confirmation.
  The shared auction cadence is 75-120 seconds, with occasional local chatter.
- Catalog is an explicit allowlist of tradeable, permanent, unaugmented Classic
  equipment. No raid, quest progression, legacy removed, charged or later-era
  items. More expansions require a reviewed catalog update.
- Reference prices are P1999 Green 30-day averages, falling back to 90-day only.
  Missing prices are excluded. Capture source URL, date, revision, price window
  and latest auction date. Prices are snapshots, not live price promises.
- September 20 follow-up: scale prices for increased earning rates before the
  premium. Live item rolls are 4x and vendor payouts are 2.5/0.95 = 2.63x.
  Default income estimate is their product, 10.53x; raw coin is not multiplied.
  Policy JSON records the basis and observed rules. Drift blocks rotation until
  repricing. Tunnel sales cost ceil(reference platinum * income factor * 1.20),
  finds use 1.10, and WTB pays floor(reference * income factor * 0.70).
  Each offer is fulfilled only once per restart.
  Find prices exceed normal merchant costs, with a floor above WTB payout to
  prevent generated-stock arbitrage. No global item-price changes.
- Stock rotates only in world startup, never quest reload, repop, zone load or
  zone restart. A persistent generation invalidates stale offers. Catalog and
  active era are checked at generation, display and purchase. Disabled or invalid
  state refuses trades. No internet request occurs in a server process.
- Currency, inventory, stock and audit records commit in one database transaction.
  Failed or uncertain commits must not permit stale profile/inventory saves.
  Reject remote, instance, combat, trade, cursor-queue, lore and modified-item cases.

## Implementation plan

1. `tools/living_economy.py`, catalog JSON and Python tests: capture public wiki
   pricing and PEQ provenance; validate curated sources, pricing and era policy.
2. `server-mods/sql/2026-09-20-living-economy.sql`: disabled-by-default schema,
   finite offers and restart procedure. Generated content SQL reserves new NPC
   IDs and proves no collisions. Rehearse using a disposable schema.
3. `server-mods/code/zone/client_living_economy.cpp`: reuse native item display,
   inventory serialization and money packets; append finds to merchant windows;
   expose one quest trade entry point. World startup calls rotation once.
4. Quest plugin and ten NPC scripts: hail/confirmation, zone-local auction and
   bounded ambient lines. Use existing playable appearance tuples and map probes.
5. Focused native/SQL/quest tests, full world/zone compilation, independent review,
   release QA/rollback, CHANGES and milestone report. Promote at most through test;
   owner in-game acceptance is required for main under the normal branch policy.

## Commands and conventions

From this worktree: `python -m unittest discover -s tools/tests -p 'test_living_economy*.py'`.
Native transaction-unit tests use the existing Windows MSVC toolchain. Full
server compilation and SQL rehearsal run inside the existing Docker toolchain;
exact commands and evidence are recorded in the release report. Existing Python
unittest/Perl Test::More conventions apply. C++ uses tabs and existing Client and
ZoneDatabase helpers. SQL integer inputs are validated and strings use hex literals.

Always preserve unrelated work and player progress; back up before live SQL.
Never edit the original game client, vendor dependencies, global item prices or
era rules by hand. Activation requires a matched world/zone build and scoped
rollback. Automated proof does not replace in-game visual/economy acceptance.

Alternative considered: quest-only hand-ins. Native transactions are required
because a currency award, item delivery and stock decrement in separate calls
can split on a failure. Alternative pricing by globally editing items would
change unrelated merchants and rewards, so prices belong to individual offers.
