# Shared expansion AA candidates

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Candidate design and isolated evidence; no live whitelist applied.

`aa-release-candidates.json` defines one global ability/rank list for each policy.
Native class eligibility intersects that list for WAR/CLR/WIZ, WAR/CLR/MNK and
MAG/NEC/SHM. There are no artificial profile-specific overrides. A caster with
Warrior as a held class can buy the permitted Warrior passives too; overlapping
class abilities must be included in the combined power assessment.

`launch_core` is a candidate Classic pool of shallow defense, sustain, spell
critical and role passives. `later_core` deepens those ranks and adds one Monk
flurry family and Fury of Magic. It is later-rank sensitivity against the same
Classic bosses, level and gear, not a validated Kunark or other expansion release.
Its full legal pool contains every launch rank, preserving earned progression.

These are restricted combat cores for comparison, not a complete launch AA
offering. Remaining utility, hate-management and pet-support abilities need
review; omission here is not a decision to remove them from the server.

Both omit Improved Twincast 515 and Frenzied Devastation 308, whose unrestricted
burst contribution is already measured. They defer both Veteran's Wrath families
338/341 and Destructive Fury 398. Flurry 108 is excluded to avoid adding it alongside
Monk Rapid Strikes 273; the native catalogue also has a missing ability 309
prerequisite on 108 and 341. This comparison does not silently restore missing
prerequisites or treat their native omission as permission to add those families.

The free baseline is explicit: Origin 331, Eyes Wide Open 938 through rank 8, and
Nightcap Ancient Attunement 2220. Origin has its native origin effect. A subsequent
source audit corrected the earlier claim that Ancient Attunement was a verified
PoK gate: spell 99001 uses effect 33, which this engine handles as pet summoning,
with `poknowledge` as the pet lookup string. Recall behavior is not validated.
The combat controllers do not activate it, so this correction does not change
the recorded fights. See `acquisition-identity-audit.md`. Placeholder ability 0 is excluded, as are
the two Alaran Culture HP grants 1684/1685. These are candidate-era/data exclusions,
not claims that every omitted AA is overpowered. The changed zero-spend baseline
is measured separately from the prior free closure.

## Allocation and evidence rules

Requested budgets are 0/100/200/500 and all legal ranks in that pool. Purchases use
explicit role-prioritized prefixes, native rank costs and prerequisites. Requested
points can remain unused at a price boundary or when the pool exhausts. **All is
the pool maximum, not unrestricted access.** The full cap lists and exact rank IDs
are reviewable in the specification and input matrix.

| Profile | Candidate | Requested 100: spent | Requested 200: spent | Requested 500 / all: spent |
| --- | --- | ---: | ---: | ---: |
| war-clr-wiz | launch_core | 98 | 135 | 135 |
| war-clr-wiz | later_core | 96 | 198 | 261 |
| war-clr-mnk | launch_core | 99 | 141 | 141 |
| war-clr-mnk | later_core | 95 | 197 | 288 |
| mag-nec-shm | launch_core | 99 | 165 | 165 |
| mag-nec-shm | later_core | 98 | 192 | 306 |

The two policies yield 18 distinct profile/allocation pairs. Each is tested against
both bosses with seeds 1729–1731, for 108 native fights. Identical purchased
allocations share evidence across requested-budget aliases instead of rerunning
the same combat state. Native characters receive exactly the allocation's spent
points and end purchasing with zero wallet points; unused requested budgets are
reported in audit metadata, not modeled as an unspent character wallet balance.

Gear remains fixed within each profile: the existing augmented shield candidates.
WAR/CLR/WIZ uses the prepared caster controller; WAR/CLR/MNK uses native autoattack,
monk combat buttons and self-healing; MAG/NEC/SHM uses the corrected native belly-
casting support controller. Each retains its documented limitations. Different
controllers are not evidence of equal player mastery, and the gear is not yet
certified obtainable full BiS.

