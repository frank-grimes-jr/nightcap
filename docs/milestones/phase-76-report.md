# Commonlands bazaar — live testing

Date:2026-10-26. Owner-approved main PR339/29e4e84b and live deployment verified.
Built: transactional item escrow, persistent listings, offline credits, native
Commonlands search/inspect/buy, cursor posting confirmation, cancellation and
collection. Full native build/source hashes,22database tests and2native groups pass.
Restricted: filled bags, temporary/evolving/scaling items, legacy metadata that
cannot roundtrip loading, and stacks using the unlimited-charge sentinel.
These are rejected before ownership moves; ordinary player trade is unchanged.

Deployment: all12workers,51schema/565content predicates,97state-table preservation
and170existing command permissions pass. Gateway open, zero detected native/quest/
database errors, fresh stopped backup verified. Initial disk-reserve failure was
resolved by exact task-cache reclamation and a reviewed preflight continuation;
no migration replay or database restore.28operator tests plus6continuation fault
tests and independent review pass. Retained world/cache/client remain unchanged.

Wiki:20261026-commonlands-bazaar-v1 publishes coordinated High Keep/Ashen content
and bazaar live-testing guidance, preserving Rogue tome content.499public files,
security headers and five private denials verify;16Linux publisher tests and
rollback rehearsal pass.19content/refresh tests pass; global source drift remains
explicitly reviewed rather than blindly advancing its ledger.

Open: native RoF2 search/inspect/zero-voucher direct buying and full ordinary-player
posting/offline/proceeds/cancellation/restart acceptance. Owner will test later.
Evidence, operations, recovery and exact QA:docs/bazaar/.
