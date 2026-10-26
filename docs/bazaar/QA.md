# Commonlands bazaar: in-game acceptance

Deployed October26 with owner approval; access is open. RoF2 UI and complete
seller/buyer acceptance remain unverified. Owner will test later.
Use two ordinary test characters with backed-up/reconcilable test stock and money.
Run on the paired deployed server/schema in public East Commonlands (zone 22,
instance 0), with the currently signed RoF2 client. A GM-only result is insufficient.

1. Seller: put one inexpensive permanent tradable item on an otherwise empty
   cursor. Run `#bazaar post 10`. Verify exact name, quantity, 10 platinum EACH,
   total and confirmation nonce. Change the cursor item: confirmation must reject.
   Obtain a new quote and confirm within 60 seconds. Item leaves the cursor once.
   `#bazaar listings` shows its ID, name, count and price. Never enter trader mode.
2. Buyer: `/bazaar` opens the native search window in East Commonlands. Search
   by item name and test price/type/class/race filters, including race-unrestricted
   Nightcap gear. Inspect the result: augments, ornaments, color and charges agree
   with the original instance. Verify the Commonlands market broker is listed.
3. Seller logs out. Buyer with empty cursor chooses direct-to-inventory delivery,
   buys the item for the shown unit price, and receives exactly one instance on
   the cursor. Money falls by exactly 10 platinum, with no delivery fee. Relog the
   buyer; item and money remain. Search again: the sold listing is absent.
4. Seller returns and collects proceeds with `#bazaar collect`. Exactly 10 platinum
   becomes carried money. Repeated collection grants nothing. Relog: balance stays.
5. Post a stack of 10 at 2 platinum each. Buy 3, refresh and inspect: remaining 7.
   A second buyer buys the remainder. Seller gets exactly 20 platinum total.
   A charged nonstack item sells as one item retaining its original charges.
6. Seller posts, zones out, adventures and relogs; listings remain. After a planned
   isolated-runtime restart, repeat search, purchase and collection. Do not kill a
   production zone: its supervisor restarts the complete runtime.
7. Cancel a partially sold listing with an empty cursor: return only remaining
   stock, retain earned proceeds, remove it from search. Another character cannot
   cancel it. Cancellation and collection still work with new trading disabled.
8. Two buyers attempt the last unit simultaneously; only one pays and receives it.
   Compete cancellation against buying: one ownership outcome only. Repeating an
   old purchase, changing price/count/item, or using an expired search must reject.
9. Reject posting a filled bag, evolving/scaling or temporary item; an empty bag
   succeeds. Reject purchase with a nonempty cursor, insufficient funds, own listing,
   combat/trade/casting or incompatible LORE under active policy. Preserve stock
   and money. Test tradeability changes: purchase refuses; owner cancellation can
   still recover an otherwise valid item. Show a clear unsupported-delivery message.
10. Leave East Commonlands or enter an instance: posting/buying must refuse; normal
    existing Bazaar behavior elsewhere remains unchanged. Test 100-listing cap,
    expired posting quote, wallet-cap partial collection and active disabled flag.

Record client/catalog versions, native/schema hashes, listing IDs, before/after
item fields, wallet and credit totals, timestamps and each result. Keep private
account/character identifiers out of public wiki output. Screenshots of actual
search/inspect/direct delivery are required for visible-client acceptance. If the
client disables direct delivery outside Bazaar, keep activation disabled and
implement/verify the needed paired client change; server tests do not waive this.
