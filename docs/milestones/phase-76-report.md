# Commonlands bazaar candidate

Date: 2026-10-26. Candidate only; not deployed or accepted in game.

Built: transactional item escrow, persistent listings, offline credits, native
Commonlands search/inspect/buy, cursor posting confirmation, cancellation and
collection. Rebased onto current main/coordinated v2. Real database tests, native
metadata/packet guards and wiki checks pass; full native build remains in progress.

Restricted: filled bags, temporary/evolving/scaling items, legacy metadata that
cannot roundtrip native loading, and stacks using the unlimited-charge sentinel.
These are rejected before ownership moves. Normal player trade remains unchanged.

Open: full build, RoF2 visible search and zero-voucher direct delivery, ordinary
player offline/restart QA, branch promotion approval and authorized activation.
Exact evidence, operations and QA are in docs/bazaar/. Wiki changes remain labeled
Not released. No live state, client or public wiki was changed.
