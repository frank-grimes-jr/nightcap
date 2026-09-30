# Advanced-loot integration review

Date: 2026-09-30. Candidate source on `feature/advanced-loot`.

An independent second-model review inspected the native queue, corpse adapters,
checked inventory/currency transfers, saved-state recovery and client snapshot/UI
changes. The reviewer was read-only; execution evidence comes from the parent
agent's fixtures and build records.

## Resolved findings

| Finding | Correction | Evidence |
|---|---|---|
| Classic manual clicks had lost cursor pickup | Explicit destination mode; cursor and child preimages checked; no cursor queue overwrite | Inventory fault fixture |
| Classic automatic pickup had lost auto-equip | Share native slot selection and wear/equip notifications; check all worn preimages; persist evolving equipped state | Inventory fault fixture and paired server build |
| Disconnected masters could strand shared controls and coins | Select connected/data-loaded eligible participants; constrain item handoff to original roster | Policy and production access fixtures |
| Classic GM recovery could be blocked by advanced ownership or Never | Require native GMAllowed session; preserve claim/quarantine checks; revalidate GM authority after quest callback | Production access fixture and source review |

The final reviewer pass found no further high-confidence defects in those fixes.
Snapshot actions intentionally remain disabled during an incomplete refresh so
stale row authority is never submitted while a newer snapshot is assembling.

## Production review and execution

A subsequent independent read-only review covered the exact 24-path source delta
against the hardened production baseline and the deployment/publication helpers.
No authentication-hardening regression was found. Resolved operational findings:

- Verify privileges through the actual game database account, with writes rolled
  back and no credential export, before marking ready and before opening access.
- Preserve the receipt-aware boundary from the first new-server start attempt;
  failures thereafter hold access closed and never choose an older binary.
- Emergency hold works without trusting the staged manifest, treats a verified
  absent gateway as closed, attempts game shutdown and records verified outcomes.
- Check exact inventory columns and zero transfer/new-table triggers before use.
- Require matching healthy server identity and a closed gateway before publishing
  the signed client channel, then verify public bytes before opening access.

Thirteen isolated orchestration tests passed. The final reviewer found no concrete
blocker. Actual production preflight, activation, publication, opening and public
transport subsequently passed; [deployment evidence](PRODUCTION.md) records scope
and limitations. Native gameplay acceptance remains with the owner.

## Limits

This review does not establish native rendering, real client packet behavior,
quest callback integration, live group/raid lifecycle behavior or owner acceptance.
The [QA matrix](QA.md) remains required. In particular, a previous server binary
that ignores loot receipts must not be paired with unreconciled saved checkpoints.
