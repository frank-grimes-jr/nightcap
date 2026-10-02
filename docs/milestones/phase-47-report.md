# Phase 47: Spell-selection menu cache correction

Read-only inspection of the reported live client confirms three cached level-255
rows, including Elementalkin: Water. The native menu copies spell levels before
class metadata arrives and does not refresh them when the snapshot arrives.
The correction invalidates accepted snapshots and rebuilds on the next safe
native frame, refreshing both labels and ordering.

Independent native RED/GREEN reproduction, lifecycle and trampoline tests,
all five runtime checks, four loot fixtures, the full launcher suite and all
70 exact signatures pass. The signed candidate preserves the current release's
44 other files. No database, spellbook, access-policy or server-binary change
is needed. Rendered owner acceptance remains open after approved publication.

[Release evidence, recovery and exact in-game QA](../releases/spell-menu-20261002.md).
