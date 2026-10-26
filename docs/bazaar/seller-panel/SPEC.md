# Bazaar Sell / My Listings panel

Requested October26: native controls inside Bazaar Search for posting a cursor
item, viewing/cancelling owned listings and collecting offline proceeds. Search
and native purchase remain available. Existing command fallback and transactional
escrow rules remain; no schema, item-power, price-policy or ownership changes.

Flow: Sell / My Listings opens a paged list (eight rows,100maximum). A whole-
platinum price field and Post Item request a server quote for the exact cursor
instance. The preview shows item, quantity, price EACH and total; Confirm Post
commits the existing60second nonce. Changing the cursor invalidates confirmation.
Cancel Listing requires selecting and confirming the exact visible listing.
Collect shows the authoritative balance, including fractional-platinum remainder.
All actions disable while awaiting acknowledgement. Timeout allows a fresh read,
never automatic mutation replay. Closing/reloading/zoning clears local selection,
confirmation and outstanding replies; server identity and ownership remain decisive.

Transport: dedicated opt-in #bazaar ui requests over the existing silent native
channel sender. Bounded [NCBZ1] begin/quote/rows/status/end snapshots correlate a
request ID and character spawn/name. Partial, duplicate, malformed and stale batches
cannot enable actions. Server results are escaped plain text, never commands.
Server independently validates all numbers, context, quote and owned listing IDs;
client presentation is not an authorization boundary. Only this character's rows
and proceeds are sent. Disabled trading still permits cancellation and collection.

Implementation slices:
1. Shared bounded protocol/parser and request-state tests.
2. Server read/quote/action adapter reusing escrow, with native/disposable DB tests.
3. Generated Bazaar SIDL panel, exact-client notify/frame hooks, native UI/controller
   tests and x86 build. Signed catalog/config and client assets must match.
4. Full zone build, independent correctness/security review, wiki impact review,
   CHANGES/status and installed Nightcap references/fingerprints.

Current baseline:main465003f6, deployed zone84b6b9ff and signed proxy0.12.0.
No deployment permission is inferred from the earlier command-only release.
Prepare a paired release and explicit in-game QA before any new production action.
Actual native rendering, input and completed offline-seller purchase remain separate
acceptance gates. Never modify the protected reference client or restore player data.
