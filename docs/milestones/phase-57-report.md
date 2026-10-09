# Phase 57: Advanced loot row controls

Date: 2026-10-09

Built: direct mutually exclusive Always Loot/Never Loot row toggles, returning
to Ask on a second click, and closing an exhausted loot queue only after a
complete server snapshot. Preserve Settings, Filters, explicit empty opens,
server authority and existing NO TRADE handling. Native controller regressions,
layout tests and the x86 DLL build pass.

Cut: no new server/protocol/database state, automatic loot permission changes,
native checkbox memory offsets, or additional configuration page.

Shaky/open: paired signed-client delivery and actual RoF2 rendering, persistence
and award acceptance. This candidate is not deployed. Source and exact QA:
[row-control release notes](../releases/advanced-loot/ROW-CONTROLS.md).
