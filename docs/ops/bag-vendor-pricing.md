# Bag vendor pricing — deployed for live QA, #22

**2026-09-15 deployment:** the owner authorized all implemented candidates for live
testing. This ladder is now applied; economy and in-game acceptance remain pending.
See [combined release evidence and QA](../releases/live-qa-20260915/README.md).

SQL and disposable MariaDB tests passed before the September 15 deployment.
The observations below describe the captured pre-deployment inventory.

## Original problem and deployed behavior

Bartholomew Packwell, NPC 999225 / merchant 99225 in PoK, stocks 22 containers.
Eighteen have zero base price. The four priced bags range from 2,500 platinum
to 1,000,000 platinum. This creates free upgrades beside extreme legacy prices.

The candidate gives every existing stock item a positive price, increasing with
slot count. It changes only `items.price`; names, container restrictions, capacity,
weight reduction, stock and NO TRADE flags stay as captured. Specialized
containers remain specialized; general-purpose use of every bag is not certified.

| Slots | Deployed base platinum | Slots | Deployed base platinum |
|---|---:|---|---:|
| 8 | 10 | 22 | 750 |
| 9 | 20 | 24 | 1,000 |
| 10 | 40 | 25 | 1,250 |
| 11 | 60 | 26 | 1,500 |
| 12 | 100 | 28 | 2,000 |
| 13 | 125 | 30 | 2,750 |
| 14 | 175 | 32 | 3,500 |
| 15 | 200 | 34 | 4,250 |
| 16 | 250 | 36 | 5,000 |
| 18 | 375 | 38 | 6,250 |
| 20 | 500 | 40 | 7,500 |

These are **base** prices, not guaranteed UI quotes. The database has
`Merchant:SellCostMod=1.0499999523163`, `UsePriceMod=true`, and
`UseClassicPriceMod=false`; charisma/faction pricing still applies. Loot income
uses `BuyCostMod=2.5`. As an illustrative unadjusted reference, item 5350 Fine
Steel Long Sword has base price 6 platinum, implying 15 platinum sell income
before the character/merchant modifier. No farming-rate or encounter-time claim
is made. At that reference the largest bag represents about 500 swords.

Alternatives for review: half this ladder (5–3,750 platinum) favors early
inventory convenience; twice this ladder (20–15,000) creates a stronger coin
sink but may overburden solo play. The middle ladder is deployed for testing; its balance is not yet accepted. Native specialty/weight-reduction differences still warrant manual QA.

## Resale and scope

The original setup comment interpreted `nodrop=0` backward. It means NO TRADE.
All 22 stock items have this flag, and `Handle_OP_ShopPlayerSell` rejects
`!item->NoDrop` before calculating the payout. Preserving it avoids turning
these bags into a buy/sell profit loop under the 2.5 loot-income multiplier.
The candidate refuses stock whose NO TRADE or sellrate flags have changed.

Prices belong to item IDs globally. Merchant list 9905 contains four shared
entries (17215, 52082, 54262, 54263), but no NPC currently references that list.
They would inherit the new prices if reused. This is explicitly part of candidate
review. If pricing must be exclusive to Bartholomew, use separately reserved and
collision-checked Nightcap item clones instead; that is additional content work.
Existing player bags with these IDs would also inherit the price metadata.

## Rehearsal and safeguards

The exact 22 input rows are retained in
`tools/tests/fixtures/bag-vendor-stock-20260915.jsonl` (public item metadata only).
The SQL is `eq-solo-gm/scripts/bag_vendor_prices.sql`.

The script locks merchant stock, NPC identity and target items in a serializable
transaction. It accepts only the exact captured stock, slot/capacity/type/weight
metadata, NO TRADE flags and sellrate, with prices entirely in the original or
candidate state. It refuses mixed states. It changes only price; a repeat apply
is a no-op. Rollback restores all exact original prices, including the four
nonzero legacy values. Its conditional UPDATE remains inert after guard failure
even if someone mistakenly uses mysql's `--force` option.

Run from this checkout:

```powershell
python -B -m unittest discover -s tools/tests -p test_bag_vendor_prices.py -v
python -B -m unittest discover -s tools/tests -p test_aa_client_strings.py -v
```

Three MariaDB integration tests pass: apply; repeat apply plus repeat exact
rollback; and nine rejected drift cases (price, NO TRADE, container type, mixed
prices, missing stock, added stock, duplicate item, NPC routing, invalid mode).
They use a new disposable database with session-local copies, so failed temp
creation cannot reach live tables. Container administrator credentials stay
inside the container. Each completed suite removes its schema. An interrupted
run can leave an empty `nightcap_bag_test_*` schema for explicit inspection.

Thirteen AA unit/CLI regressions pass. Post-test capture matched all 22 live bag
rows exactly, and zero scratch schemas remained. Initial pricing tests failed
because the SQL did not exist; the first isolated-schema setup as the gameplay
user failed permissions. The corrected administrator-backed rehearsal passed.
An initial post-check command had PowerShell quoting wrong; the corrected
read-only comparison passed. None of these failures changed live item prices.

## Deployment, rollback and exact in-game QA

1. Review the price ladder and four shared merchant entries; retain candidate
   status until the intended economy choice is accepted.
2. Take and verify a fresh PEQ backup using the established backup runbook.
   Capture current stock/flags/prices and compare the exact candidate preimage.
3. In a **fresh** mysql batch connection to the intended database, source
   `bag_vendor_prices.sql` without `--force`. Do not embed this script in an
   already-open application transaction. Any nonzero exit is a failed deploy.
4. Rebuild shared item data and coordinate the required zone reload/restart;
   establish all serving processes use the new cache. The combined September 15
   deployment completed this refresh; these steps document future redeployment.
5. PoK: target Bartholomew Packwell. On an ordinary non-GM character, check all
   22 listings have positive prices increasing by capacity. Record actual quotes
   and charisma/faction. Compare the proposed base ladder with applicable mods.
6. Buy the 8-slot item 53684, 16-slot 52082 and 40-slot 54726 with an exactly
   recorded wallet. Verify deduction equals the quote; insufficient funds must
   refuse the sale without item or coin change. Verify actual bag capacity,
   item restrictions, and weight reduction; do not assume specialized bags hold
   every item. Try resale: server refuses it and grants no coin. Confirm ordinary
   loot still sells normally. Zone, camp/relog and recheck item/coin persistence.
7. Recheck merchant list 9905 has no NPC association. If it has been activated,
   record the exact NPC/zone and compare its quotes for 17215, 52082, 54262 and
   54263 before proceeding. Confirm unrelated item prices remain unchanged.
8. For rollback, use a fresh session with `SET @nightcap_bag_rollback=1;` before
   sourcing the same script. Require successful guards/exit, then repeat shared
   memory and process refresh and verify original prices. Never overwrite drift.

Follow feature -> dev -> test with this QA spike. Owner in-game sign-off is
required for main promotion and issue closure. Deployment evidence is linked above.
