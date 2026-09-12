# Native activated-AA baseline

Date: 2026-09-12. Candidate WAR/CLR/WIZ data; final BiS and balance tuning remain open.

## What the diagnostic now measures

Purchased ranks are activated through the native AA entry point, casting,
client processing, buff ticks and persistent cooldowns. The diagnostic records
acceptance evidence, failure-message IDs, resources, buff durations and hit
charges. There is no resource refill after a scenario begins. Timers begin ready
in each fresh process; this models a prepared cooldown state, not consecutive farming.

Fourteen 150-second lifecycle controls hold gear and purchases fixed at the
balanced 200-point and all-purchasable stages. They compare idle, each selected
AA, competing sustain requests, and combined burst abilities. Tenacity-induced
deaths terminate a control early. Seven isolation checks, five invalid-input
checks passed. Automated tests also reject corrupted identities, cooldowns,
charge histories, missing native failures and incomplete scenario sets.

Final verification: 149 Python tests pass. All 144 native encounter reports have
identical raw hashes on replay, and their serialized JSON is identical after the
charge-summary correction. The local and container gzip implementations produce
different compressed bytes; the saved encounter artifact is the native replay.
The 14 lifecycle controls replay byte for byte. All 52 prior passive-only pursuit
encounters also reproduce byte for byte. All 144 active cases pass movement checks;
the 54 active-policy cases at 0/100 points preserve their prior combat/movement.
The isolated account and character tables remain empty.

## Observed server interactions requiring reconciliation

1. **Celestial Regeneration can be owned but cannot buff this level-50 character.**
   Captured spells 2740 and 27657 use level 254 in their class fields. Native
   `GetSpellMinimumLevel` returns 254; enabled `Spells:BuffLevelRestrictions`
   rejects the group buff at level 50. The native packet contains message 197
   (spell too powerful), no buff appears, and no cooldown starts. This is distinct
   from AA purchase eligibility. Do not count this as available sustain yet.
2. **Tenacity and Celestial Regeneration share cooldown group 4.** A successful
   Tenacity activation prevents subsequent regeneration requests. At the maximum
   purchased ranks, native AA reductions resolve Tenacity to 1,620 seconds and
   regeneration to 540 seconds. Do not independently stack their advertised effects.
3. **The permanent self-buff change also affects Tenacity and Twincast.**
   `zone/spells.cpp::CalcBuffDuration` sets eligible self-buffs to one million
   ticks while excluding disciplines and short-box buffs. Tenacity is not in the
   short box: the low-rank control receives 1,000,000 ticks and the maximum-rank
   control receives 1,800,000 after native duration bonuses. Its negative HP ticks
   continue. At 150 seconds, low-rank Tenacity leaves 1,709 HP versus 2,750 for the
   identical idle control. The maximum-rank control starts at 5,438 HP, rises to
   20,210 on activation, then dies at 78.65 seconds without an opponent or healing.
   The latter establishes the harm under current behavior; a counterfactual with
   normal duration is still needed to attribute how much harm permanence causes.
4. **Twincast retains finite charges despite the long timer.** The idle low/high
   rank controls retain 10/12 charges, respectively. Frenzied Devastation is in the
   short box and starts with 3/9 charges and 20/36 ticks. Native costs and focus
   interactions must be exercised during combat; indefinite time is not unlimited charges.
   Nine boss runs show directly observed Twincast charge decreases (1-3 charges
   each); many others lose the buff before any decrease is sampled. A disappearance
   is not counted as charge use. The breath spell definitions contain Cancel Magic,
   so buff ordering and timing need preparation controls before claiming burst ceilings.
5. **Divine Arbitration spends a cooldown without changing solo resources.**
   Its effect requires a group or raid subgroup. Both solo controls match the
   corresponding idle HP/mana/buff trace. It is excluded from encounter rotations.

## Encounter policies

