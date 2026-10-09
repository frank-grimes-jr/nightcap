# Classic hunt and forge — approved October 9, 2026

The owner approved the recommended Hunt and Forge proposal after choosing two independent 0.5% family rolls per eligible death. Each successful family roll selects Base / Polished / Exalted / Ascension at 60% / 30% / 8% / 2%. Existing named loot stays intact.

The reviewed catalog contains 81 Classic zone/hub records. Combat zones receive one augment family and one new wearable family. City and hub concepts remain reserved; access-check zones fail closed until their source/access audit passes. Version 0 only. Native spawn identity, minimum NPC level and exclusion of services, pets, scripted clones and restored corpses are mandatory.

Six armor locations (head, chest, arms, hands, legs, feet) receive one type-22 socket per eligible item, preserving existing sockets. Only approved new augment heroics contribute to level-50 output cap headroom: aggregate effective INT or WIS / 2, rounded down, at most +30. This raises a cap; it does not grant missing Spell Damage or Healing Amount. Native heroic stat effects remain.

Three identical, unequipped, unmodified copies of one family and quality forge into one next-quality copy, at no fee. No cross-family conversion or further Ascension upgrade. Exact persisted instance preimages, binding preservation, database-first atomic consumption/grant, durable audit and uncertain-commit quarantine are required.

## Integration decisions

- Start from current main 081c4d8 in an isolated feature branch; preserve advanced-loot receipts, saved-state replay protection, universal trading and passive-AA behavior.
- Universal trading already overrides raw NO TRADE/attunement for trade eligibility. Keep that policy and preserve raw instance attunement when forging. The review workbook's binding label is superseded by the current server policy.
- New custom IDs bypass the legacy loot-tier hook. A dedicated death roll bypasses GlobalLootMultiplier=4.
- Retain awarded item definitions and sockets during rollback; disable new acquisition while preserving inventory and receipts. Removing earned power after player activity requires a separately reviewed migration.
- No client binary/data edits. Source promotion follows feature → dev → test, with explicit owner in-game QA before main.

## Build slices

1. Freeze approved data and audit native sources; generate collision-guarded item/socket migrations and rollback; exercise them on an isolated database.
2. Add and test the native death reward policy and cached allowlist.
3. Add and test equipment-order-independent cap credit.
4. Add named forge choices and atomic transaction/failure handling.
5. Fresh native build, independent review, balance measurements, QA steps, release/changelog/ADR evidence and test candidate promotion.
