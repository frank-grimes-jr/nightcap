# ADR 0028: Scope client equipment eligibility to submission

Date: 2026-09-15. Status: candidate; in-game acceptance pending.

October 15 update: the all-class bypass below is superseded by the
[held-class correction](../releases/multiclass-equipment-20261015/README.md).
Native CanEquipItem also drives inspection colors, so the scoped accessor now
projects only currently held classes. Cursor placement and direct inspection
share this policy while keeping canonical scroll handling. Item/thread scope
and native non-class checks remain. This update is a tested, unpublished candidate.

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
