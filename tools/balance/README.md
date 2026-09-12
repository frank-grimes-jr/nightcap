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

## Calculator development

```powershell
python verify_cpp.py --source E:/EQ_Local_Dev/akk-stack/code/zone/effects.cpp --output ../../docs/balance/spell-formula-oracle.json
python verify_resources_cpp.py --source E:/EQ_Local_Dev/akk-stack/code --snapshot fixtures/classic-20260912.json.gz --output ../../docs/balance/resource-formula-oracle.json
python snapshot.py --output fixtures/classic-20260912.json.gz
python builds.py --snapshot fixtures/classic-20260912.json.gz --output ../../docs/balance/candidate-builds.json
```

The oracle extracts and compiles the actual `GetExtraSpellAmt` body in a temporary
standalone C++ program inside the server container, compares boundary/random cases,
and removes the temporary executable. Its proof covers that function only.

The resource oracle extracts the actual base/max HP and mana functions plus
caster predicates. It compares four outputs per case using the frozen base-data
rows. It fixes the client to RoF2 and the SoD resource rule to enabled, as observed
in this baseline; supplied stats and bonuses bypass inventory/AA/buff resolution.
It does not boot a zone or connect to PEQ. `resources.py` rejects missing base data
instead of returning a plausible but incomplete build. Its ancillary heroic/stat
helpers have unit coverage and source review, but are not part of this native
resource oracle's differential proof.

The snapshot uses one read-only content transaction and excludes player/account
data and service configuration. The manifest hashes the compressed fixture; the
build generator rejects a mismatched snapshot. The SQL export query is saved for
inspection. The pool is based on current Classic-zone spawn/loot eligibility,
including parent loot gates and open-world disabled-spawn records. It is not a
claim of historical Classic item authenticity, and deliberately excludes flagged,
conditional, quest, merchant, global-loot, epic, and augment paths at this stage.

The assignment solver maximizes the documented additive score exactly, including
lore conflicts and legal class/race/deity/level/slot checks. This produces candidate
loadouts, not final combat BiS. The full enemy/character model, AA/buff/effect
coverage, and encounter simulations are still in progress.

## Event simulation and controls

```powershell
python verify_melee_cpp.py --source E:/EQ_Local_Dev/akk-stack/code/zone/attack.cpp --output ../../docs/balance/melee-formula-oracle.json
python encounter_cli.py --scenario fixtures/nagafen-melee-control.json --runs 1000 --trace --output ../../docs/balance/nagafen-melee-control.json
python verify_control.py --results ../../docs/balance/nagafen-melee-control.json --output ../../docs/balance/nagafen-melee-control-check.json
```

`encounter.py` schedules casts, mana spending, cooldowns, healing, fear interrupts,
periodic effects, regeneration, and melee rounds. Inputs must supply resolved
effects and defenses. The current scenario format accepts only `diagnostic`
status and requires explicit assumptions; it does not certify those assumptions.
The CLI preserves seeds, input/model hashes, all trial results, and optionally the
first trace. Kill times and death times are reported separately.

The Nagafen control has captured unbuffed melee inputs and an artificial
defender. It excludes spells and is not a complete boss fight or a BiS result.
The check enumerates exact hit and mitigation distributions and compares the
event runner's mean damage with the resulting expectation. See
`docs/balance/engine-validation.md` for fidelity boundaries and remaining work.
