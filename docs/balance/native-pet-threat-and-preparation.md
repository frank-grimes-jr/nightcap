# Pet threat and preparation controls

Date: 2026-09-13. Native diagnostic work; no live tuning.

## Feign Death: mechanics work, tested policies do not solve the fight

The source-constrained MAG/NEC/SHM build retains its exact gear, creation stats,
AA purchases, preparation and eight combat gems. Two strategies replace the
previously unsuccessful slow gem with Feign Death 366:

- `no_slow_control` leaves that gem unused and removes slow attempts. This
  isolates the time/mana effect of dropping slow from the effect of using feign.
- `feign_on_aggro` casts only when the boss targets the owner, an owned pet is
  alive, the native recast timer is ready, and mana is sufficient. It waits while
  feigned, then sends the native standing appearance packet after four seconds.

A follow-up `feign_escape` requires owner HP at most 40% and every surviving
owned pet at least 80%, with a one-second hold. The native controller does not
edit HP, mana, hate or the feigned flag directly. It respects spell failure,
interruption, aggro memory, spell breaks, control effects and recast timers.
Standing requests and their packet processing are recorded. No casts or movement
requests are generated while the controller is holding feign.

Captured spell 366 is Necromancer level 16, costs 60 mana, casts in 1.5 seconds,
and has a 15-second recast. Native effect 74 rolls success; the captured base is
87 against a 0–99 draw. Observed post-cast feign is not equivalent to this raw
success chance because casts can be interrupted and later spells can break it.
`Character:FeignKillsPet` is false. Native level-35+ enemies can retain feign
memory; the diagnostic does not erase it. See `pet-threat-source.json` for spell,
rule and source evidence. The two dragons have high MR and ranged-spell immunity;
the lack of observed slow uptime is not a claim that they have slow immunity.

Each pilot uses Nagafen, seed 1729, and zero spend or one of the two legal AA
maxima. All nine cases end in player death:

| Actual AA spent | Policy | Seconds | Boss HP remaining | Living pets at end |
| ---: | --- | ---: | ---: | ---: |
| 0 | No slow | 579.05 | 8,121 | 0 |
| 0 | Feign on aggro | 232.40 | 28,097 | 0 |
| 0 | Emergency feign | 579.05 | 8,121 | 0 |
| 165 | No slow | 709.25 | 10,955 | 2 |
| 165 | Feign on aggro | 642.45 | 19,252 | 0 |
| 165 | Emergency feign | 112.85 | 27,433 | 3 |
| 306 | No slow | 656.75 | 4,921 | 2 |
| 306 | Feign on aggro | 747.40 | 24,322 | 0 |
| 306 | Emergency feign | 656.75 | 4,921 | 2 |

All three aggressive pilots contain observed successful feigns with positive
owner hate becoming zero and the boss switching away. Their failures therefore
cannot be attributed simply to an unimplemented hate-clear operation. Shifting
damage to these pets and pausing their support is not an automatic improvement.
The emergency policy casts once at 165 AA and never qualifies at the other two
stages. Its one successful feign also fails to save the owner.

These small pilots reject these specific policies as a baseline improvement;
they do not prove that skilled Feign Death use is useless. The larger aggressive
strategy matrix was not run; the pilot gave no reason to adopt that policy.
Pet survivability, support timing, resummoning and preparation remain distinct
questions. The optional policies remain disabled in the existing baseline.

## Resist Magic preparation

The previous pet preparation omitted Resist Magic 64, although the caster
controller included it. Captured data allows it at Necromancer 37 or Shaman 43.
It is a targeted magic-resistance buff; its presence is compatible with the
existing required buffs in the native pilot.

The resistance comparison adds exactly four native preparation casts, one for
the owner and one for each class pet, before Lich. It retains the original slow/
support combat routine, gear, AA allocations, commands and seeds. Native recovery
again reaches full mana, full pet HP and at least 95% owner HP. Verification
requires spell 64 to remain on all four actors after preparation; cast acceptance
alone is insufficient. `pet-resist-source.json` preserves the spell definition.

