# Sell / My Listings: native acceptance

Candidate only. These steps require the paired zone build and proxy/catalog0.13.0,
config and Bazaar XML delivered through the launcher after the authorized combined deployment.
The existing command-only market remains live; this panel is not yet published.

## Main offline-seller test

1. Fully exit EverQuest, update with normal launcher Play, and enter public East
   Commonlands with the seller. Open Bazaar (`/bazaar`). Verify Search is the first
   tab and the familiar search/filter/results/Buy controls still work.
2. Select **Sell / My Listings**. It must load your own listings and proceeds.
   Pick up one inexpensive eligible item, enter **1** in Platinum EACH, and click
   **Post Item**. Nothing should leave your cursor yet. Check item name, quantity,
   1 platinum EACH and the total; click **Confirm Post** within 60 seconds.
3. Verify the item leaves your cursor exactly once and appears in My Listings.
   Log the seller out completely. Listings must remain available while offline.
4. Log into another character in public East Commonlands with at least1platinum
   and an empty cursor. On Search, find the exact item, inspect it, select one unit,
   and buy using direct-to-inventory delivery. Verify one item on the cursor and
   exactly1platinum deducted. A fresh search must show the remaining stock or none.
5. Log the buyer out, return to the seller and open Sell / My Listings. Verify the
   sale removed/reduced the listing and added exactly1platinum to Proceeds. Click
   **Collect Proceeds** once. Verify the balance clears and your money increases
   exactly once. Reopen/relog to check persistence.
6. Post a second inexpensive item. Clear your cursor, select its listing, click
   **Cancel Listing**, check the named confirmation, then **Confirm Cancel**.
   Verify the exact remaining item/stack returns once and the listing disappears.

## Interaction and recovery checks

- Repeat with a stack of3 at1platinum each; preview must say3total, buying one
  leaves2, and cancellation returns exactly2. Inspect supported augment/custom
  metadata before/after; use expendable items for initial QA.
- Change the price after preview: Confirm must require a fresh preview. Swap the
  cursor item: confirmation must reject without taking either item. Expired quotes
  require Post Item again. Never mind must leave ownership unchanged.
- Double-click Post, Confirm, Cancel and Collect: no duplicate movement or money.
  A filled cursor prevents cancellation/buying safely; clear it and refresh.
- Rapidly switch Search/Sell, close/reopen, resize smaller/larger, scroll, and reload
  the skin. Seller controls must remain reachable; Search controls and filtering
  must behave normally. Price Enter/right-click must not submit or change Search.
- Zone or change characters while a request is outstanding. The next panel must
  show only the new character; old selections/quotes cannot be acted upon.
- With more than8listings, Previous/Next must show distinct pages; selling/cancelling
  the last row must clamp to a valid page and clear stale confirmation.
- If a reply times out, controls must require Refresh. Refresh reads the resulting
  ownership/balance; it must never repeat the sale/cancel/collection automatically.
- Operator-only rehearsal: disabled trading prevents new posts while owned listing
  cancellation and earned-credit collection remain available. No live toggle is
  authorized by this QA document.

Report Search, inspection, posting, offline buying, cancellation and collection
separately, with character, zone, item, price, expected/actual totals and timestamp.
Native rendering/focus/skin-reload and end-to-end acceptance remain open.
