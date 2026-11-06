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

## Verified release

Main PR412/91b992d9c2cb3f13eef3c419633fb109d440da4c is published as signed
2026110603/proxy0.13.4. All148HTTPS assets/300620951bytes, shipped-key
signature, history and retained DLL/catalog pair verify. Only Inventory XML changed;
147other descriptors/URLs retained. All five service identities/starts/restarts
are unchanged.20Linux publisher fault tests passed. Wiki20261106-character-stats-font-v1
verifies510files/503HTML routes, rollback/private downloads/service preservation;
505files preserved. Main plus recorded overrides reproduces79inputs/510outputs.
The inherited global wiki source drift remains review-required, not blanket approved.

Owner reports Stats functioning in their screenshot. The revised font/row sizing,
scrolling/resize and broader lifecycle/gameplay checks remain open. Full EQ exit/
launcher Play loads the new XML; no native server restart or DLL replacement.
