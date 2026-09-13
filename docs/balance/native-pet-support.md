# Native MAG/NEC/SHM support comparison

Date: 2026-09-12. Isolated diagnostic only; no live deployment or numerical tuning.

Follow-up: [native belly casting](native-pet-belly-casting.md) corrects the approach
for the dragons' ranged-spell immunity. Retain the results below as historical
ranged-strategy controls, not an estimate of this build's full combat power.

This extends the [pet command controls](native-pet-commands.md) with an active
owner. It measures fixed candidate equipment and explicitly purchased AAs against
Lord Nagafen (32040, soldungb) and Lady Vox (73057, permafrost). It does not establish
obtainable full BiS, an optimal pet strategy, or a release AA whitelist.

## Controller and preparation

The normal connected, non-GM client summons Greater Conjuration: Water 633,
Invoke Death 443 and Frenzied Spirit 166 through native casts and reagent inventory.
Talisman of Altuna 168, Chloroplast 145 and the appropriate fire 60/cold 61 resistance
buff prepare the owner and all three pets. Burnout III 107 targets the primary pet;
targeted Alacrity 170 buffs the extra pets. Native pet-target spells redirect to the
primary pet, so their effects are not fabricated on extras. Lich 644 prepares owner
mana regeneration. Arch Shielding 67 is omitted because native Talisman replaces it.

Repeated preparation casts wait for actual per-spell timers. The initial prototype
failed this at the unrestricted-AA stage: faster Talisman casting finished before
the previous recast timer expired, producing message 236 and leaving one pet
unbuffed. The final controller waits instead of treating CastSpell acceptance as
proof a spell landed. Buff presence is checked after preparation.

Preparation uses native sitting and Greater Healing 15 until mana is full, pet HP
is full, owner HP is at least 95%, and the owner is standing. Lich prevents requiring
exact full owner HP on every pulse. This recovery has a 15-minute upper bound and
records resource snapshots, healing requests and elapsed time. No resource reset
occurs between preparation and combat. Out-of-combat gem changes do not simulate
client memorization time; the subsequent recovery is native.

Eight gems are selected once before each encounter:

| Gem | Nagafen | Vox |
| --- | --- | --- |
| 1 | Greater Healing 15 | Greater Healing 15 |
| 2 | Togor's Insects 507 | Togor's Insects 507 |
| 3 | Malosi 112 | Malosi 112 |
| 4 | Envenomed Bolt 436 | Envenomed Bolt 436 |
| 5 | Plague 32 | Ignite Blood 6 |
| 6 | Blizzard Blast 510 | Blaze 120 |
| 7 | Cannibalize II 754 | Cannibalize II 754 |
| 8 | Drain Soul 447 | Drain Soul 447 |

The owner begins 80 units from the boss, enables primary pet taunt, then sends the
native attack order. Self-healing below 55% and pet-healing below 65% take priority.
Malosi, slow, Cannibalize, missing DoTs and reserve-mana filler spells follow.
Repeated debuff/DoT attempts are separated by at least 30 seconds; the first pilot's
shorter retry repeatedly spent casts on resisted slow. The final rotation uses
native recast checks and spell recovery. Purchased burst AAs use the existing
native activation controller, with one attempt per owned selected ability.

Owner movement uses native pathfinding, native speed and ordinary position/history
packets to return within 80 units with line of sight after displacement. It pauses
for control effects, casting and affordable emergency healing. Sitting recovery
is conditional on aggro and resources. This is not continuous kiting. There is no
pet resummoning, midfight gem swapping, owner autoattack, pet equipment/focus
optimization or complete active-AA rotation.

## Results

See `pet-support-checks.json` for every outcome, actual spent AA points, duration,
healing requests and native damage accounting. The requested stages 0/100/200/500
spend 0/100/199/494 points; the unrestricted closure spends 13,288. These are open-pool
sensitivity comparisons. **Unrestricted all is a stress test, not Classic's
release maximum.** All legal AAs for an expansion must be defined by its curated
ability list, rank caps and prerequisites. A requested budget can exceed that
pool's cost; report exhaustion and actual expenditure instead of inventing ranks.

