# Earned AA ownership: native load/save increment

2026-09-13. Feature branch only; **not ready for promotion or activation**.
The five-fix QA candidate on `test` remains frozen at `5f61fdd`.

## Implemented and measured

`Client` now retains canonical earned rank counts separately from the usable
`Mob::aa_ranks` view. Loading derives the greatest currently eligible prefix.
Saving preserves the full earned count, remaining charges, and full nominal
cost plus existing expended-AA cost. The earned-count check also prevents
repurchasing an already-owned rank. Unresolved saved ranks invalidate ownership
and block saving and purchases rather than silently repricing them.

Six native controls passed, covering 32 operations:

| Control | Result |
|---|---|
| Six Natural Durability ranks, only three eligible | Three remain active; all six earned ranks and 29 spent points survive; restoring access returns six |
| All six ranks temporarily unavailable | Zero active ranks; full ownership and accounting survive; restoring access returns six |
| Empty ownership, five expended points | Empty ownership stays empty; five spent points and the wallet remain unchanged |
| Glyph of Dragon Scales temporarily unavailable | One earned rank and its one remaining charge survive suspension and restoration |
| Oversized saved count of seven | Load/save reject it; saved row and currency remain unchanged |
| Noncanonical saved rank ID 108 | Load/save reject it; saved row and currency remain unchanged |

Every step checks the client profile against the usable native count, stored
rows, wallet, spent points, earned-count validity and applicable anti-repurchase
readouts. These are real native load/save and gate calls. They do not simulate
purchase completion, refunds, charge consumption or gameplay.

The earlier failure remains captured in `aa-owned-view-before.json.gz`: the
three-rank prefix disappeared and a save lowered reported spent points to five.
The exact earlier harness is archived separately and matches its build hash.

## Build and reproduction

Freshly built `zone` and `tests` from all 2,787 verified source files in
`/tmp/nightcap-aa-owned-core-20260913/source`. Only `aa.cpp`, `client.cpp` and
`client.h` differ from the frozen QA source. A full rebuild accounts for the
changed `Client` layout. All 87 C++ tests pass in a separate directory.
All 324 calculator and evidence tests pass; the exact final suite log is archived.

The diagnostic in `/tmp/nightcap-balance-owned-core-20260913` links those fresh
objects with the existing isolated adapters and additional ownership readouts.
Its binary SHA256 is
`5c620e2aac0856b180c4d2581c163e7a8c4254661336d8128e6effabeb9d1ca9`.

From `tools/balance`, reproduce against the dedicated empty clone:

```text
python run_aa_owned_core.py --runtime /tmp/nightcap-balance-owned-core-20260913
python -m unittest discover -s tests -v
```

The runner checks the clone name, empty fixture tables and binary hash, removes
only exact known synthetic rows, and verifies the unchanged AA-table hash.
Afterward account, character, owned-AA and inventory row counts are all zero.
No live server, era, balance cap, NPC HP or real character data was changed.

Build logs, source manifests, exact source archive, native reports and input
fixtures are recorded under `aa-owned-core-*`. The diagnostic builder's generic
manifest describes reused objects; the separate full-build evidence establishes
that these particular objects came from the fresh isolated source build.

Historical five-fix tests now use a five-file archive extracted from the exact
verified release source archive. Original and candidate hashes and the regenerated
patch still match. They no longer mistake a subsequent feature edit for corruption
of the frozen QA candidate.

## Remaining integration and review findings

This is a coupled load/save increment, not a complete ownership feature:

- Refund, reset and class-release still operate on the old active-only view.
  They must remove the corresponding canonical ownership and preserve native
  grant-only/shared-class behavior before this code can be promoted.
- Charge consumption and explicit rank removal must remove canonical ownership;
  otherwise a later save can recreate a removed row. The charged control above
  proves preservation only, not consumption.
- Purchase/grant/toggle paths still need persistence-failure handling. SaveAA's
  successful row replacement does not make wallet, expended points and all other
  character writes atomic. Catalog-rejection controls are not SQL failure injection.
- Declarative expansion caps must retain the complete catalog. Permanent removal
  and compensation remain separate from temporary suspension.

Author review checked exact saved-rank validation, profile bounds, cost overflow,
anti-repurchase readouts, source provenance, clone isolation and the known lifecycle
gaps above. This increment is intentionally kept off `dev` and `test` until the
remaining ownership lifecycle is implemented and verified. It makes no claim that
final gameplay balance is clean or that owner in-game QA is complete.
