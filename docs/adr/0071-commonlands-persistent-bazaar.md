# 0071: Persistent player listings in East Commonlands

Date: 2026-10-24. Status: implemented candidate; activation and player QA pending.

Players need fixed-price sales without maintaining an auctioneer character.
Native trader rows are removed by trader/login/world lifecycle, and seller profile
saves can overwrite money credited remotely. Reusing either would risk lost items
or payment. NPC resale does not preserve player-set listings.

Use independent InnoDB escrow and credit tables. One transaction locks a market
state row, validates session inventory/wallet preimages, moves ownership, changes
buyer funds or seller credits and writes a receipt. No query retries. Ambiguous
outcomes quarantine/disconnect the session; reconnect loads authoritative state.
Credit collection is a separate transaction by the authenticated seller.

Reuse native bazaar search/inspect/direct purchase in public East Commonlands with
a reserved virtual broker and expiring server quotes. Cursor posting has an exact
item/price confirmation. Preserve instance metadata; reject unsupported filled
bags/evolving state. A global lock is acceptable for this small market but is an
explicit throughput limit. Prices are whole platinum, partial stack sales allowed,
100 active listings per seller, no additional fee or currency reward.

The schema starts disabled. Disabling trading leaves recovery and collection
available. Never drop escrow to roll back; drain ownership first. Full native build,
real MariaDB fault/concurrency tests and ordinary-player RoF2 QA are separate gates.
See docs/bazaar/SPEC.md and QA.md. No production deployment is authorized by this ADR.
