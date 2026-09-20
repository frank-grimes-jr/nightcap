# Living economy release checks

Candidate dated 2026-09-20. Not yet activated. Do not interpret generated SQL or
a successful compile as live deployment or owner acceptance.

The candidate now also includes [six named residents](residents/README.md).
Follow their additional setup, Lavastorm map prerequisite, exact appearance/port
QA and independent rollback steps when activating this combined candidate.

## Intended behavior

- Twelve ordinary city merchants are eligible; ten receive one find per world
  generation, at most two copies of each find across the server.
- Ten tunnel traders offer six sales and four purchases, one transaction each.
  A sold-out trader remains present but no longer advertises unavailable stock.
- One shared timer attempts a line every 75-120 seconds while EC has clients;
  roughly 20% are local chatter. Sold-out/missing speakers can make a pulse quiet.
- Prices are whole platinum, fixed across charisma/faction, quoted before action.
  Tunnel sales are scaled P1999 reference plus 20%. Buyers pay 70% of scaled
  reference. Finds add 10% with a floor above ordinary purchase/resale prices.
- Current combined earning estimate is `4 * 2.5 / 0.95 = 10.526315...`.
  FBSS: reference 1,575 pp, ask 19,895 pp. This reflects loot-sale income, not a
  direct 10.53x coin-drop rule. These prices require owner balance acceptance.

## Installation gate

1. Review `policy.json`, `catalog-20260920.json`, and `generated/catalog.json`.
   The latter contains final scaled prices; the former is immutable source evidence.
2. Run focused tests, the disposable database rehearsal and quest tests. Build
   **both** world and zone from the same candidate; retain their hashes.
3. Before activation, check player presence, arrange a restart, take a verified
   full PEQ backup and preserve currently deployed world/zone, plugin and quests.
   Stop world and all zones gracefully. Do not use a live broad repop.
4. Apply `server-mods/sql/2026-09-20-living-economy.sql` once, then
   `generated/content.sql`. Both reject collisions; content rejects rule/item
   drift and nontransactional tables. They leave the feature disabled.
5. Install the matching binaries, `server-mods/plugins/living_economy.pl` and
   `server-mods/quests/ecommons/999500.pl` through `999509.pl`. Enable with
   `UPDATE nightcap_market_state SET enabled=1 WHERE id=1;` while stopped.
   Start world first; verify one epoch increment, then boot zones.
6. Verify enabled state/era/earning rules, 10 find + 6 sell + 4 buy offers,
   quantity one, and matching running binary hashes. A world rotation failure
   refuses startup. Never manually call the rotation routine on a running server.
7. Complete the following normal-account QA before main promotion.

## Exact In-Game QA

Use the approved current QA client; this feature introduces no additional client
files. GM teleport/item preparation may assist, but repeat trades on normal accounts.

1. Enter East Commonlands. Rellan Ridgewalker is at world X=-300, Y=-1660,
   Z=3.75; Mirielle Dusksong is at -240,-1660; Caelith Emberweave at -80,-1650.
   Other sellers are Bromli Copperkeg (-35,-1705), Tamsin Quickstep (-90,-1735),
   and Varkyn Ashblade (-155,-1750). Confirm distinct playable appearances,
   grounding, readable names, normal visibility and no overlap with hub services.
2. Buyers: Harlon Frostbeard (-230,-1735), Nimri Mossfoot (-300,-1720), Grukk
   Bargainhand (-390,-1710), Selindra Starsong (-385,-1585), all Z=3.75.
   Hail one, inspect the item link and quoted price. Put exactly one requested,
   unmodified item on the cursor and click the sell link. Confirm one payout,
   one removal, correct weight and persistence after zoning/reconnect.
3. Hail a seller with empty cursor and sufficient carried money. Buy one.
   Confirm the exact ask is deducted once, the actual linked item is on the
   cursor, and reconnect retains both balances. Repeat link: no second purchase.
4. Test insufficient funds, occupied/queued cursor, wrong item, augmented item,
   existing lore conflict (including pet armor), combat, and out-of-range use.
   Each must preserve all money/items and explain the rejection. Ordinary
   hand-ins of wrong items and mixed coin must be returned in full.
5. Watch at least ten minutes with auction enabled, then disabled. Auction
   filtering should work; chatter is nearby only. Two clients should hear the
   same line from the same NPC. Sold-out offers must never be advertised.
6. Visit the exact city merchant locations in `generated/placement.json`.
   Identify current stocked actors using the query below; two of twelve are
   intentionally empty each generation. Normal stock, faction restrictions,
   buyback and parcels must continue working. Find is quantity one with the
   catalog price, regardless of charisma. Purchase it with empty cursor.
7. With two clients viewing one find, buy simultaneously: exactly one wins.
   Sell native buyback stock while the other client has a shop open; a collision
   must close/reject the old find quote, not buy a replacement item. Reopen and
   verify the correct fresh list. Closing a shop invalidates queued purchases.
8. Reload quests, repop only in an isolated QA copy, restart a zone, and reopen
   shops: consumed offers remain consumed. A controlled full world restart
   increments the epoch once and rotates the selection. Old links must reject.
9. In an isolated database copy only, change earning rules, present a future-era
   catalog entry and inject a commit-disconnect. No future offer or stale price
   may trade; reconnect after an uncertain commit must show exactly the stored
   item/payment outcome. Restore via `era.json` tooling, not ad hoc live era rules.

```sql
SELECT o.epoch,n.name,a.zone_id,o.kind,i.Name,o.price_cp/1000 AS platinum,o.remaining
FROM nightcap_market_offers o
JOIN nightcap_market_actors a ON a.npc_id=o.npc_id
JOIN npc_types n ON n.id=o.npc_id JOIN items i ON i.id=o.item_id
ORDER BY a.zone_id,o.kind,n.name;
SELECT * FROM nightcap_market_trades ORDER BY traded_at DESC LIMIT 30;
```

## Rollback

With world/zones stopped and a fresh backup, apply `generated/rollback.sql`.
It verifies ownership, disables offers, removes only the ten new NPC/spawn sets
and their base-instance non-corpse saved spawns. Existing merchants, corpse and
other-instance state, player wallets/items, catalog, epoch and trade audit remain.
Remove only the ten installed adapters and this plugin, restore the paired old
binaries, and restart. Do not restore an old whole database over earned progress.
The retained catalog/audit intentionally prevent blindly rerunning initial setup;
re-enabling after full rollback needs a reviewed actor-restoration migration.

## Reproduction

Run from the repository candidate root:

```powershell
$env:NIGHTCAP_TEST_EVIDENCE='E:\EQ_Local_Dev\artifacts\living-economy-20260920'
python -m unittest discover -s tools/tests -p 'test_living_economy*.py' -v
python tools/tests/rehearse_living_economy.py $env:NIGHTCAP_TEST_EVIDENCE
```

The native test requires the existing MSVC Build Tools. The database test uses
Docker, creates a uniquely named disposable schema, and drops only that schema
in `finally`; it never writes live PEQ. Run the Perl test with the staged
`server-mods` directory as its argument. `build_living_economy.py` runs only in
the container and installs nothing; see its `--help` for staging paths.