| Actual spent AAs | Boss | Wins / three samples | Outcome time range |
| ---: | --- | ---: | --- |
| 0 | Nagafen | 0/3 | 251.75-671.60s |
| 0 | Vox | 3/3 | 596.45-656.55s |
| 100 | Nagafen | 0/3 | 715.95-849.15s |
| 100 | Vox | 3/3 | 593.95-735.40s |
| 199 | Nagafen | 1/3 | 311.05-854.70s |
| 199 | Vox | 3/3 | 510.55-674.20s |
| 494 | Nagafen | 3/3 | 660.70-719.70s |
| 494 | Vox | 3/3 | 616.10-691.80s |
| 13,288 (stress) | Nagafen | 3/3 | 334.35-363.15s |
| 13,288 (stress) | Vox | 3/3 | 60.50-202.00s |

Three seeds are diagnostic samples, not estimated win probabilities. Failed runs
measure this controller under these conditions, not impossibility for the class.
Boss resistances and owner healing pressure can dominate AA improvements. Short
unrestricted fights on another build do not establish this build's ceiling.

The final corrected matrix has one Nagafen victory at 199 spent points, compared
with none at 0 or 100 and three at 494. Vox wins occur at every sampled stage.
No sampled slow lands; Ignite Blood contributes native damage against Vox while
the disease/poison effects fail to produce damage against Nagafen. This supports
further resistance-aware strategy and role-specific AA review, not a universal
AA requirement or an NPC HP change. The table includes times to death as well as
times to victory; it is not a kill-time table for the losing rows.

The native boss HP ledger includes root Damage calls and excludes nested double
counting and negative terminal HP. Gross damage can exceed starting HP because
Vox heals and NPCs regenerate. Observed client packets can omit distant actors and
are not a complete damage meter. Owner/boss death uses diagnostic terminal adapters;
surviving pets at that instant do not certify real owner-death persistence.

## Reproduction and remaining work

From `tools/balance`:

```powershell
python -m unittest discover -s tests
python pet_support_controls.py --inputs ../../docs/balance/pet-support-inputs.json --verify ../../docs/balance/pet-support.json.gz --output ../../docs/balance/pet-support-checks.json
```

`pet_support_controls.prepare` regenerates 30 cases: two bosses, five AA stages and
seeds 1729–1731. The build manifest pins the four spells/attack/mob/client-packet
candidates and 130 native objects/archives. This remains a partial native build,
not fresh complete-source parity. The evidence manifest records source fingerprints,
regressions and clone-only reagent cleanup.

All 35 previous native reports (12 command/combat, 15 ownership and eight
caster/monk) remain byte identical. All 211 Python tests pass, including rejection
of altered resources, missing buffs, wrong spell gems/targets, invalid victory
claims and unbounded movement. After the runs, the two verified synthetic
inventory rows were removed; clone accounts, characters and inventory are empty.

Remaining balance work includes obtainable gear/quest/merchant/focus challengers,
role-specific curated AA pools, stronger player strategies, wider seeds and live
client parity. Do not change global HP or spell caps on the strength of one weak
controller or unrestricted AA access.

On eventual promotion to test, explicitly QA:

1. Use a level 50 MAG/NEC/SHM character with the recorded gear and exact purchased
   ranks. Confirm the owner and pet buff roster and normal reagent consumption;
   at the unrestricted stress stage, repeat Talisman on all pets without bypassing
   its recast timer. It must land on each pet after the timer expires.
2. In soldungb, fight Lord Nagafen 32040 with the listed cold-oriented eight gems;
   in permafrost, fight Lady Vox 73057 with the fire-oriented set. Verify pet attack
   orders, primary taunt, healing targets, fear/control, return movement and mana
   expenditure. Record combat logs, starting resources, deaths and elapsed time.
3. Repeat at 0/100/199/494 spent points and the proposed release maximum. Label a
   separate 13,288-point run as unrestricted stress only. Compare direction and
   mechanics with the recorded samples; do not require an identical RNG outcome.
4. Check pet death/resummoning and owner death/zoning/relog separately, since this
   controller does not model those persistence transitions. Main promotion still
   requires owner sign-off after manual QA.
