# ADR 0023: Refund earned AAs and guard invalid profile saves

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-13. Status: implemented on the AA feature branch; promotion pending.

## Decision

Bulk refund operates on canonical earned ranks, including temporarily suspended
or partially usable ranks. Refund the full earned rank cost once; retain grant-only
abilities and the existing exception for exhausted charged abilities. ResetAA uses
the same operation without a subsequent blanket deletion.

A shared persistence helper locks and verifies current ownership and expended
cost, persists changed ownership plus wallet/spent/expended counters in one
transaction, and replaces session state only after an acknowledged commit.
Single-rank reset and charge consumption also use this helper.

An unacknowledged change invalidates the AA session and immediately asks the player
to reconnect. Refuse AA-only reload while invalid: it does not reload the character
point counters and could otherwise enable stale profile writes. A fresh client
session is required. SaveCharacterData refuses invalid AA sessions before writing
the character row, and Client::Save propagates its failure result.

## Tradeoffs and boundaries

This also requires reconnect after a known rollback. It sacrifices availability
for preserving ownership and counters. Main character-row progress cannot be
saved while invalid; other tables written earlier by Client::Save are not made
atomic by this change. The direct profile-save controls exercise the real native
function with an explicit positive-account fixture, not login/authentication or
the complete Client::Save path.

The committed-state control injects a database/session disagreement; it does not
simulate a dropped COMMIT response. Real reconnect, network failure, nested
transactions, purchase/grant/toggle, and class-release integration remain open.
No live binary, AA policy, or balance numbers change in this increment.

Evidence: ../balance/native-aa-bulk.md.
