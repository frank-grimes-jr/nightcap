# Gear and AA encounter progression controls

Date: 2026-09-12. Native candidate results; full BiS, activated abilities,
preparation, client parity and final balance recommendations remain incomplete.

## Recommended-level and haste controls

The previous additive gear optimizer excluded recommended levels above 50.
That loses legally equippable items. Native `Mob::AddItemBonuses` scales HP/mana,
stats and several other bonuses by recommended level, with signed integer
rounding. It takes the maximum raw worn haste without that scaling.

One hundred controls cover the 24 existing AA allocations with original gear,
Cloak of Flames (Ascended), Band of Swirling Air (Ascended), and both, plus four
isolated-item controls. Native flat item HP/mana, maximum haste, unchanged purchased
rank IDs and resolved total HP/mana all match their independent checks.
The 324-HP/348-mana recommended-level-62 ring contributes 261 HP and 281 mana at
level 50; its full 41% haste applies. Adding the 36% cloak retains 41% worn haste.

For the original caster-primary WAR/CLR/WIZ candidate at zero spent AA, the ring
substitution changes total HP 5,922 -> 6,162, mana 4,707 -> 4,835, and haste
0% -> 41%. These controls hold other slots and the AA allocation constant.
They do not declare the ring globally optimal or its level-72 source soloable.

## Actual boss encounters

The 52-case matrix uses the existing native engine, map geometry, spells and
32,000-HP boss definitions. All cases use the same level-50 Human agnostic
WAR/CLR/WIZ candidate with Sabertooth (Ascended) as a functioning one-handed
weapon and a shield. Forty-eight cases also equip the haste ring: eight AA
allocations, two bosses, three seeds (1729/1730/1731). Four zero-AA cases compare
the original back/ring setup and the haste cloak at seed 1729.

Gear stays identical across AA budgets. The comparison is spent AA points, with
common free ranks at zero. Finite budgets use the previously validated nested
balanced and durability-first allocations. All means the 13,738-point legal
purchase closure in the captured native data, excluding grant-only rewards.

Observed kills among the **three exploratory seeds**, using the balanced policy:

| AA budget | Actual spent | Nagafen kills | Vox kills |
|---|---:|---:|---:|
| 0 | 0 | 1/3 | 0/3 |
| 100 | 98 | 3/3 | 0/3 |
| 200 | 198 | 3/3 | 2/3 |
| 500 | 496 | 3/3 | 3/3 |
| All | 13,738 | 3/3 | 3/3 |

All-purchasable-AA kills took 26.30–39.45 seconds for Nagafen and 25.60–42.95
seconds for Vox. The balanced 500-AA kills took 88.60–198.95 and 59.45–194.60
seconds respectively. These ranges describe these runs, not population estimates.
At 200 points, durability-first also killed Vox in two of three attempts; at 500
it produced two kills and one 900-second timeout. Every retained run has native
player/boss melee activity and valid initial/terminal state and AA identities.
The complete 52-case rerun is byte-identical, and the separate test database still
contains zero accounts and zero character records. All 134 Python tests pass.

The zero-AA no-haste Nagafen case reproduces the earlier weapon control's
241.40-second kill. Changing equipment changes random draw consumption; equal
seeds across different builds are not paired identical combat rolls. The same
seed producing a worse outcome with better stats does not establish a regression.

## Interpretation and remaining work

The observed AA effect is large enough that balancing solely around zero or
fully purchased AAs would conceal material progression differences. It also
means raising spell/healing caps is not justified by a weak zero-AA candidate
alone. No cap, NPC HP, live rule, or production binary was changed.

The controller currently casts a fixed nuke and Superior Healing below 55% HP.
It uses purchased native AA bonuses, but activates no AAs and casts no preparation
buffs. These are neither optimized player rotations nor full power ceilings.
The shared limits in `native-encounter-runtime.md` still apply, including the
trained held-class skill ceiling, base-class client UI, reused native objects,
50-ms pulse, two-actor processing and mock death handling.

Movement is a concrete next correction: the controller faces the boss but does
not navigate back into melee after separation. The 500-point durability-first
Vox timeout ends out of melee range, with both actors alive, and cannot establish
a damage/sustain balance failure. Further scenarios need deliberate movement,
legal preparation/AA activation policies, additional entity processing where
required, timestep checks, more seeds, and final gear/acquisition review. Only
then can cap/HP sensitivity results support tuning and focused in-game QA.

Follow-up: `native-player-pursuit.md` records the implemented pursuit policy.
The historical timeout above becomes a 271.30-second kill, and the old policy
still reproduces exactly. These original records remain unchanged.

## Evidence and reproduction

- `gear-haste-inputs.json`, `gear-haste-stats.json`, `gear-haste-check.json` and
  `gear-haste-resources-check.json`: 100 equipment/AA controls.
- `gear-aa-encounter-inputs.json`: all 52 exact build/AA/boss/seed inputs.
- `gear-aa-encounters.json.gz`: full native reports, traces and per-run summaries.
- `gear-aa-encounter-check.json`: independent recomputation of every summary,
  complete case coverage and input/evidence/binary hashes.
- `gear-evidence-manifest.json`: artifact hashes and replay evidence.

From `tools/balance/`:

```powershell
python gear_haste_controls.py --snapshot fixtures/classic-20260912-v2.json.gz --aa-inputs ../../docs/balance/native-aa-inputs.json --output ../../docs/balance/gear-haste-inputs.json
python encounter_matrix.py --inputs ../../docs/balance/gear-haste-inputs.json --snapshot fixtures/classic-20260912-v2.json.gz --boss-inputs ../../docs/balance/native-encounter-nagafen-long-inputs.json ../../docs/balance/native-encounter-vox-long-inputs.json --output ../../docs/balance/gear-aa-encounter-inputs.json
```

Copy the matrix and `encounter_matrix.py` into the existing isolated runtime.
There, run `python3 encounter_matrix.py --run --inputs gear-aa-encounter-inputs.json
--output NEW-EVIDENCE.json.gz`. It refuses an existing output and a different
binary, starts a fresh native process per case, and checkpoints completed records.
After retrieving the evidence, recompute the checks locally:

```powershell
python encounter_matrix.py --inputs ../../docs/balance/gear-aa-encounter-inputs.json --verify ../../docs/balance/gear-aa-encounters.json.gz --output ../../docs/balance/gear-aa-encounter-check.json
```
