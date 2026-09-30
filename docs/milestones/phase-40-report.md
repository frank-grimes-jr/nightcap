# Phase 40: Advanced loot live deployment

Date: 2026-09-30. Owner-authorized direct main/OVH release; gameplay QA pending.

## Built and deployed

PR 91 is merged to main. Fresh paired world/zone preserve the prior production
hardening and unchanged login/UCS/shared-memory binaries. Additive loot schema,
signed game release 2026093006 and matching server are live with access open.
The existing launcher installs all 46 files; no separate launcher update is needed.

Private full-backup restore and migration rehearsal passed, followed by 47
existing-data preservation checks, actual game-account transaction probes,
15 native process hash checks, complete hosted client signature/file checks
and four public native handshakes. Thirteen isolated rollout fault tests and
independent source/operations review passed. Detailed host evidence remains
private; the public record uses command outcomes and public/local artifact hashes.

## Cut / superseded

The isolated local port-9000 cutover was superseded by the owner's live-test
request and was not performed. No requested core feature was cut. Native loot
rights, range and progression balance remain intact.

## Shaky / incomplete

Native rendering, real looting and lifecycle, quest restrictions, NO TRADE/lore,
raid transitions and checkpoint fault/replay acceptance remain open. The owner
will test ordinary gameplay live; injected faults stay isolated. After the new
server starts, recovery must preserve receipt-aware code and current data.
An older binary or pre-release database dump is not a routine rollback.

[Production and recovery](../releases/advanced-loot/PRODUCTION.md) ·
[Exact owner live QA](../releases/advanced-loot/LIVE-QA.md).