The 144-case matrix extends the existing 48 fixed-gear AA cases (two bosses,
three seeds, eight AA allocations) with three policies: burst only; burst plus
one regeneration attempt; burst plus Tenacity. All start with native Twincast
then Frenzied Devastation when owned. Sustain is requested below 80% HP. Each AA
gets at most one request. Rejections still consume the controller's reaction time.
The 0/100-point allocations own none of these selected activations.

These are explicit candidate rotations, not optimal play. A failed regeneration
request can alter spell timing and subsequent RNG draw consumption; different
outcomes at the same seed are not evidence that the rejected AA healed anything.
The Tenacity policy does not click off the harmful buff. A cancellation policy
and intended self-buff behavior require separate analysis.

All 144 cases completed. For the balanced spending policy, observed kills among
three seeds per boss were:

| Budget | Nagafen: burst / regeneration attempt / Tenacity | Vox: burst / regeneration attempt / Tenacity |
|---|---|---|
| 0 | 1 / 1 / 1 | 0 / 0 / 0 |
| 100 | 3 / 3 / 3 | 0 / 0 / 0 |
| 200 | 3 / 2 / 3 | 1 / 3 / 1 |
| 500 | 3 / 3 / 3 | 3 / 3 / 3 |
| All | 3 / 3 / 3 | 3 / 3 / 3 |

Maximum-AA kills take 30.90-63.30 seconds for Nagafen and 16.95-32.65 seconds for
Vox under these policies. Their sustain threshold is never reached, so the three
policies behave identically at that stage. These samples establish meaningful
progression and policy effects; they are too small for win-rate estimates, and
neither monotonic improvement nor optimal rotations are implied.

## Evidence and reproduction

- `active-aa-inputs.json`, `active-aa-controls.json.gz`, `active-aa-check.json`:
  lifecycle inputs, full native reports and independent checks.
- `active-aa-spell-rows.json`: complete selected spell rows from the isolated clone.
- `active-aa-build-manifest.json`: diagnostic source, flags, link and reused-object
  hashes. The existing 130-object build provenance limitation still applies.
- `active-aa-encounter-inputs.json`: exact candidate boss inputs and policies.
- `active-aa-encounters.json.gz`, `active-aa-encounter-check.json`: all 144 native
  reports and independently recomputed summaries. Charge counts are conservative
  observed decrements, not an inference from vanished buffs.
- `active-aa-replay-check.json`, `active-aa-isolation-regression-check.json`,
  `active-aa-movement-check.json`: replay, unchanged passive results, empty player
  tables and movement verification. `active-aa-legacy-inputs.json` reproduces the
  prior 52-case matrix with the new binary hash.
- `active-aa-guard-check.json`, `active-aa-invalid-check.json`: seven preflight
  and five activation-input rejection controls.
- `active-aa-evidence-manifest.json`: hashes of the retained evidence and sources.

From `tools/balance`, verify retrieved lifecycle evidence:

```powershell
python active_aa_controls.py --inputs ../../docs/balance/active-aa-inputs.json --verify ../../docs/balance/active-aa-controls.json.gz --output ../../docs/balance/active-aa-check.json
```

Copy the native sources/header and build script to the existing isolated runtime,
build with `python3 build_native.py --reuse-adapters`, and check the binary hash
against the chosen matrix. Copy `active_aa_controls.py` and `encounter_matrix.py`
there. Execute with container Python, choosing a new output path:

```sh
python3 active_aa_controls.py --run --inputs active-aa-inputs.json --output NEW-AA-controls.json.gz
python3 active_aa_controls.py --run --inputs active-aa-encounter-inputs.json --output NEW-AA-encounters.json.gz
```

Run matrix drivers sequentially: they share per-case scratch filenames. The
captured AA eligibility and engine build are dated evidence, not a permanent
claim about future server state. Preparation buffs, final gear/acquisition/BiS,
other build archetypes and pets, timing sensitivity, larger seed sets, fresh build
parity and in-game QA remain before numerical balance recommendations.
