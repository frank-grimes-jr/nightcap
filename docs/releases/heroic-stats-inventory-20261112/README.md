# Heroic stats and the Inventory attribute column

Production was checked read-only on November 12, 2026. Heroic stats are already
enabled: STR/STA/AGI/DEX/INT/WIS multipliers are 1.0, and Nightcap heroic melee
and spell scaling rules are true. `HeroicStatsUseDataBucketsToScale=false` only
disables optional additional bucket scaling; it does not disable heroics.
The optional direct heroic INT-to-Spell Damage and WIS-to-Healing Amount
multiplier rules remain zero; those are separate from existing heroic benefits
and Nightcap's earned augment cap headroom. No balance rule needs changing.

The current signed client is 2026110701. Its retained Inventory XML is the
November 6 single-Shield-Block asset. Inventory > Stats already contains native
gold/yellow heroic labels, EQTypes 251–257. The main Inventory tab has no such
labels beside STR/STA/AGI/DEX/WIS/INT/CHA. This is a display omission, not a
disabled game mechanic.

## Candidate

`tools/client_character_stats_ui.py` adds seven gold `+` signs and seven native
heroic values to the main Inventory tab. It copies the matching existing Stats
labels, retaining their native EQTypes and gold RGB 214/178/40. Existing normal
attribute labels, values, native coloring, equipment controls and every other
page remain unchanged. Totals already include heroics; the tooltip explicitly
warns against adding the yellow number a second time. No command or server poll
is introduced. Zero heroics displays +0 using the existing client behavior.

The normal generator calls this helper. `inventory_heroics_xml` also supports
an additive delta over the actual currently published XML, preserving all
existing bytes rather than regenerating from an older protected client.
`tools/stage_heroic_stats_client.py` checks the captured manifest descriptor and
all existing controls before writing the one-file candidate. Rerunning on an
already patched or incomplete input fails closed.

Source branch: `feature/heroic-stats-inventory`, based on origin/main b7e404b2.
Baseline/candidate hashes and production findings are in `verification.json`.
The candidate is in `artifacts/heroic-stats/candidate/uifiles/nightcap/equi_inventory.xml`.
It is unsigned and unpublished. No production files, rules, player records,
installed game files or protected reference-client files were changed.

## Verification and release boundary

The Inventory regression fails against the original generator and passes with
the fix. Five character UI tests, five gameplay UI tests and eleven resource
controls pass, including heroic stat/cap and base-class mana checks. Native
pixel rendering and equipment-refresh acceptance remain pending. Python test
import failures from incorrect search paths were corrected by using the owning
module's directory/PYTHONPATH; the final suites pass without test changes.

Release work must freshly verify the production channel and native pair, sign
a higher game release containing only this XML, preserve the other 147 asset
descriptors/URLs and all notes/tombstones, and use the guarded client publisher.
Run the publisher's Linux recovery tests before publication and verify the
served signed envelope/XML and retained DLL/catalog afterward. No server build,
restart, cache reload or gameplay tuning is required. Client pairing remains
the current proxy/catalog/config and all current spell/world assets.

The repository requires owner sign-off for test-to-main promotion. The initial
request authorizes this investigation and candidate; no new main promotion or
public release is claimed. Recovery after publication must use a higher signed
counter restoring the previous XML while preserving newer unrelated assets.
Never downgrade a counter or restore player snapshots.

## Exact owner in-game QA

1. After an approved signed release, fully exit EQ and use normal launcher Play.
   Use the managed Nightcap skin and open Inventory's main tab.
2. Confirm STR, STA, AGI, DEX, WIS, INT and CHA retain their existing normal
   stat coloring and each has a yellow/gold `+N` immediately beside it.
   Open Stats and compare each yellow value with the same attribute there.
3. Equip/remove owned heroic gear or a legal augment and compare both tabs.
   For example, Passwatch Flint (940032) grants heroic STR2/DEX2 and Hillside
   Dewstone (940024) grants heroic AGI1/WIS1 before eligibility/scaling. Use an
   eligible character and existing earned items; do not grant test gear to a player.
4. Confirm bagged items provide no worn bonus, and zero heroics shows +0.
   Compare the final normal total and HP/mana/endurance before/after without
   adding the displayed yellow total again. Existing stat caps and recommended
   level scaling still apply.
5. Check all seven rows, long values, Inventory resize, Stats scrolling,
   zone/relog/skin reload and an ordinary character without heroic equipment.
   Check bags, equipment drag/drop, pet armor and the single Shield Block row.

## Wiki impact

Reviewed all 42 authored articles, Home, Features, commands, launcher guidance,
catalog/item/zone projections and release labels. Equipment, Augment guide,
Features and Change Log receive the existing Stats-tab instruction and a
clearly labeled unpublished main-tab preview. Home needs no extra release
announcement; commands, acquisition, generated catalog values and gameplay
guides retain their current behavior. Public wiki publication is pending.
Global source drift stays review-required; do not advance unrelated ledger
entries or publish unrelated previews with this client-only change.
