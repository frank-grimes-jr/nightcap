# Native pet commands and first pet-only boss controls

Date: 2026-09-12. Candidate-only work; no live restart, binary replacement, AA
removal, item/NPC adjustment or cap change.

## Command defect and correction

The original primary pet received a native attack order. Extra pets instead called
`Attack` immediately. Four requests spaced 100 ms apart produced 102 damage at
both 80 and 500 units, while NPC AI was deliberately paused. Neither extra pet
received its proper hate-list order. With only extra pets, the handler ignored
attack and qattack completely. Two primary-only controls behaved correctly.

The candidate shares the existing native attack/qattack logic across owned pets.
All eight command controls now pass: legal-distance pets receive orders, distant
pets receive none, repeated input causes no direct damage, and extra-only pets
respond. The two primary-only command reports remain byte identical. ADR 0012
records the decision, scope and manual QA.

The command boundary is intentionally a diagnostic with NPC AI paused. Actual
fights use `EntityList::MobProcess` and native movement, normal pet damage/death,
boss AI, buffs, resources and clocks. Primary and extra pets are created by real
summon casts; no pet ownership, stats or attack damage is fabricated.

## Combat and measurement scope

Four 120-second controls fight Nagafen/Vox using the fixed MAG/NEC/SHM candidate
shield inventory at zero and all open-pool purchases. The owner issues one attack
order and otherwise remains passive. Pets use their native AI. These runs show
real movement, aggro, damage and pet deaths, but are not an active player rotation,
win-rate estimate, final AA pool or full BiS certification. `pet-command-after-checks.json`
contains their results, elapsed times, boss HP and surviving pet IDs.

Client damage messages are incomplete when the owner is distant from combat.
The old `pet_damage`/`owner_damage` summary fields are observed packet totals only;
they must not be treated as complete DPS. New fight reports include a native boss
`damage_ledger` with before/after HP for every damage call. `native_boss_hp_loss`
sums root calls with overkill capped at zero HP; nested calls remain in the ledger
without being counted twice. This is gross HP loss through damage calls; healing
and regeneration between calls explain its difference from final boss HP.

| Control | Result/time | Final boss HP | Native gross HP loss | Observed pet packet damage |
| --- | --- | ---: | ---: | ---: |
| Zero-AA Nagafen | Owner death, 96.20s | 30493 | 1852 | 1852 |
| Zero-AA Vox | Owner death, 108.45s | 27035 | 5254 | 2622 |
| Open-all Nagafen | 120s timeout | 26773 | 5664 | 1612 |
| Open-all Vox | 120s timeout | 19511 | 12812 | 11402 |

The all-open allocation spends 13,288 points. Both Nagafen controls lose all pets;
zero-AA Vox ends with the owner dead and all pets still present, while open-all Vox
retains two pets. These are single-seed, passive-owner controls. In particular,
the missing packet damage would substantially understate some ranged runs.
Owner/boss death uses the existing diagnostic terminal adapters; pet persistence
after a real owner's death is not modeled by the final snapshot.

Follow-up: [native pet support](native-pet-support.md) adds self/pet healing,
resistance reduction, boss-specific offense, preparation and native recovery.
It uses spells eligible for this held-class profile instead of substituting the
Warrior/Cleric/Wizard rotation. Pet gear/focus, acquisition, other pet commands,
optimal play and curated expansion AA pools remain open. The unrestricted AA row
remains a stress case, not the Classic release target.

## Reproduction and provenance

From `tools/balance`:

```powershell
python -m unittest discover -s tests
python pet_combat_controls.py --inputs ../../docs/balance/pet-command-before-inputs.json --verify ../../docs/balance/pet-command-before.json.gz --output ../../docs/balance/pet-command-before-checks.json
python pet_combat_controls.py --inputs ../../docs/balance/pet-command-after-inputs.json --verify ../../docs/balance/pet-command-after.json.gz --output ../../docs/balance/pet-command-after-checks.json
```

`pet_combat_controls.prepare` regenerates the matched 12-case matrix. The existing
15 pet ownership controls and eight caster/monk encounters are rerun separately
as `pet-command-ownership-regression-*` and `pet-command-encounter-regression-*`.
Build and evidence manifests record exact binary/source hashes and test results.
All 201 Python tests pass. All 15 ownership reports and eight caster/monk reports
remain byte identical to the preceding phase. The two synthetic reagent inventory
rows were inspected and removed after testing; clone account, character and
inventory counts are zero.

The diagnostic now requires four source flags: `--spells-source`, `--attack-source`,
`--mob-source`, and `--client-packet-source`. `--reuse-candidates` saves build time
only when each candidate source, object, compiler flags and link file match their
prior hashes; changed or missing objects are recompiled. The harness/runtime are
still compiled each time. This cache operates within the existing partial build
snapshot and does not establish fresh header/source parity. No live object is
replaced. Reagent inventory writes are confined to the synthetic clone character
and require scoped cleanup after the controls.
