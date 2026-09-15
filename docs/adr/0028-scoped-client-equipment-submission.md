# ADR 0028: Scope client equipment eligibility to submission

Date: 2026-09-15. Status: candidate; in-game acceptance pending.

RoF2 blocks off-base equipment before the server held-class check sees a move.
Globally widening item Classes alters other consumers; replacing the whole
CanUseItem result skips native restrictions.

Redirect the exact equip call into original CanUseItem under a thread-local item
scope. Its class accessor widens only nonzero masks for that item and observed
flags. SEH finally restores nested scope. Preserve original arguments and later
predicates; the server authorizes held classes plus race/deity/level/slots.

Guard by exact executable hash, both full calls and both helper prefixes. Install
the neutral accessor first and roll it back if the caller cannot install. There
are no persistent item/database changes. This is submission permission, not
client knowledge of held classes. Server rejection is expected for unheld classes.
Dynamic eligibility display, signed configuration, runtime health and release
recovery remain separate work. [Evidence](../../eq-client-dll/docs/offsets.md)
and [QA](../../eq-client-dll/docs/equipment-qa.md).
