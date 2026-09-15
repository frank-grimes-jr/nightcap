# Native multiclass pet ownership correction

Date: 2026-09-12. Candidate-only source change; no live binary replacement,
restart, AA policy deployment, cap adjustment or NPC tuning.

## Result

The real summon path created extra-class pets, but normal entity processing
removed them because owner lookup accepted only the primary pet. Thirteen native
controls reproduced ten failures: Necromancer/Shaman-only summons, mixed summon
orders and every three-pet AA stage failed to retain their expected pets. The
ordinary Magician summon and reagent controls worked.

The candidate `server-mods/code/zone/mob.cpp` now recognizes the client's explicit
extra-pet registry in both owner lookups. All 15 candidate controls pass, including
two negative controls that unregister the Necromancer pet and verify native
detach/depop behavior. Six caster and two monk boss encounters produce the same
native report bytes as the previous phase. ADR 0011 records the decision and QA.

## What runs natively

The new `pet_probe` diagnostic is restricted to a connected, non-GM MAG/NEC/SHM
client and a bounded spell/action set. It uses actual gem `CastSpell` completion,
inventory reagents, `EntityList::MobProcess`, pet NPC construction, native maps
and movement. It records primary and extra IDs, surviving NPCs, owner IDs, depop
state, HP, AC, damage, haste, buffs, mana and component stacks. Cast acceptance is
not treated as proof that a pet exists; verification inspects the settled roster.

No owner IDs, pet stats or summon success are forced. The two explicitly labeled
negative controls remove a registry entry to test invalid ownership. The isolated
client never uses a live account. Native reagent consumption wrote two synthetic
inventory rows (character12, slots23/24, items10015/13073, nine charges each); both
were inspected and removed after the runs. Account, character and inventory tables
were empty afterward. Future reagent tests can create these clone-only inventory
rows again and require equivalent scoped cleanup.

The initial missing-Malachite control creates no pet. Supplying ten Malachite
creates the water pet and leaves nine. Burnout III changes its reported haste from
100 to 160 and installs the real buff. Its extra pets survive native processing.
Haste here is the engine's multiplier-style value: 100 is the unmodified baseline.

## AA sensitivity, not a release recommendation

The same candidate shield inventory is held fixed across all five stages. These
are open-pool diagnostic allocations; the all-purchase row is an unrestricted
stress case, not the legal maximum for a proposed Classic release.

| Requested budget | Actual spent | Water pet HP | Necromancer pet HP | Shaman pet HP |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0 | 2520 | 2615 | 1623 |
| 100 | 100 | 2545 | 2641 | 1639 |
| 200 | 199 | 2646 | 2745 | 1704 |
| 500 | 494 | 3099 | 3216 | 1996 |
| All open purchases | 13288 | 3402 | 3530 | 2191 |

Water/Necromancer pets are level41; Shaman is level36. These inputs resolve to pet
NPCs609/625/548, with zero focus power and no base equipment set. This is a
preparation/stat observation, not pet DPS, tanking, boss win rates or full BiS.
Pet gear/focus, buffing each pet, commands, taunt/aggro, DoTs, sustain, death,
movement and encounters remain to be implemented and measured. Global widened
spell class levels still prevent treating every class field as original ownership.

Curated release pools must also be tested for this role. Do not raise spell/heal
caps or boss HP to compensate for the reproduced ownership bug, and do not select
a Classic AA pool from the prior caster-only candidate comparisons.

## Reproduction

From `tools/balance`:

```powershell
python -m unittest discover -s tests
python pet_controls.py --inputs ../../docs/balance/pet-inputs.json --verify ../../docs/balance/pet-before-ownership.json.gz --output ../../docs/balance/pet-before-checks.json
python pet_controls.py --inputs ../../docs/balance/pet-ownership-inputs.json --verify ../../docs/balance/pet-after-ownership.json.gz --output ../../docs/balance/pet-after-checks.json
```

`pet_controls.prepare` regenerates the candidate matrix from expanded gear and
native AA inputs. The first 13 cases exactly match the original control inputs;
the last two exercise orphan lookup semantics. `pet-encounter-inputs.json` contains
the eight unchanged fight controls. Evidence and source fingerprints are pinned
in `pet-evidence-manifest.json` and the two pet native build manifests.

The current diagnostic requires all three source flags: `--spells-source`,
`--attack-source`, and `--mob-source`, pointing to their reviewed candidates inside
`/tmp/nightcap-balance-20260912`. Omitting one restores its earlier native object.
This remains a partial rebuild using 130 pinned native objects/archives, not a
complete fresh-source or live runtime parity claim. The original failure binary
is retained as `balance-zone-before-pet-ownership` in that isolated runtime.
