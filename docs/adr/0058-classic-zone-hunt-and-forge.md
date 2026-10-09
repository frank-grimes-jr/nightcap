# ADR 0058: Classic zone hunt and forge

Status: accepted design; test candidate, pending gameplay acceptance. Date: 2026-10-09.

The owner approved zone-specific augments and new wearables, two independent 0.5% family chances and rarer quality tiers, with modest heroic-based cap growth and deterministic duplicate upgrades.

We use a native once-per-accepted-death award before corpse construction, with explicit high item IDs and a cached native spawn/NPC allowlist. This avoids the existing GlobalLootMultiplier=4 and legacy item-tier hook while preserving normal physical-drop IDs and advanced-loot receipts. Restored corpses and owned/script-created NPCs fail eligibility.

Type-22 sockets are limited to six armor locations. Special Spell Damage/Healing Amount cap credit comes only from these augment instances after native equip/required/recommended-level gates, aggregated before division and limited to +30 at level 50+. Raw client item totals are clamped after all equipment is counted. Existing nonplayer cap behavior is retained.

Forging shares the established inventory serializer and quarantine mechanism. It requires three exact carried copies, a single-use quote, full locked database preimages, no query retries and one transaction for consumption, output and receipt. Uncertain completion disconnects the session before stale in-memory inventory can save. Customized or socketed payloads are rejected rather than discarded.

Universal trading remains global; raw flags and instance binding are preserved. Explicit zero resale prevents these progression rewards from entering the merchant economy. Rollback disables acquisition but retains earned definitions, sockets, inventory and receipts. The alternative of deleting new IDs after player activity is rejected because it would invalidate owned items.

The eight access-check zones remain disabled, and cities/hubs remain reserved. Their item definitions do not authorize acquisition. See [release scope and QA](../releases/zone-loot-20261009/README.md).
