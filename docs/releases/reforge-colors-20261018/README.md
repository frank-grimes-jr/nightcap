# Reforging default colors — October 18, 2026

Status: deployed October 18; access open and automated verification passed. Owner in-game acceptance remains pending.

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

The operator validates the market rotation against its actual retained procedure:
exhausted eligible pools can leave empty slots. Counts must stay within actor and
scarcity capacities, with every present offer satisfying epoch, price, quantity
and eligibility checks. The operator passed twelve test groups on
Windows and Linux before deployment; it does not change market behavior.

The first preflight stopped before creating evidence or changing service state:
BuildKit interpreted a bare local image ID in `FROM` as a registry name. The
corrected build creates a release-local tag from the authenticated image ID and
verifies it before and after building with pulls disabled. Full binary hashes and
one-layer ancestry still verify against the immutable baseline. Three regression
groups cover successful construction and tag drift before/during the build.

## Production verification

PR225 contains the native fix; PR227/228 contain the reviewed operator repairs.
The coordinated rollout used the completed cooldown image and preserved its
migration, saved deadlines and signed client2026101801. All twelve running zone
processes match the new binary, with zero container restarts or detected native,
quest or SQL errors. A fresh stopped database backup passed gzip verification;
no player snapshot or timer migration was restored/replayed.

The closed-access checks preserved 47 player tables, 28 custom/timer
tables, content, item cache, quests, public downloads and supporting services.
The existing market startup procedure rotated exactly once, from epoch82
to83, with42 valid offers within capacity44. Access reopened
only after preservation and health checks passed. Exact receipts are in
`production-verification.json`, `backup.json` and `stage-manifest.json`.

Wiki `20261018-reforge-colors-v1` is published, retaining the reviewed
cooldown/travel additions from main47c9e87 and adding default-color guidance.
All465 public hashes/security headers and five private-source denials verify.
The guarded origin update rehearsed rollback and preserved private downloads,
configuration and all five service identities. Thirty Linux wiki tests, fourteen
Windows content/refresh tests and thirteen Node checks passed. Publication
receipts are separate from owner gameplay acceptance. The public verifier uses
the established NightcapLauncher user-agent; the generic Python agent received
HTTP403. No access or Cloudflare configuration was changed.

## In-game QA

On Palwar, place exactly three Normal Daggers of Marnek in the Reforging Box,
leave one slot empty, close other interactions, disable auto-attack and Combine.
Expect exactly one Dagger of Marnek (Polished) inside the reusable box. Reopen the
box and relog: the upgraded item remains and the three inputs do not return.
Also verify a genuinely dyed eligible item is refused without consuming copies,
and an augmented/ornamented item remains refused. Owner acceptance is pending.
