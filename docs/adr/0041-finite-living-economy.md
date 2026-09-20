# 0041 - Finite, restart-scoped NPC economy

Date: 2026-09-20. Status: implementation candidate; owner gameplay acceptance open.

## Decision

Keep a small, manually reviewed Classic drop catalog with dated P1999 Green
price evidence. Do not randomly expose arbitrary item-table entries. Native
city merchants show one synthetic finite listing; ten new East Commonlands
NPCs provide six WTS and four WTB offers. The world startup rotates a durable
generation once. Zone boots, respawns, shop opens and quest reloads do not restock.
Auctions use the actual auction channel and occasional nearby say chatter.

Scale reference prices by the observed earning changes before premiums:
`4 * (2.5 / 0.95)` estimates increased item-drop resale income. It is not a raw
coin multiplier. Seller premium is 20%; finds use 10% with native-price/resale
floors. Buyers pay 70% of the scaled reference, never the seller premium.
This provisional spread avoids creating a buy/sell profit route. The owner
can choose the narrower vendor-payout-only basis in the policy before release.

Use one native InnoDB transaction for stock, wallet, cursor item and audit.
Lock the market generation first, compare persisted wallet/item preimages,
and never retry a mutation automatically. An uncertain commit disconnects and
quarantines the client until authoritative state reloads. Perl is only an
adapter: it neither moves money nor creates/deletes purchased items.

## Alternatives

- Temporary native merchant stock is simpler, but cannot reliably preserve
  restart-only quantity, independent pricing and shared state across zone boots.
- Quest-only money/item calls are smaller, but separate saves introduce crash
  windows between payment, delivery and stock consumption.
- Unbounded NPC buyers create a repeatable currency source. A finite demand
  budget, spread, trade log and exclusion of permanent merchant stock constrain it.

## Consequences

Deploy matching world/zone binaries, schema, plugin and quest adapters together.
No client patch is needed. Earnings-rule drift fails closed until repriced.
The current catalog has five lower-tier finds and seven tunnel items; future
expansion additions need fresh provenance and prices, not just a higher era rule.
Player-earned items and wallets survive rollback. Manual client UI, economic
balance and recovery QA remain release gates even after automated checks pass.
