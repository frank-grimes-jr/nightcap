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
python snapshot.py --output fixtures/classic-20260912-v2.json.gz
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

## Spell content and arithmetic

```powershell
python spell_content.py --snapshot fixtures/classic-20260912-v2.json.gz --output ../../docs/balance/npc-spell-profiles.json
python verify_spell_math_cpp.py --source E:/EQ_Local_Dev/akk-stack/code --snapshot fixtures/classic-20260912-v2.json.gz --output ../../docs/balance/spell-resolution-oracle.json
```

The v2 snapshot closes references from actual boss lists, their immediate parents,
item effects, and recourses; it also captures Human creation allocations. Existing
proofs retain their original fixture hashes. Do not overwrite a reviewed fixture
when refreshing content; choose a new dated/versioned output name.

The spell oracle compiles extracted native duration, effect-value, and resist
functions without booting a zone or accessing PEQ. It tests ordinary resists with
resolved modifiers; it excludes the special paths listed in its report. Unsupported
effect formulas are reported explicitly. The content report contains formula
values, not fully applied spells. `npc_casting.py` supplies engaged selection for
the captured boss categories, given scan order and resolved readiness/statuses;
runtime integration, stacking, prebuffs, fear timing, and dispels remain pending.

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

## Native equipped-stat diagnostic

The first validated runtime is `/tmp/nightcap-balance-20260912` inside the server
container, using `nightcap_balance_20260912` and its dedicated test user. It has
empty account/character tables and its own generated caches. Do not point it at
the live runtime. The executable refuses that before initialization.

For a new setup, `prepare_native.py` copies content tables, creates empty schemas
for other tables, and prepares synthetic creation/loadout inputs. It refuses an
existing destination/user. Its root access is used only to read source content
and create the isolated destination and test permissions; test credentials stay
in the container runtime, outside these reports. The `shared_memory` configuration
must end in `/` for the existing cache builder.

```powershell
python prepare_native.py --source E:/EQ_Local_Dev/akk-stack/code --snapshot fixtures/classic-20260912-v2.json.gz --builds ../../docs/balance/candidate-builds.json --output ../../docs/balance/native-clone-manifest.json
docker cp build_native.py akk-stack-eqemu-server-1:/tmp/nightcap-balance-20260912/build_native.py
docker cp native_harness.cpp akk-stack-eqemu-server-1:/tmp/nightcap-balance-20260912/native_harness.cpp
docker exec akk-stack-eqemu-server-1 python3 /tmp/nightcap-balance-20260912/build_native.py
docker exec -w /tmp/nightcap-balance-20260912 akk-stack-eqemu-server-1 /home/eqemu/code/build/bin/shared_memory
docker exec -w /tmp/nightcap-balance-20260912 akk-stack-eqemu-server-1 /tmp/nightcap-balance-20260912/balance-zone tests:balance /tmp/nightcap-balance-20260912/inputs.json /tmp/nightcap-balance-20260912/results.json
docker cp akk-stack-eqemu-server-1:/tmp/nightcap-balance-20260912/results.json ../../docs/balance/native-equipped-stats.json
python verify_native_resources.py --native ../../docs/balance/native-equipped-stats.json --builds ../../docs/balance/candidate-builds.json --snapshot fixtures/classic-20260912-v2.json.gz --output ../../docs/balance/native-resource-check.json
```

Reuse the prepared runtime for subsequent diagnostics; skip the creation command
when it already exists. Copy/run `verify_native_guard.py` in the same directory
with `--binary .../balance-zone --output .../native-guard-check.json` to test its
seven preflight refusals. No valid configuration is started by those guard tests.

The original native results include worn bonuses but no purchased AAs, active
buffs, clicks, or quest hooks. The build manifest pins reused objects and makes no fresh full
source-build claim. See `docs/balance/native-equipped-stats.md` and ADR 0005.
The requested AA comparison matrix is in `docs/balance/aa-baseline-matrix.md`.

### AA progression inputs

`native-aa-catalog.json` captures the native eligible ranks for the three Ascended
profiles. To refresh it in the prepared runtime, use inputs selecting those
profiles with `export_aa_catalog: true`, no `aa_rank_ids`, and no AA budget.
Keep catalogs paired with their source build manifest and content clone.

```powershell
python aa_allocations.py --catalog ../../docs/balance/native-aa-catalog.json --builds ../../docs/balance/candidate-builds.json --snapshot fixtures/classic-20260912-v2.json.gz --output ../../docs/balance/native-aa-inputs.json --audit ../../docs/balance/aa-allocation-audit.json
docker cp ../../docs/balance/native-aa-inputs.json akk-stack-eqemu-server-1:/tmp/nightcap-balance-20260912/aa-inputs.json
docker exec -w /tmp/nightcap-balance-20260912 akk-stack-eqemu-server-1 /tmp/nightcap-balance-20260912/balance-zone tests:balance /tmp/nightcap-balance-20260912/aa-inputs.json /tmp/nightcap-balance-20260912/aa-results.json
docker cp akk-stack-eqemu-server-1:/tmp/nightcap-balance-20260912/aa-results.json ../../docs/balance/native-aa-stats.json
python verify_native_aa.py --inputs ../../docs/balance/native-aa-inputs.json --native ../../docs/balance/native-aa-stats.json --catalog ../../docs/balance/native-aa-catalog.json --output ../../docs/balance/native-aa-verification.json
python verify_native_resources.py --native ../../docs/balance/native-aa-stats.json --builds ../../docs/balance/native-aa-inputs.json --snapshot fixtures/classic-20260912-v2.json.gz --output ../../docs/balance/native-aa-resources-verification.json
```

Copy/run `verify_native_aa_gates.py` and `verify_native_aa_closure.py` in the
isolated runtime for illegal-purchase rejection and all/free completeness checks.
Their `--inputs`, `--catalog` (gates only), and `--output` files must live directly
in that runtime. Results and limitations are in `docs/balance/native-aa-stats.md`.
The finite budgets use nested purchase prefixes, so actual spent points can be
slightly below budget. Free purchasable ranks are common to every stage;
grant-only rewards are excluded. AA activation policies and fights remain pending.
