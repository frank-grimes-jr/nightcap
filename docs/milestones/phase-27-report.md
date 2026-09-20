# Phase 27: class pet roster and tunnel assessment

September 19, 2026.

Implemented original-class summon ownership, one pet per held class, shared
native pet commands, per-class armor assignment, native window representative
selection, transactional roster persistence and class-aware suspension.
Death, reclaim, familiar fade and committed class release use the same roster.

The build, 36 native permutations, eight attack/range cases, four migration
cases, isolated save-failure rollback, ownership/armor tests and independent
review passed. Final-candidate smoke and failure checks passed after the legacy
suspension fix. [Evidence and exact manual QA](../releases/multiclass-pets-20260919/README.md).

The East Commonlands tunnel assessment includes map geometry, existing props,
16 spaced merchants and a ten-stone travel proposal. It identifies client model,
door asset, quest, saved-state and return-route work needed before moving the
hub. [Proposal](../pok/ecommons-tunnel-proposal.md). No hub migration was applied.

Not claimed: in-game visual acceptance, complete death/zoning/client interaction
QA, or encounter balance with three pets. The release stays at the test gate
until owner sign-off. The earlier silent UI package remains unchanged.

The candidate is active on the development server after graceful shutdown and
a verified full backup. World and all eight zone hashes match, 17 source files
match, required rules and PoK stock are intact, and the 14 checked startup logs
contain no Error/Fatal lines. [Activation and recovery](../releases/multiclass-pets-20260919/ACTIVATION.md).
