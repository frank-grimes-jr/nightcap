# Inventory combat stats, caps and heroic totals

The owner explicitly authorized the screenshot layout and live-testing publication.
Exact acceptance criteria and combat/stat sources are in SPEC.md. The November12
read-only probe confirmed heroic mechanics already active; this release changes
the display and read-only stat delivery, with no balance, item or player edits.

The frozen reviewed source/evidence snapshot is commit `b70292be` at
`E:/EQ_Local_Dev/_worktrees/inventory-published-20261112`. Later integrated main
also contains a separate raid-augment candidate. That later source is not proof
of what this Inventory release deployed; retain the native build and paired
receipts below. Installed skill fingerprints route to the frozen snapshot rather
than blindly accepting subsequent changes to the same headers.

## Reviewed implementation and current release state

Main Inventory shows HP/MP/endurance, AC/MIT/AVD/ATK/DMG/HEAL, XP/AA XP, attributes,
resists and weight. Attributes use green current, white /actual cap and gold signed
heroics. The actual cap includes heroic allowance; heroics are a component already
included in totals. AC retains the conventional native display. MIT is the cached
combat mitigation AC; AVD is total server defense, not item mod2 Avoidance. Auto
preserves the automatic-avoidance sentinel. Ratings are not percentages or DPS.

The panel/window widen40px and extend56px, keeping normal fonts and scroll access.
Equipment/bag/button behavior and other tabs remain. The normal generator and
scoped transform use tools/client_inventory_summary_ui.py. It modifies only the
owning current Inventory controls, preserving unrelated signed XML bytes.

NCST1 and its33fields remain unchanged. Only the negotiated inventory subcommand
sends NCIV1; old clients continue stats without new frames. Identity, sequence,
8second freshness, one/sec client and3sec server throttle, silent chat and state
clearing remain. Client::RefreshEquippedStats gains only a nonvirtual parameter;
no Client member/vtable/ItemData/cache layout changes. Source-only patch applies
to retained deployed source, excluding unrelated unshipped title gameplay.

Current DoT zone7b61b5ac reproduces byte-for-byte before compiling the two affected
retained command unity units. Candidate zoneb737e641 preserves world95fc228a,
shared_memoryb60c4dfc, Quick Buff, Imitate Death, DoT ticks and all current content.
Signed client2026111202/proxy0.13.6 changes DLL/catalog/Inventory XML only;145other
descriptors/URLs, Quick Buff strings, history/tombstones and config remain.
Paired native/client release is deployed for live testing. Admissions are open;
all12zone workers, native pair, stopped backup and preservation checks verify.
All148canonical HTTPS client assets/signature and all614wiki hashes/headers verify.
Owner visible acceptance remains OPEN.

## Checks and rollout

16focused native/protocol/XML checks,11DLL runtime groups,120exact-client guards,
9new rollout gates and9retained operator fault checks pass. The Windows publisher
suite passes16with5POSIX-only skips; all21pass on Linux before preflight.
Independent reviews resolved alignment, retained-string verification, exact hosted
receipt binding and standalone publisher bypass. Owner declined extra cross-model.
The public wiki's614files reproduce exactly; only four guides/history plus search
change,609files remain.20wiki tests pass; unrelated refresh drift stays explicit.

rollout.py inherits the current one-shot operator's deploy/GM locks, zero players,
125second closed admission drain, clean whole-runtime stop, stopped full backup,
saved-state boot model, one market rotation and preservation/failure-hold gates.
Do not kill a single production zone or replay terminal actions. Native activation
keeps admissions closed; publish-client is the only permitted publication path.
Verify the exact hosted signature/channel/assets before open. Private signing
seed never leaves the local machine. Observed publication receipts are native-deployment.json, client-publication.json,
client-public-verification.json and wiki-public-{publication,verification}.json.
Publication is not owner visual/player acceptance.

The immutable native stage's `client_channel_sha256` is the prepublication
2026111201 baseline. Its `files['client/channel.json']` and the
`evidence/activation/paired-deployed.json` receipt own the current2026111202 hash.
Inherited Quick Buff console labels and its intermediate `deployed.json` are not
the Inventory pair's authority. Future wrappers must use the paired receipt and
current source manifests rather than treating that baseline field as live state.

Recovery uses current player state and a fresh guarded prior-image transition;
never restore an old player snapshot. Client recovery needs a higher signed
counter restoring the prior matching assets while retaining newer unrelated files.

## Exact owner in-game QA

1. After publication, fully exit EQ and use normal launcher Play. Open main
   Inventory with the managed Nightcap skin. Confirm combat rows appear above XP
   and the seven attributes, using the normal font without clipping or overlap.
2. Confirm green current / white cap / yellow signed heroic for STR/STA/AGI/DEX/
   WIS/INT/CHA. +0 is legitimate with no heroics. The actual cap includes heroic
   allowance, unlike a base-only cap: never add the yellow component again.
3. With owned eligible gear, equip/remove a heroic item or legal augment, change
   shield and apply/remove ordinary stat/defense buffs. Values should update within
   the existing throttle. Bagged and training items must not supply worn bonuses.
4. MIT is the current server mitigation rating; AVD is its complete hit-check
   defense rating, separate from item Avoidance/Dodge/Shield Block. Auto denotes
   the existing automatic-avoidance effect; it is not guaranteed against every
   attack rule. DMG/HEAL are capped stat bonuses, not actual cast amounts.
5. Check ordinary and large values, low/high/zero heroics, XP/AA bars, weight,
   scroll access with saved window sizes, bags, gear drag/drop and all bottom
   buttons. Other Stats/Pet Armor/AA tabs and the single Shield Block total remain.
6. Zone, relog, change character and reload the skin. Old values must expire to
   -- while refreshing; no internal frames, target-NPC callback or log spam.

Visible player/native acceptance and broader combined-build balance remain OPEN.
