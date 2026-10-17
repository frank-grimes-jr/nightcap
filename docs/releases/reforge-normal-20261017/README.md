# Normal items in the Reforging Box

October 17, 2026 candidate, based on origin/main `8d30ea6`. Implemented and
regression-tested; not built as a complete production zone, deployed, or accepted
in game. The owner requested that three normal items make a Polished version.
The October 12 box deliberately supported only higher tiers; its separate
`#zoneforge` path already supported three Base rewards.

## Recipe and implementation

- Exactly **3 identical eligible Normal (Base) items -> 1 Polished** in the free,
  reusable four-slot Reforging Box 900620. Leave the remaining slot empty.
- Exactly **4 Polished -> 1 Exalted**, **4 Exalted -> 1 Ascended** for ordinary
  tiered items, or **1 Ascension** for hunt rewards. Those costs are unchanged.
- Ordinary families require an existing +200000 item with the exact next-quality
  name. Hunt rewards require an explicit NextTier catalog entry and enabled hunt
  state. Dungeon rewards remain separate; no new item definitions are generated.
- Stack units count individually; charged nonstackables count as physical items.
  The result is one item (one unit when stackable). Binding remains preserved.
- Mixed items/qualities, wrong quantities, missing targets, top tiers, bags,
  augments installed in an item, dyes, ornaments, customization and evolving
  instances retain existing rejection behavior. The box remains reusable.

`common/item_upgrade_policy.h` now separates container capacity from recipe
quantity. `zone/advanced_loot_inventory.cpp` uses that quantity and accepts normal
legacy/hunt targets through the existing atomic inventory/receipt transaction.
The complete parent/child preimage, no-retry, receipt replay and quarantine guards
are retained. `zone/client_packet.cpp` and Artisan Veyra's `999820.pl` explain
three-normal/four-higher recipes. No item stat, drop rate or economic value changes.

## Verification

The changed policy test failed first at `LegacyTarget(1001) == 201001`; the actual
inventory translation-unit fixture failed at the new normal combine. Both passed
after the fix. Final checks:

- Four item-upgrade policy/package tests pass (compiled C++17 policy).
- Actual inventory translation unit passes all existing and new cases, including
  both normal families, all six transitions, wrong quantities, one/split stacks,
  charged outputs, binding, missing/cross-family targets, disabled hunt state,
  dungeon/top-tier rejection, stale preimages, replay and each SQL failure or
  exception boundary. `inventory-native.json` records the source hash and emitted
  SQL. Database, inventory and client boundaries are fakes, not live MariaDB.
- Eight zone-hunt and 25 ordinary-tradeskill tests pass. Use Python `-X utf8`
  on Windows for source files with Unicode comments. Ten Perl assertions pass.
- Independent read-only code review found no remaining blockers; `git diff
  --check` passes. A transient source-encoding edit was removed before final review.
- Maintained wiki: 14 Python content/refresh checks and 13 Node search/equipment
  checks pass. No layout or JavaScript change; no new browser acceptance claim.

Commands are the existing `tools/tests/test_item_upgrade_policy.py`,
`test_item_upgrade_package.py`, `test_advanced_loot_inventory.py --root . --output
...`, `test_zone_hunt*.py`, `test_tradeskill_*.py`, and `test_reforging_box.pl`.
Exact in-game checks are in [QA.md](QA.md).

## Build, activation and recovery boundary

Build the changed zone translation units against a fresh retained source/image
matching the current runtime, preserving the October 16 dungeon/journal and other
intervening releases. Do not reuse the October 12 builder's frozen old baseline.
Deploy the matching Veyra quest and zone together through the supported complete
runtime refresh. A quest/rule reload alone cannot activate the native recipe.
No SQL migration, feature-revision change, item/cache ABI change, new item cache
content or client download is required; retain existing enablement revision
2026101201 and the current signed client/cache pairing.

Main promotion and production restart remain subject to owner approval under
AGENTS.md. This work changes no runtime or player inventory. After activation,
rollback can restore the exact pre-change receipt-aware zone and Veyra script;
retain all earned outputs, inventory and receipts. Never restore an old player
snapshot. Three Base copies now provide an ordinary-item progression entry point;
48 eligible Base copies produce one top-tier item through 3/4/4. Balance and
actual client combine/persistence acceptance remain open.

## Whole-wiki impact review

Reviewed all 21 maintained articles plus commands, generated item/zone guidance,
catalog values and release labels in the maintained wiki checkout. Updated
item-upgrades, equipment, zone-hunt, Features, home, unreleased and Recent changes,
plus generated catalog guidance, with explicit **not released** labels. Dungeon
exclusions remain. Unaffected commands, tunnel acquisition, tradeskills, travel,
class/AA/combat/pet guides, item stats and drop rates need no content changes.

`wiki-refresh.json` records the required HEAD/include-worktree comparison: review
required, including this fix and historical source drift. The global audit ref
was deliberately not advanced; this scoped review does not certify unrelated
historical changes. `wiki.patch` and `wiki-preimages.json` retain the exact local
maintenance change. Public wiki publication is pending, not claimed.
