# Universal item trading — October 4, 2026 deployment

**Deployed to OVH after the owner's October 4 approval to push to main and
server.** Main source promotion is `1a5c0fe`; all five matching native binaries
run in `nightcap-game:free-trade-20261004`. Manual gameplay acceptance remains
open; the owner authorized activation for live QA.

## Behavior

- Every item is player-tradable, including NO DROP, NO TRANSFER and already
  attuned instances, bags, contents and augments. Future definitions inherit
  the policy. Lore ownership and inventory capacity still apply.
- Every originally NO DROP item sells to an ordinary merchant for **1pp per
  physical item**: five stack units pay 5pp; one charged object pays 1pp total.
  Player `#sellall` uses the same payout and still retains containers themselves.
- Ordinary prices retain their existing calculations. Former NO DROP purchase
  prices have a 1pp floor after modifiers, including buyback stock. Existing
  expensive bag purchase prices remain expensive.
- SQL item definitions and saved attunement remain intact for provenance and
  rollback. Effective flags are projected into shared memory and client packets;
  SQL `nodrop=0` alone therefore no longer establishes an in-game restriction.

The native merchant preview can show its standard quote instead of the fixed
payout. A merchant-open message explains the override; the server controls the
actual wallet change and sale receipt. Quote rendering remains a RoF2 QA caveat.
No signed client update is included.

## Audit and design

Read-only OVH audit: 308,961 definitions; 171,561 NO DROP, 50,688 attuneable,
932 NO TRANSFER, and 5,454 stackable former NO DROP definitions. Of the NO DROP
pool, 152,292 have zero price and 1,464 are temporary. There are 2,479
merchant-listed definitions with zero price or sellrate. One definition is both
stackable and multi-charge, making that regression a real catalog case.

Hosted `Merchant:BuyCostMod=2.5` and charisma/faction adjustment are enabled.
Setting price=1000 alone would not produce the requested payout. The fixed branch
bypasses those multipliers only for the original NO DROP pool. Summons and free
quest rewards intentionally become income sources; measure acquisition rates in
QA rather than claiming the economy is balanced. Curated living-economy offers
and alternate currencies retain their separate contracts.

`Items:FreeTrade`, default true in this candidate, is applied by
`SharedDatabase::LoadItems` through `common/item_trade_policy.h`.
`ItemData::FreeTrade` and `FixedSellPrice` travel with shared memory. Raw
`IsAttuned()` remains the save API; `IsAttunedForTrade()` handles restrictions.
All six item codecs use the effective predicate. Advanced loot retains missing
item, corpse access, physical preimage and receipt checks while removing obsolete
NO TRADE confirmation for converted items.

The plan was to inspect hosted flags/native pricing; add tests; implement
projection and both sale paths; compile preserved hardened production source;
verify a separate cache; and promote only through the authorized boundary.
Risks are shared-memory ABI compatibility, sale-unit counting, native quotes
and repeatable free-item income. The SQL-rewrite, FV-only and global-price-rule
alternatives are evaluated in [ADR 0054](../../adr/0054-universal-item-trading.md).

## Verification

Native regressions compile the actual recursive trade gate, merchant pricing
block, `SellAllSlot` and advanced-loot consent function. They cover raw attunement,
nested contents, missing definitions, disabled policy, price preservation,
modifiers, charged/stacked/invalid quantities, overflow, temporary items and
purchase floors. The initial compile failed before the new policy header existed.
Independent review found and resolved the separate `#sellall` payout and mixed
stack/charge cases. Gameplay remains distinct from these fixtures.

```powershell
python -m unittest discover -s tools/tests -p test_free_trade.py -v
python -m unittest discover -s tools/tests -p test_gameplay_policies.py -v
python tools/tests/test_advanced_loot_bulk.py --root . --output <evidence.json>
python tools/tests/test_advanced_loot_access.py --root . --output <evidence.json>
```

All six native trade tests, two existing gameplay tests, advanced-loot bulk/access
controls, all five Linux native targets and the private-login crypto self-test
passed. The actual loader verified every one of 308,928 local catalog rows with
the policy enabled, disabled and enabled again; the two enabled caches are
byte-identical. The hosted catalog has 33 additional definitions covered by the
same policy. The first fixture attempt stopped on missing zone/instance tables;
adding those isolated dependencies resolved it. Both temporary schemas/accounts
were removed. These local verification steps did not modify live game/cache/item
data; the later approved hosted activation is recorded below.

Evidence: [build](build-summary.json), [cache passes](cache-check.json),
[tests](tests.json), [hosted audit](hosted-audit.json),
[source provenance](source-provenance.json), [binary package](package.json).
The 220,837,734-byte package contains all five matching binaries. Operations
scripts in ops/ archive this exact run and reference its local evidence paths;
they are not general deployment commands. Local operation evidence is under `E:/EQ_Local_Dev/artifacts/all-items-tradable-20261004/`.

