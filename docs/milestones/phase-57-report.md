# Phase 57: Advanced loot row controls

Date: 2026-10-09

Built: direct mutually exclusive Always Loot/Never Loot row toggles, returning
to Ask on a second click, and closing an exhausted loot queue only after a
complete server snapshot. Preserve Settings, Filters, explicit empty opens,
server authority and existing NO TRADE handling. Native controller regressions,
layout tests and the x86 DLL build pass.

Cut: no new server/protocol/database state, automatic loot permission changes,
native checkbox memory offsets, or additional configuration page.

Deployed: owner-authorized PR #129 is on main; signed release 2026100901 /
proxy 0.7.8-dev publishes the paired DLL/catalog/XML. The other 101 current
assets and all game services are preserved. Runtime, packaging and twelve
publication recovery checks pass.

Shaky/open: actual RoF2 rendering, preference persistence and inventory award
acceptance remain for owner gameplay QA. Source, deployment and exact QA:
[row-control release notes](../releases/advanced-loot/ROW-CONTROLS.md).
