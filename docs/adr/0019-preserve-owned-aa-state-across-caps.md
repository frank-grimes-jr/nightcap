# 0019: Preserve owned AA state across expansion caps

Date: 2026-09-13. Status: native loader candidate and offline model verified;
release integration pending.

## Decision

Populate the profile AA array only after native SetAA accepts an owned rank, and
clear the array when reloading ownership. Keep rejected persisted rows intact for
explicit reconciliation. The loader must not implicitly refund, delete or clamp
earned purchases when a catalog changes.

Model earned ownership separately from the active rows permitted by the current
expansion. Preserve the original rank source and nominal earned cost; materialize
active rows from that source and the selected policy. This is an offline model,
not an installed database ledger or an approved final AA offering.

## Evidence

Five native controls reproduce three stale-profile cases and verify the fix.
The two already-valid controls remain byte-identical. Twenty-four matched boss
reports also retain their complete reports and raw hashes. All 196 captured
purchases survive launch/later/launch transitions with total nominal cost 3,155.
A synthetic six-rank Natural Durability purchase returns from a three-rank cap,
then loads and saves natively with all six ranks and an unchanged 17-point wallet.

## Alternatives and consequences

Deleting excluded purchases loses earned progression. Refunding automatically can
change the economy and permit repeated conversion when policies change. Merely
keeping above-cap rows in the existing table does not provide active lower ranks;
repurchasing can overwrite that same canonical row. The separate earned model
allows explicit decisions about temporary expansion locks and permanent removals.

Deployment still requires durable transactional storage, spent-point accounting,
purchase/reset/refund/class-release/charged-AA lifecycle handling, and declarative
era integration. The model rejects decreases, disappearance and affected charged
abilities instead of inventing those rules. It cannot infer an unseen reset of a
fully suspended family; runtime hooks are required. Permanent removals and their
compensation need a deliberate policy distinct from later expansion unlocks.

See `docs/balance/native-aa-ownership.md` for exact scope and in-game QA.