## Verified hosted activation

The new runtime started at **2026-10-04T21:43:46.214625821Z**. Every one of
**308,961 hosted items** has effective tradable flags; all
**171,561 original NO DROP items** carry the 1,000-copper
fixed payout. The actual loaded cache was checked row by row against SQL before
reopening gateway access. All 12 zone workers plus world, UCS and loginserver
match the verified build; the new runtime has zero restarts and no detected
native, quest or SQL startup errors.

A fresh full PEQ backup passed gzip/completion verification before activation.
Closed-gateway checks preserved 47 player, receipt,
settings and saved-state tables; 8139 quest/plugin files;
the item, spell, NPC, spawn and merchant tables; and client release 2026100406.
Database, web and tunnel services retained their identities and start times.
The only intentional database change is ruleset 1 **Items:FreeTrade=true**.
No database restore or item-definition rewrite occurred.

[Activation](activated.json), [complete hosted cache](hosted-cache.json),
[fresh runtime report](live-report.json), [backup and preflight](preflight.json),
[closed-gateway verification](verified-closed.json), [uploaded package](server-package.json).

## Exact in-game QA spike

Use two normal accounts in **East Commonlands**, with empty general slots.
Provision disposable items through a GM separately; perform transactions as
normal players. Record wallets in copper, then verify persistence after camp/zone.

1. Trade **990500, Winged Helm of the Dawn**, both directions: no NO DROP/NO TRADE
   marker or rejection, exactly one copy after relog. Repeat **13555, Ancient
   Longhandled Frostreaver**, for NO TRANSFER.
2. Trade an already-attuned saved **15802, Cloak of Greater Pernicity**. Repeat
   with an augmented item and converted contents inside **17969, Hand Made
   Backpack**. Check augment IDs, charges, ornamentation and evolving ownership.
   Check shared bank, parcel and barter if used; direct-trade tests do not certify
   the existing parcel format's handling of every metadata field.
3. At **Bartholomew Packwell, NPC 999225 / merchant 99225**, sell the helm and an
   empty **53684, Kregnad's Knapsack**: exactly 1pp each. Sell **1057, Mystic Cloak**
   with ten charges and with fewer charges: 1pp per cloak. Compare the preview,
   receipt and wallet, retaining the documented preview caveat.
4. Sell five **1425, Tundrabear Sandwich**, from a larger stack: receive 5pp and
   retain the remainder. Sell the rest with `#sellall`; no extra money/items and
   containers are retained. Check a mixed stack/charge fixture as well.
5. Repeat a fixed sale under different charisma/faction: still 1pp. **1001, Cloth
   Cap**, and **1004, Cloth Shirt**, retain their ordinary pricing.
6. Buy and immediately resell former NO DROP stock, including buyback: buying
   costs at least 1pp per unit, resale yields no profit. Packwell's expensive bag
   purchase prices remain intact.
7. Check recipient-full, duplicate-lore, cancel-trade, insufficient player funds
   and inventory-full purchase cases for no loss/duplication. Corpse rights and
   advanced-loot award receipts remain enforced.
8. Loot former NO DROP gear through advanced loot: no obsolete NO TRADE prompt,
   with normal ownership/receipt behavior. Sell a disposable former NO DROP
   summon/free quest reward for 1pp and measure its repeat acquisition rate.

All native gameplay checks remain open until observed by the owner.

## Activation and recovery

Before hosted activation, pin service/image/client-channel identities, take a
fresh full PEQ backup and preserve the current receipt-aware image. Close gateway
access, stop game cleanly, fingerprint player/receipt/rule/content data and quests,
then install all five matching binaries. Startup regenerates shared memory before
world/zones. Verify active `Items:FreeTrade=true`, cached flags/payout markers,
process hashes, health and preserved data before reopening. No item-table
migration is required.

Never install only zone or reuse old shared/items. Rollback closes access, stops
all native processes, restores the exact previous receipt-aware image and rebuilds
its old-format caches. Preserve current player progress and award receipts; do
not restore a historical database simply to reverse this policy. Completed trades
remain completed. A policy-only disable also requires cache regeneration and a
coordinated restart. A rule reload alone is insufficient.

The completed rollout used the unchanged blessing-lifetime native image as its
rollback baseline and preserves client release 2026100406. Nine deployment fault
tests cover startup, health, cache mismatch, gateway failure, data drift, scoped
rule ownership and content-snapshot failure. The production cache verifier also
passed against the actual 308,928-item local cache. Activation checks all hosted
rows before reopening access. Only the new ruleset-1 Items:FreeTrade row is added;
item definitions are retained. See ops/rollout.py and ops/test_rollout.py.
