# Nightcap balance tooling

Python 3 standard library; no package installation or root npm command needed.
Run from this directory:

```powershell
python -m unittest discover -s tests -v
python baseline.py --runtime E:/EQ_Local_Dev/akk-stack --database --cpp-tests --output ../../docs/balance/baseline-after.json
```

The audit is read-only. It compares the active source to this checkout, verifies
the declared stored rules and existing worn item stamps, and optionally runs the
existing C++ suite in its required server working directory. It fails closed on
missing/mismatched files or rules and rejects the C++ runner's false-zero exit
status on failed assertions. `--database` and `--cpp-tests` need local Docker access.

The baseline expectation is deliberately pinned to the reviewed 250 caps. A future
approved cap change should update the explicit expectation and evidence together;
the audit must not silently learn whatever live values happen to exist.

This tool does not reload zones, modify PEQ, or certify in-memory combat behavior.
See `docs/balance/reconciliation.md` for the current pending runtime gate.