HP minima retain each controller's normalization: pet samples use the current
maximum HP, while caster/melee summaries reference prepared starting HP. Do not
treat these as identical cross-controller risk percentages when buffs change.

| Profile | Candidate maximum | Boss | Wins / three samples | Outcome duration range |
| --- | ---: | --- | ---: | --- |
| war-clr-wiz | launch_core: 135 | Nagafen | 3/3 | 111.90-184.25s |
| war-clr-wiz | launch_core: 135 | Vox | 3/3 | 227.30-338.05s |
| war-clr-wiz | later_core: 261 | Nagafen | 3/3 | 128.75-194.45s |
| war-clr-wiz | later_core: 261 | Vox | 3/3 | 105.05-275.45s |
| war-clr-mnk | launch_core: 141 | Nagafen | 3/3 | 501.45-510.50s |
| war-clr-mnk | launch_core: 141 | Vox | 3/3 | 512.45-531.65s |
| war-clr-mnk | later_core: 288 | Nagafen | 3/3 | 357.45-387.50s |
| war-clr-mnk | later_core: 288 | Vox | 3/3 | 454.75-499.50s |
| mag-nec-shm | launch_core: 165 | Nagafen | 2/3 | 740.35-900.00s |
| mag-nec-shm | launch_core: 165 | Vox | 3/3 | 596.25-715.30s |
| mag-nec-shm | later_core: 306 | Nagafen | 3/3 | 700.40-753.40s |
| mag-nec-shm | later_core: 306 | Vox | 3/3 | 603.75-662.55s |

## Reproduction and promotion

The launch core produces sampled victories for caster and melee builds, while
the pet build has two Nagafen victories and one 15-minute timeout at its maximum.
The deeper pet pool wins all three but still needs roughly 12 minutes. The caster
remains much faster. These samples support constraining unrestricted AA power;
they do not establish a finished release pool or justify a uniform cap/HP change.
Obtainable gear, stronger threat/support strategies and a broader AA review come
before final tuning. Three seeds are not a win-probability estimate.

All 108 records verify against regenerated whitelist allocations and exact native
purchases. The complete 229-test suite passes, including clean zero-AA HP deltas,
retained earlier ranks, rejected false budget aliases and absent burst activations.
After all matrices, two synthetic reagent rows were removed; clone accounts,
characters and inventory are empty. No live AA removal or other tuning occurred.

From `tools/balance`:

```powershell
python release_pool_controls.py --inputs ../../docs/balance/release-pool-inputs.json --verify ../../docs/balance/release-pool.json.gz --catalog ../../docs/balance/native-aa-catalog.json --output ../../docs/balance/release-pool-checks.json
python -m unittest discover -s tests
```

The input generator regenerates the global pool allocations from the captured
native catalogue, refuses invalid/duplicate policies, excludes unreachable ranks,
and records pool exhaustion. Native verification checks exact purchases, costs,
equipment, preparation, movement, combat actions and terminal states. A whitelist
is still only a candidate until obtainable gear and representative class strategies
meet the demanding solo design and in-game QA confirms native/client behavior.

Future enforcement must be declarative alongside `era.json`, cover both offered
and purchased ranks, preserve prerequisite closure, and explicitly reconcile
existing purchases. This diagnostic does not implement that deployment or remove
live AAs. A later pool is not assigned to an expansion until that expansion's
content and progression have been tested.

On test promotion, run the existing caster, monk and corrected pet QA against
Nagafen 32040 in soldungb and Vox 73057 in permafrost with exact candidate ranks.
Verify excluded AAs are unavailable, capped ranks stop at the declared maximum,
class eligibility remains native, early earned ranks survive a later unlock, and
points/refunds reconcile for existing characters. Record duration, deaths,
lowest HP, mana pressure and successful/failed encounter mechanics; compare
direction across stages rather than requiring deterministic logs. Main requires
owner sign-off.
