# Native earned-AA reset and charge consumption

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


2026-09-13. Feature branch only; not promoted or activated. The five-fix candidate
on `test` remains frozen at `5f61fdd`.

## Verified change

Explicit single-AA reset now removes canonical earned ownership as well as the
usable view, including when expansion restrictions make the entire family
inactive. Final-charge consumption removes canonical ownership and moves its
native rank cost into expended points once. The unspent wallet is unchanged.
Subsequent saves and reloads cannot recreate the removed AA or its charge.

The native transaction checks the saved ownership and expended counter against
the loaded state, changes the selected row and character counters together, and
updates the session only after an acknowledged commit. Both clone tables use
InnoDB. See ADR0022 for the decision and its remaining failure-handling boundaries.

Four before/after native controls cover 22 operations:

| Control | Before | After |
|---|---|---|
| Reset an active six-rank Natural Durability purchase | Earned row returns on save/reload | Ownership/profile remain empty; spent points fall from 29 to five expended points; wallet remains 17 |
| Reset the same purchase while all ranks are suspended | Reset does nothing; restoring access returns all six ranks | Earned row stays removed after access is restored |
| Consume Glyph of Dragon Scales, reload, attempt consumption again | Charge returns; spent points rise from 8 to 11 to 14 | Charge stays removed; expended points rise from five to eight once; total stays eight; legitimate repurchase is offered |
| Reject character UPDATE after the owned-row DELETE | Old path has no coupled character update or rollback handling | Transaction restores the row and counters; memory stays intact; SaveAA is blocked until ownership reload |

The final case uses a temporary clone-only `BEFORE UPDATE` trigger that raises a
SQL error. It is removed after the case. No real character or live database is
used. The runner requires an empty clone, creates exact synthetic character and
AA rows, and preserves unexpected rows for inspection instead of deleting them.
After both batches, account/character/owned-AA/inventory counts are zero, the
trigger is absent, and the AA catalog hash remains unchanged.

These are direct native reset/consumption calls and persisted-row observations.
They do not include a spell activation, full-character reconnect, refund, class
release, or gameplay simulation. Calling a void native method is not treated as
proof of success: the acceptance checks compare its resulting state.

## Build and reproducibility

A fresh `zone` and C++ test build uses all 2,787 verified source files in
`/tmp/nightcap-aa-removal-20260913/source`. All 87 C++ tests pass in separate test
storage. Exact source and build evidence are archived under `aa-removal-*`.
All 329 calculator/evidence tests pass; the final suite log is archived alongside
the native reports. Rebuild from the frozen five-fix full-source archive plus
the three native files in `aa-removal-source.tar.gz`; the full source manifest
pins the resulting tree.

The same diagnostic harness is linked separately to the before and after builds.
The after diagnostic SHA256 is
`5448dd3130e26c05442b10b4a44b5dce748f494ea6f1b4c66a0fbc309a9c765e`.
The earlier core source and diagnostic remain preserved.

From `tools/balance`, with the corresponding isolated runtimes prepared:

```text
python run_aa_removal.py --phase before
python run_aa_removal.py --phase after
python -m unittest discover -s tests -v
```

The before batch intentionally fails all four acceptance states; the after batch
passes all four with zero differences. Native reports pin input identity, usable
and earned counts, profile entries, charges, wallet, spent/expended points and
their database counterparts. Historical evidence uses archived source so later
feature edits do not invalidate a frozen build's provenance.

## Review and remaining gates

Author review checked transaction ordering, exact ownership comparison, numeric
SQL inputs, disabled retry behavior, no wallet mutation, removal while suspended,
profile cleanup, and unchanged non-client charge handling. The consumed-rank
price preserves native behavior; all charged families in the captured full
catalog have one rank and one charge. Future multi-rank/multi-charge expendables
need additional validation.

This does not finish the AA lifecycle. Refund/all-AA reset, class release,
purchase/grant/toggle, and general character-save persistence still need work.
Uncertain commit recovery and interaction with ordinary character saves remain
explicit blockers; the injected definite SQL failure is not evidence for those
paths. Nested-transaction refusal and connection-loss paths also need native
failure controls before promotion. No live source, binary, cap, NPC HP, era or
AA offering was changed. Final balance and owner in-game QA remain open.
