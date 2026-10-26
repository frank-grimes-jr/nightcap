# East Commonlands persistent bazaar

Status: implementation in progress; not deployed. Source starts at origin/main ddd16e02 on feature/commonlands-bazaar. A separate October 24 coordinated release is in progress; reconcile its actual final source before any native release.

## Required result

Players in East Commonlands (zone 22) can use the native `/bazaar` search and buy window. A character can post an inventory item at a fixed platinum price without entering trader mode, owning a trader satchel, parking a character, or remaining online. Listings survive zoning, logout and runtime restart. Sellers can inspect their listings, cancel unsold items and collect earned proceeds. Buyers receive the exact item instance, including stack charges, augments, custom data, attunement persistence and ornaments. Existing effective FreeTrade/LORE policy applies; do not replace an instance with a newly summoned base item. No added item power, generated stock, currency subsidy or NPC market rotation is involved.

Use native search results and server-authoritative purchase handling. Add `#bazaar post <unit-price-pp>`, `#bazaar listings`, `#bazaar cancel <listing-id>` and `#bazaar collect`; `#bazaar confirm <nonce>` commits a posting quote. Native `/bazaar` opens search; no client command alias is included. Post from the cursor, with an explicit quoted item/quantity/price confirmation before committing. The player can keep adventuring after confirmation. Search/inspect must accurately represent quantities and augmented instances. Preserve native filters, stale-result rejection and clear errors.

## Ownership and failure contract

Independent escrow tables own posted items. Never insert them into `trader`: native trader shutdown/login and world startup clean that table. A posting moves the complete persisted cursor tree into escrow atomically with its listing receipt. An active listing is the sole owner; sold/cancelled escrow snapshots are retained as audit data, not spendable inventory. Purchase commits item delivery, buyer debit, listing consumption, seller credit and receipt in one InnoDB transaction. Seller credits live outside character_currency until collection, avoiding online profile saves overwriting a remote payment. Cancellation and collection require the authenticated character's identity. Never accept a seller ID from a client request.

Compare locked database inventory/wallet preimages with the requesting session. Runtime GUIDs are regenerated on login: preserve the saved GUID while comparing all other durable item fields. Reject nonempty cursor queues/destinations and unsupported instance state explicitly, never silently strip it. Partial stacks and empty bags are supported. Filled bags and evolving/scaling instances are explicitly rejected; posting their contents separately remains possible. Temporary NORENT items are rejected. Every post must also roundtrip the native item loader before escrow removal. Legacy multi-key custom-data encoding currently fails that test; those items remain with the seller and are not silently normalized. This is a documented launch restriction, not evidence of support for those ownership trees. Every query disables automatic retry; no mutation may continue after a failed statement. Uncertain commit/rollback closes and quarantines the session before any stale profile save. Reconnect reads committed state; no snapshot restore and no blind replay.

A small-server global bazaar state-row lock orders all mutations initially. This intentionally trades throughput for simple cross-zone buyer/cancel/collection ordering. IDs are bounded to native wire widths; price arithmetic uses checked 64-bit copper. Migration starts disabled. Disabling new posts/purchases preserves cancellation, recovery and earned credits. Rollback never drops owned escrow or receipts.

## Implementation sequence and proof

1. Transaction engine and additive schema: real disposable MariaDB tests for post, offline purchase, cancel, collect, competing buyers, stale wallets/items, overflow, missing rows, disabled state, and uncertain acknowledgments. Compile the actual C++ engine, not a Python reimplementation.
2. Native client adapter and command registration: exact instance reconstruction, request/confirmation binding, current session restrictions and failure quarantine. Verify actual native methods and full zone build against the retained current release lineage.
3. Native bazaar search/inspect/buy integration in East Commonlands: preserve filters and item IDs, bound packet sizes, reject forged/stale quotes; inspect RoF2 wire encoding. Verify whether native command/client gates require a paired signed DLL/catalog update.
4. Independent review; feature -> dev -> test with exact in-game QA. Update CHANGES/status, installed knowledge/fingerprints and current wiki candidate. Main/live activation requires the branch-policy approval, then a fresh backup and guarded pairing, followed by actual player acceptance.

## Alternatives considered

Stationary/offline trader mode preserves a dedicated auctioneer character and fails the requested behavior. NPC resale does not provide persistent player-set listings. Dedicated escrow supports the requested ownership and offline lifecycle and keeps existing finite NPC economy separate.