The preparation allowlist initially rejected spell 64 before a fight could run.
Adding it to the diagnostic does not change its native eligibility or spell
effects. There is no live spell edit. Buff memorization time is not separately
modeled, as in the previous preparation controller.

Across six distinct pet AA allocations, two bosses and three seeds (1729–1731),
all 36 comparisons verify. The table shows wins out of three. AA totals identify
actual purchased ranks in the proposed pools, not unrestricted AA budgets.

| Actual AA spent | Nagafen, original | Nagafen, +Resist Magic | Vox, original | Vox, +Resist Magic |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0/3 | 0/3 | 0/3 | 0/3 |
| 98 (later pool) | 0/3 | 0/3 | 0/3 | 0/3 |
| 99 (launch pool) | 0/3 | 0/3 | 2/3 | 0/3 |
| 165 (launch maximum) | 0/3 | 0/3 | 3/3 | 3/3 |
| 192 (later pool) | 0/3 | 0/3 | 2/3 | 3/3 |
| 306 (later maximum) | 1/3 | 0/3 | 3/3 | 3/3 |

With Resist Magic, launch-maximum Vox wins take 603.05–657.15 seconds and
later-maximum wins take 580.80–725.10 seconds. All 18 Nagafen samples end in
player death. The four additional preparation casts alter native timing and RNG
consumption: the shared seed does not hold each combat random draw constant.
Three seeds per allocation are insufficient to conclude that the buff itself
causes worse outcomes, or to estimate reliable population win rates. The measured
preparation change does not establish consistent dominance or solve pet survival.
Keep both reports and avoid using this result alone to justify higher caps.

These are candidate AA pools, not the complete expansion offering or enforced
live access. Removed abilities must remain unavailable in every baseline; each
expansion's “all” must stop at its retained, level-eligible rank caps. Preserve
0/100/200/500/all requested budgets while recording actual spend, unused points
and exhausted pools. Higher budgets must not silently unlock a later expansion.

## Verification and in-game QA

Generate and independently verify strategies with `pet_threat_controls.py`, and
resistance preparation with `pet_resist_controls.py`, using the source gear matrix
and native AA catalog. Run through the shared driver in the isolated runtime with
each input's pinned binary. All four existing native combat candidates remain in
the build; this is not a fresh complete source/header parity claim.

The complete balance suite passes 263 tests. Native evidence includes nine
threat-policy pilots, three resistance pilots and 36 resistance comparisons.
Twelve original reports remain byte-identical after adding threat policies; six
initial threat pilots remain byte-identical after adding the emergency policy.
The Resist Magic allowlist build preserves six original reports byte-for-byte,
and the full resistance matrix reproduces all three resistance pilots exactly.
Mutation tests reject changed gear/combat inputs, illegal feign conditions, and
missing retained resistance buffs even when the original cast was accepted.

Only `native_runtime.o` changes across these diagnostic builds; all four candidate
source hashes, other linked objects, harness and build flags remain unchanged.
The completed isolated run left two synthetic reagent rows; bounded cleanup
removed them and verified zero account, character and inventory rows. No live
server was restarted and no live binary, NPC HP, spell cap or AA access changed.
`pet-strategy-evidence-manifest.json` pins the inputs, reports, build manifests,
verification tools and tests for this pass.

Before test promotion, use a level-50 MAG/NEC/SHM character in soldungb with the
exact source-constrained loadout and AA ranks. Verify the RoF2 client can scribe
and memorize held-class Feign Death and Resist Magic; native minimum-level
acceptance alone does not establish that UI behavior. Summon the three pets,
apply the recorded preparation, and check spell 64 on the owner and all pets.
Compare fear interruptions, pet deaths, mana pressure and fight time against
Nagafen 32040; repeat resistance preparation against Vox 73057 in permafrost.
For feign QA, observe failed/successful casts, boss target changes, pet retention,
native cooldown, spell breaks and return to standing. Main requires owner sign-off.
