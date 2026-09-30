# Phase 39: Advanced-loot server integration

Date: 2026-09-30. Candidate on `feature/advanced-loot`; not deployed.

## Built

Authoritative corpse queue and window protocol, persistent character filters and
settings, personal/shared decisions, native item transfer with checked inventory
placement, atomic item/coin receipts, group/raid splitting, classic-loot
coordination, and complete saved-state metadata with stable physical IDs.

The clean paired world/zone build passes with all 73 overlay hashes verified.
Protocol/policy/screen fixtures, production inventory/currency/saved-state body
fault checks, five proxy runtime tests, three Go package suites and 16 disposable
SQL checks pass. Signed QA release 2026093001 installs 23 files and starts actual
RoF2 with all 14 required features active, followed by clean owned shutdown.
No live data, server process or original client installation was changed.

## Cut

No requested core behavior was cut. The implementation retains native loot rights
and range, creates no additional personal drops, and does not alter progression.

## Shaky / incomplete

Real client rendering, quest/packet/lifecycle integration, saved-state recovery,
disconnected group leadership, isolated server startup and manual gameplay acceptance
remain gates. Fixture dependency fakes are not proof of native gameplay. Older
receipt-unaware binaries require saved-state reconciliation before rollback.

Current evidence and release gates:
[advanced-loot implementation](../releases/advanced-loot/README.md).
