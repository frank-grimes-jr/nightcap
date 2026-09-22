# Phase 36: Three-pet command management

September 22, 2026. Candidate; activation and manual acceptance pending.

Built a three-row Pet Info roster with class, name and health, an explicit command
scope, All pets control, and commands routed through the existing server handler.
Clicking a roster name or an owned pet selects that pet. Enemy targeting preserves
the selected pet; clearing the target or clicking All pets restores shared scope.
Native slash commands and existing pet hotbar assignments follow the same scope.

The client uses a server-confirmed roster and bounded identity/freshness checks.
Server scope tokens prevent stale individual actions from broadening to survivors
after death, dismissal or class release. Existing combat and AA requirements stay
in the server handler. Pet Armor retains its independent selection.

Cut: per-pet buff grids, new AA permissions and gameplay balance changes. Native
gauges/buffs still show one representative; all three rows expose health. The
reported live no-op was not reproduced in the owner's session. Client disassembly,
compiled ABI checks and isolated native integration provide bounded evidence;
renderer appearance and owner command/lifecycle acceptance remain open.

[Build evidence, delivery and exact owner QA](../releases/pet-management-20260922/README.md).
