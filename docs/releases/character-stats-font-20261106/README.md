# Character Stats font and Hunt label

Owner confirms the new Stats view functions, but the supplied screenshot shows
smaller added rows. Existing stat labels omit Font and inherit the normal UI
font; new NCST labels incorrectly pinned Font2. Inherit the native IWS_Shielding
font and14pixel row height; widen values to75px, matching ordinary total widths.
Rename Hunt contribution to Hunt aug block. It is already included in total
Shield Block; max means strongest Hunt bonus, not a second additive bonus.

Scope: one signed Inventory XML replacement,2026110603, existing proxy0.13.4.
All147other asset descriptors/URLs, DLL/catalog, spell data and rules remain.
No server build/restart, native change, player write or protected-client write.
Audit proves exactly15NCST labels changed and every other control is preserved.
Two existing Stats UI and five gameplay UI tests pass; signature/exact-client
preflight and unchanged proxy/catalog pairing pass. POSIX publisher fault tests
run before publication. Candidate until hosted verification receipts exist.

Native QA: fully exit EQ/use launcher Play. Open Inventory -> Stats. Compare
Shield Block/Hunt aug block/Dodge labels and values to Shielding/Avoidance; font
and row alignment should match. Values and long focus labels must fit when
scrolled/resized. Confirm the Hunt row is included in total Shield Block and two
+1% copies still give+1%. Owner function report is accepted evidence for this
view, not acceptance of every zone/class lifecycle or the revised font pixels.

Wiki impact: all generated item/zone/catalog values, Home, navigation and assets
are unchanged. Update owning guide labels/stacking explanation, Features and
Change Log together over the exact current510-file public source; preserve
unrelated main-only previews. Native functional report and revised font QA are
recorded separately. Recovery uses a newly signed higher counter with prior XML,
current matching DLL/catalog and all retained assets; never lower the counter.
