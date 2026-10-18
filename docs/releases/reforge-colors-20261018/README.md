# Reforging default colors — October 18, 2026

Status: implementation and verification in progress; not yet deployed.

The owner requested correction and production deployment after three ordinary
Daggers of Marnek were rejected. Their instance color matched the item definition
(`0xff000000`); item 13169 has a valid Polished target 213169 and no instance
augments, ornaments or custom data were present. Private character data is not
included in this release evidence.

## Contract and implementation

`PlainUpgradeItem` and the equivalent `PlainForgeItem` check accept zero (the
existing no-tint representation) or the source definition's exact color. Any
different nonzero color remains customization. Native `ItemInstance` constructors
initialize from `ItemData::Color`; the inventory loader uses the definition color
when a saved row is zero. No color is stripped or rewritten on input items.

The output uses its own target definition's color. Quantities, eligibility,
binding, augments, ornaments, evolving items, saved preimages, atomic receipts,
rollback and uncertain-result quarantine remain unchanged. No item SQL, schema,
catalog, ItemData layout, client asset or game balance change is required.

Files: `server-mods/code/zone/advanced_loot_inventory.cpp` and
`tools/tests/advanced_loot_inventory_fixture.cpp`. The failure-injection harness
executes the complete production translation unit with dependency fakes.

## Verification and release plan

1. Reproduce before editing: the new harness failed with
   `default/no-tint color rejected by box` against the unchanged implementation.
2. Run the inventory suite and upgrade policy/package controls. Added 61 cases
   span all six box input tiers, zero and nonzero definition colors, genuine dye,
   output color/binding/receipt preservation, zoneforge and saved-color drift.
3. Authenticate the retained cooldown release source and all link inputs.
   Re-link the baseline byte-identically before compiling the single changed
   implementation file and linking a new zone. No header or ABI changes.
4. Independently review the fix, test coverage, build provenance and operator.
5. Wait for the concurrent cooldown release to finish. Preflight must require
   its exact deployed baseline, current client, cache, quests and runtime.
6. Acquire the shared deployment/GM locks, take a fresh stopped backup, deploy
   a zone-only immutable image and verify with access held closed. Preserve
   player state, receipt/timer tables, content, cache and supporting services.
7. Reopen access only after checks pass. Record deployment and public wiki
   publication separately from owner gameplay acceptance.

The owner explicitly requested this deployment. It requires the supported
whole-runtime restart; a quest reload cannot change this native check. Keep the
latest signed client and cooldown migration. Recovery selects the immediately
preceding cooldown-capable image, preserving current inventory and receipts;
never restore an old player snapshot or the pre-cooldown binary.

## In-game QA

On Palwar, place exactly three Normal Daggers of Marnek in the Reforging Box,
leave one slot empty, close other interactions, disable auto-attack and Combine.
Expect exactly one Dagger of Marnek (Polished) inside the reusable box. Reopen the
box and relog: the upgraded item remains and the three inputs do not return.
Also verify a genuinely dyed eligible item is refused without consuming copies,
and an augmented/ornamented item remains refused. Owner acceptance is pending.
