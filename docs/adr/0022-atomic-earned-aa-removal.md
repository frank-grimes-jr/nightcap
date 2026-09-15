# 0022: Commit earned-AA removal and its counters together

Date: 2026-09-13. Status: feature implementation; not promoted.

## Problem

The canonical ownership introduced by ADR0021 must participate in explicit rank
reset and charged-AA consumption. The old paths delete a database row but leave
the new ownership cache intact; SaveAA recreates the row. Native controls show
a reset six-rank purchase returning on reload, and a one-charge glyph returning
twice while reported spent points rise from 8 to 11 to 14.

## Decision

For single-family reset and charge consumption, prepare the resulting earned and
usable maps and point totals without mutating the session. In a native database
transaction, lock the character and all its owned AA rows, check the saved owned
counts/charges and expended counter against the loaded state, modify the selected
row, and persist spent/expended counters. Update session ownership, active ranks,
profile entries and bonuses only after an acknowledged commit. Do not change the
unspent wallet for either operation.

An explicit reset removes earned ownership even when all ranks are suspended.
Consumption requires an active owned AA with charges; consuming the final charge
removes its earned row and increments expended cost once. Preserve native pricing
of the consumed rank. The captured full catalog contains only one-rank, one-charge
expendables, so rank cost equals their complete nominal cost. This evidence does
not validate a future catalog with multi-rank or multi-charge expendables.

Reject nested transactions rather than committing an outer operation. Disable
automatic statement retries within this transaction. A failed or uncertain
mutation invalidates the AA state; SaveAA, purchases and AA activation are then
blocked pending reload/reconciliation. A definite SQL failure after deleting the
owned row must restore that row and both counters through rollback.

`DBcore::QueryDatabase` has both `(const char*, uint32 length, bool retry)` and
`(const std::string&, bool retry)` overloads. Calls with a literal and `false` can
select a zero-length query instead of disabling retry. Explicit `std::string`
arguments select the intended retry-flag overload for transaction statements.

## Boundaries before promotion

This transaction is not a complete AA persistence redesign. Refund/all-AA reset,
class release, purchase/grant/toggle and general character-save writes still need
coordinated handling. In particular, a lost commit acknowledgment followed by an
ordinary character save could overwrite counters with the old session values;
that broader path needs reconciliation and connection-loss fault tests before
promotion. The captured rollback control proves a definite statement failure,
not uncertain commit recovery or exactly-once gameplay effects.

Manual in-game QA remains required. The five-fix test candidate is unchanged.
