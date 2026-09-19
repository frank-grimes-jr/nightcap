# Phase 25 — Repair native skin rejection

Owner gameplay evidence exposed a gap in phase 24 verification: the client could
initialize every native hook yet reject the UI assets and use Default. The old
ElementTree output changed the literal schema syntax required by RoF2.

The repair preserves the exact Schema declarations, adds a failing-then-passing
regression test, and rejects the old representation during signed packaging.
Independent native-parser and stock-schema review found no additional concrete
rejection causes. Both Go suites, all four UI tests and the launcher build pass.
Signed release 2026091905 replaced the old launcher at the usual path after the
owner closed both apps. Installation and startup on the separate QA copy passed
with proxy 0.4.1 and all 12 features active, followed by clean owned shutdown.
Original-client installation awaits the explicit protected-folder override;
native character login/UI loading remains unverified.

The missing AA names are a separate pre-existing catalog gap: even the database's
ability names are placeholders. No AA flags, ownership, points, server binaries
or database content changed. [Evidence, delivery and exact QA](../releases/client-skin-repair-20260919.md).

Future UI release evidence must include native character loading, not only
well-formed XML and successful hook initialization. Keep the owner's existing
launcher path current; multiple offline launchers can otherwise install different
embedded releases despite sharing the same visible application name.
