# Server-backed character Stats tab

Owner: add Shield Block and other missing bonuses directly to the character
Stats window, without requiring #augstats. Extend the existing Inventory Stats
tab; retain ordinary stats, inventory/pet tabs, item descriptions and gameplay.

Add Shield Block with strongest-Hunt contribution, relative Dodge modifier,
best worn item spell-haste/mana-preservation potential and worn Faerune status.
Focus rows explicitly show potential before spell limits, not a guaranteed
modifier on every spell. Replace stock mod totals/caps with calculated server
values, including750base damage/healing caps and earned headroom.

Plan: a bounded numeric presentation snapshot bound to the existing UI identity,
sent only on a silent self-only request and throttled server-side; client polling
while custom labels render, identity reset/replay/expiry guards and no stale
cross-character values. Add a scrollable Additional bonuses section to the
existing Stats page and preserve its ordinary two-column layout. Use existing
label/request hooks, with no new native executable patch offsets or gameplay
authorization. Keep #augstats as a diagnostic fallback.

Verify protocol extremes/malformed/stale/replay frames, exact XML layout and
unrelated-control preservation, actual server collection with bag/training/
shield/duplicate controls, real label hooks, native compile/link against the
current3fc2b901baseline, signed client pairing and hosted/public wiki delivery.
Protected client remains read-only. New UI pixel/scroll/resize and actual
equipment/buff/zone/class refresh acceptance remains owner in-game QA.

## Verification and release boundary

Protocol/cache, real server collection, exact native label/chat/state hooks and
XML-preservation regressions pass. The focus fixture covers passive cast level60
on a level50 character: cast level is not an equip requirement. Bagged, wrong-class,
required-level and ordinary slot21 training items are excluded. Real label hooks
cover silent throttled transport, stale identity/generation rejection, placeholders,
stock labels and ordinary chat forwarding. Existing Description passes25 checks.
Fourteen focused native/runtime groups pass; all runtime test executables build
with /W4 /WX. Existing UI and #augstats regressions pass.24 Linux operator/publisher
fault tests pass. Native pixels and actual client/server round trip await owner QA.

Quiet polling retains command permission checks but bypasses quest GM-command
callbacks and persistent command logs. The self-only read-only capture makes no
DB query. Server refresh is at most every3seconds using the existing class-UI timer;
rendered custom labels request at most once/second. Identity is generation,
character/zone/instance/spawn; sequence rejects replay,8second expiry avoids stale
values. No Client fields/vtable, ItemData, rules, cache or player-data change.

The native build reproduces3fc2b901 byte-for-byte from144 authenticated link inputs
before replacing unity_1 only. Candidate ea6ad532 retains compatible world and
shared_memory. Focus rows show best worn-item potential before spell limits;
buffs/AAs may change a cast. Worn Faerune means item utility, not all spell buffs.

Signed2026110602/0.13.4 is a candidate: DLL, paired catalog and Inventory XML change,
145other asset descriptors/URLs retained,148 total. Cast-bar/recall repairs remain.
Deploy native first with supported whole-runtime restart, stopped backup, saved
state and held compatible rollback; never kill one production zone or restore
old player data. Publish client after verified opening. Wiki uses exact public
510-file source; unrelated main previews stay unpublished. Actual receipts establish
live state. Full EQ exit/launcher Play required; no protected-client writes.

## Exact in-game QA

Fully EXIT EQ/use launcher Play. Open Palwar's Inventory -> Stats. At normal and
resized dimensions, ordinary rows stay readable in two columns; Shield Block/Hunt
appear by Shielding and Dodge by Avoidance. Scroll to focus/Faerune. No raw frames,
command echo or NPC interactions should appear. Heal Amount and Spell Damage
show server caps/headroom rather than stock250. Tooltips explain relative Dodge
and item focus potential before spell limits.

In The Hole, compare Exalted Understone Heart940282 loose, socketed into eligible
worn armor with usable shield, shield removed and restored. Hunt should show
0/+1/0/+1 within about3seconds; Shielding stays separate. A second Exalted stays+1;
Ascension gives+2. Check required level/class and training-slot exclusions. Numeric
copies still add within real caps. Compare #augstats as a diagnostic control.
Equip/remove Improved Dodge I, haste/mana focus and Faerune; same copies must not
multiply. Zone, class change and character switch must not carry old totals.
Missing/stale data shows --. Check ordinary inventory, pets, AA/class labels and
item descriptions (now pointing to Inventory Stats). Owner native sizing/scroll/
refresh/gameplay acceptance remains pending; automated tests do not establish it.

## Review

Reviewed correctness, readability, authority boundaries, bounded collection,
replay/expiry, focus limits, actual caps, native ABI and operational recovery.
Quiet-poll logging and cross-character placeholders were corrected before packaging;
server3second throttle retained. No unresolved merge blocker. This is self-review;
no independent agent review is claimed. No gameplay power or loot tuning.
