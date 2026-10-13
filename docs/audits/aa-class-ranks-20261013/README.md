# Class AA rank-depth re-audit — October 13, 2026

**Recommendation, not deployed:** replace the one-rank Slay Undead cap with its
full nine-rank Buried Sea prefix, and test the 26 explicitly identified AA lines
below at their listed ceilings. The earlier generic three-rank ceiling was too
coarse for class identity. The cutoff and an AA's natural in-era rank depth are
different things. Every allowed rank remains available at character level 1;
class eligibility, prerequisites and earned point costs still apply.

The proposed pool has **394 families / 1,051 ranks**, versus the deployed
**390 / 941**. All 941 currently allowed rank identities remain allowed. This
adds 110 ranks, including four deliberately restored prerequisite-dependent
families. It adds no post-TBS exceptions. These are catalog and source findings,
not measured encounter balance or owner acceptance.

**Implementation blocker found:** Triple Backstab's native roll requires level
55 under the live rule, above Nightcap's level-50 cap. Its proposed rank 9 is
conditional on repairing that activation path. The candidate config models
target rank availability; deploying it alone would not fix this defect.

## Slay Undead: nine ranks already fit

Ability 75 currently stops at rank 1 because of our explicit policy cap, not
because of The Buried Sea. Its complete in-era chain is:

| Rank | Expansion tag | AA cost / cumulative | AA-only Slay roll | Native damage factor |
|---|---:|---:|---:|---:|
| 1 | 3 | 3 / 3 | 6.8% | 2.25 |
| 2 | 3 | 6 / 9 | 11.9% | 2.35 |
| 3 | 3 | 9 / 18 | 17% | 2.40 |
| 4 | 10 | 7 / 25 | 18% | 2.60 |
| 5 | 10 | 7 / 32 | 19% | 2.80 |
| 6 | 10 | 7 / 39 | 20% | 3.00 |
| 7 | 12 | 7 / 46 | 21% | 3.30 |
| 8 | 12 | 7 / 53 | 22% | 3.60 |
| 9 | 12 | 7 / 60 | 23% | 3.90 |

All nine require Combat Fury 3. The 60 points exclude that prerequisite's cost.
The next rank is expansion 19 (Rain of Fear), not a hidden TBS rank.
[Exact IDs and costs](slay-undead.csv).

The retained live source tests Undead, Summoned Undead and Vampire body types.
At the observed Slay rate/damage rules of 1.0, it divides the rate by 10,000,
and on success multiplies `max(hit.damage_done, hit.base_damage) + 5` by the
listed factor, with integer truncation and a minimum-damage floor. A successful
Slay returns before the ordinary melee-critical branch. Item/spell Slay bonuses
can contribute too. **The factors are not final DPS multipliers** and the rolls
are per eligible Slay check, not percentages of all attempted swings.

This scales physical hit damage against a narrow target category. The native
special-attack path can also reach Slay for kicks and backstabs; it is not
restricted to ordinary weapon swings. Rank 9 is
a reasonable full-depth QA candidate. Its 23%/3.9 endpoint is still substantial:
test undead camp clearing, PAL/WAR/MNK kick damage and attack frequency before calling it
balanced. Do not replace the one-rank cap with another arbitrary three-rank cap.

## Recommended candidate: 26 lines

These recommendations favor identifiable, incremental class progression. All
ceilings below are the natural contiguous TBS prefix. Percentage values describe
the AA bonus itself, not guaranteed changes in total DPS, healing or hit rate.
They still need the combined-build checks below.

| Class / scope | AA (ability ID) | Current → candidate | Reason / endpoint to test |
|---|---|---:|---|
| PAL | Slay Undead (75) | 1 → 9 | Full undead specialization; 60 points before prerequisites. |
| MNK | Technique of Master Wu (206) | 3 → 5 | DoubleSpecialAttack 60 → 100. Native extra-attack loop also rolls diminishing additional attacks; it is not limited to THJ's stated three-attack model. |
| RNG | Trick Shot (557) | 3 → 6 | DoubleRangedAttack 6 → 12; preserves ordinary bow damage scaling. |
| ROG | Triple Backstab (281) | 3 → 9, conditional | TripleBackstab 15 → 45; first fix the native level-55 activation blocker described below. Position/weapon/attack checks still matter. |
| ROG | Poison Mastery (103) | 3 → 4 | ReduceTradeskillFail 50 → 75 for Make Poison; crafting utility rather than a raw damage multiplier. The application-time effect is unimplemented in the retained AA bonus switch. |
| WAR | Shield Specialist (605) | 3 → 5 | Shield-equipped damage modifier 15 → 25; supports a shield build. |
| BRD | Instrument Mastery (90), Singing Mastery (118) | 3 → 4 each | AddSingingMod 6 → 8 for the relevant instruments/singing; audit with instrument gear. |
| BRD | Extended Notes (227) | 3 → 6 | Song range 25 → 65; utility without direct damage inflation. |
| BRD / BST | Harmonious Attack (187), Bestial Frenzy (186) | 3 → 10 each | GiveDoubleAttack 9 → 30 each; both sum if held together. See combined-build warning below. |
| BST / MAG | Warder's Fury (248), Elemental Fury (266) | 3 → 10 each | PetCriticalHit 3 → 10 each; steady investment in pet offense. |
| SHD / NEC | Death's Fury (278) | 3 → 5 | PetCriticalHit 3 → 5. |
| NEC | Death's Wrath (665) | 0 → 5 | Explicitly restore dependency after Death's Fury 5; adds up to 5 PetCriticalHit. |
| WIZ | Spell Casting Fury Mastery (114) | 3 → 11 | Spell critical-chance contribution 6 → 17. Keep Destructive Fury's separate deferral during this test. |
| Listed caster/hybrid classes | Fury of Magic (215) | 3 → 9 | Spell critical-chance contribution 6 → 15; can combine with the Wizard-specific line. |
| Listed DoT classes | Critical Affliction (259) | 3 → 6 | CriticalDoTChance 9 → 18; unlocks the following reviewed chain. |
| DRU / SHM / NEC | Affliction Mastery (526), Blood Tithe (740) | 0 → 3 each | Adds 6 then 4 DoT critical-chance points; prerequisites preserved. |
| NEC | Greater Blood Tithe (628) | 0 → 3 | Adds 3 more DoT critical-chance points. |
| CLR / PAL / RNG / DRU / SHM / BST | Healing Adept (18) | 3 → 9 | Eligible instant-heal focus 10 → 28, retaining effect/spell limits. |
| Same healing classes | Healing Gift (19) | 3 → 12 | CriticalHealChance 10 → 28; test healing throughput and resource use together. |
| SHD | Soul Abrasion (89) | 3 → 6 | Focus for spell group 99 rises 200 → 250; do not describe this as all lifetaps or all procs. |
| ENC | Enhanced Forgetfulness (262) | 3 → 5 | IncreaseChanceMemwipe 30 → 50; a modifier, not a guaranteed 50% success rate. |
| BER | Conservation (504) | 3 → 5 | Eligible reagent-saving focus 30 → 50. Blur of Axes needs separate damage tuning below. |

Exact class masks, costs and effect strings are in
[recommended-caps.csv](recommended-caps.csv). Shared AAs are purchased once;
holding multiple eligible classes does not duplicate the same ability. Different
ability IDs contributing to the same bonus can stack.

### Rogue activation defect

In the retained `special_attacks.cpp`, the Triple Backstab roll is inside the
double-backstab branch requiring `level >= DoubleBackstabLevelRequirement`.
The fresh [rule query](additional-rules.json) returns 55 for ruleset 1; the
active global maximum is 50. Normal rear/Seized Opportunity backstabs therefore
cannot reach the triple roll at Nightcap's allowed levels. Chaotic Stab's
minimum-damage frontal branch explicitly does not use that roll either.

Repair the path so an earned, legal Triple Backstab AA can take effect from
level 1 while preserving its prerequisite double-attack check, weapon and
position rules. Do not silently lower all characters' native double-backstab
level requirement as an unrelated side effect. Add a native level-1/50
earned-AA/control regression before including this rank expansion in a release.
This audit identifies the defect; it does not patch it or claim a reproduction
in the player's client.

### Dependencies that must be deliberate

An unguarded expansion of the recommended lines would restore seven previously
blocked families. Four are explicitly included above. Three remain at their
current zero usable ranks in the audit candidate:

- **Dance of Blades (359)** needs Harmonious Attack 5. Its spell has
  DoubleAttackChance 500, DualWieldChance 100 and a weapon proc. Audit the burst
  and Nightcap's actual AA buff lifetime before restoring it.
- **Hastened Blades (541)** needs Dance of Blades 3; review with that ability.
- **Abundant Healing (516)** needs Healing Gift 7. It triggers additional healing
  and includes spell-level 60–75 focus limits. Verify the effective focus checks
  and custom spell data before offering a possibly ineffective or excessive line.

These guards remove no currently usable ranks. They are not character-level
gates. [Dependency audit](dependency-unlocks.csv).

## Other class lines: scale or retune, not a blind full-rank unlock

The complete [188-family inventory](rank-inventory.csv) includes every enabled,
uncharged, non-veteran, non-grant-only in-era line whose contiguous prefix exceeds
its current legal cap, including generic AAs and prerequisite-blocked lines.
Each has current/proposed/natural caps, costs, free ranks and effects. The
following are the important second-pass decisions; numbers are current → natural
TBS depth, **not additions to the candidate above**.

| Class | Further candidates | Why they need a different treatment |
|---|---|---|
| WAR | Sturdiness 3 → 10; Tactical Mastery 3 → 9 | Sturdiness is flat 300 → 1,000 HP; could replace early gear. Check strikethrough with offensive gains. |
| CLR | Celestial Regeneration 3 → 9; Divine Avatar 3 → 6; Turn Undead 3 → 6 | Mana-free recovery, large melee modifiers and linked attack spells require real uptime/encounter checks. |
| PAL | Lay on Hands 3 → 17; Hand of Piety 0 → 12; Fervent Blessing 0 → 3 | The first ten Lay on Hands ranks cost zero; later ranks unlock heal/cooldown families. Review together, rather than claiming points constrain them. |
| RNG | Precision of the Pathfinder 3 → 9; Headshot 0 → 7 | Accuracy is a rating bonus. Headshot starts at 32,000 fixed damage and reaches 60,280; raw admission would erase much Classic content. |
| SHD | Touch of the Cursed 3 → 6; Theft of Life 3 → 11; Harm Touch 3 → 18 | Proc healing, healing criticals and formula-based damage interact. First ten Harm Touch ranks are free. Mortal Coil remains separate. |
| DRU | Spirit of the Wood 3 → 9; Nature's Boon 3 → 11 | Regen/shield uptime and ward NPC healing need spell/pet data and actual fights. |
| MNK | Kick Mastery 3 → 9; Critical Mend 3 → 6 | Kicks add flat 30 → 90 alongside Master Wu; Mend jumps from 30 to 68 at rank 4. These are not evenly sized steps. |
| BRD | Dance of Blades 0 → 3 | Review the attack burst and AA buff lifetime; explicitly held out above. |
| ROG | Virulent Venom 3 → 5; Anatomy 0 → 8 | Proc gains need real poison data. Anatomy/Assassinate starts at 32,000 and reaches 65,440 fixed damage; retune before admission. |
| SHM | Ancestral Aid 3 → 6; Spirit Call 3 → 5 | Aid combines healing procs and melee modifiers; swarm performance requires NPC data and owner-bonus routing. |
| NEC | Quickening of Death 3 → 5 | Pet flurry contributes 12 → 20, on top of other held pet classes. |
| WIZ | Improved Familiar 3 → 4; Destructive Fury 0 → 9 | Inspect familiar benefits and critical-damage interaction after the frequency increases, not simultaneously without measurements. |
| MAG | Elemental Alacrity 3 → 11; Servant of Ro 3 → 6; Host of the Elements 3 → 6 | Pet flurry rises 12 → 50; swarms need NPC and lifetime evidence. |
| ENC | Eldritch Rune 3 → 8; Deep Sleep 3 → 5 | Rune absorption doubles 1,500 → 3,000; triggered debuffs need boss/stacking tests. |
| BST | Warder's Alacrity 3 → 11; Paragon 3 → 7 | Pet flurry rises 12 → 56; recovery can eliminate attrition. |
| BER | Blur of Axes 3 → 13; Cascading Rage 3 → 5 | Flat Frenzy bonus rises 96 → 416. Prioritize a deliberate scaling curve so Berserker also gains meaningful combat progression. |

Hunter's Attack Power has 26 in-era ranks, all free. Expansion tags alone also
put the long knight touch chains in the legal era. These are strong reasons to
review effect/cost curves instead of treating either the expansion cutoff or a
uniform rank number as sufficient balance evidence.

## What THJ evidence actually establishes

Retrieved October 13 from search-indexed THJ-Wiki class pages. These are historical
documentation, not a current THJ database dump. Direct wiki/database availability
was unreliable: eqdb.net returned 410, the old wiki hostname failed DNS, and
direct Gilead requests failed TLS/timed out. No accessible source confirmed the
exact THJ Slay Undead ceiling. The user's recollection remains plausible but
unverified; **Nightcap's nine-rank finding is from Nightcap data**.

- [THJ Monk](https://thj.gileadgames.net/classes-and-abilities/classes/monk/)
  describes Master Wu increasing by 20% through rank 5 and further ranks improving
  the third attack by 5%. This supports preserving a complete class progression
  line. Nightcap's retained native extra-attack loop differs; don't copy the
  advertised THJ percentages onto Nightcap's post-five ranks.
- [THJ Paladin](https://thj.gileadgames.net/classes-and-abilities/classes/paladin/)
  documents customized, out-of-era AAs tuned for that server. It does not provide
  the needed Slay rank/effect table.
- [THJ Ranger](https://thj.gileadgames.net/classes-and-abilities/classes/ranger/)
  describes substantial bow-combat changes and progressive Trick Shot. Those
  combat differences prevent direct transfer of THJ balance conclusions.

THJ also used level-based autogrants for some lines. Nightcap's required policy
is different: every allowed rank purchasable at level 1. Do not import THJ gates,
autogrants or damage values as part of this recommendation.

### Beyond TBS

Restore the substantial in-era depth first. The next increments include Slay 10
(expansion 19: 24% / factor 4.20), Master Wu 6 (15: DoubleSpecialAttack 120),
Trick Shot 7 (15: 14), Triple Backstab 10 (14: 48), and pet critical rank 11
(14: 11). They are possible later candidates, but no evidence here requires
another era exception to fix today's overly shallow class trees. Slay 9 and
Master Wu 5 already solve the immediate rank-depth issue.

## Verification, evidence and QA boundary

The October 13 12:56:55 UTC read-only OVH check matched all four AA tables to the
captured fixture and confirmed the level-1 correction image still running. Its
anonymous ownership count was **240 rows / 1,194 earned ranks**, one row/rank more
than the earlier deployment receipt; normal play continued during this audit.
No SQL, rule, purchase, binary, client or active-policy writes were made.
[Fresh production check](production-check.json).

The AA snapshot is from 09:33 UTC; linked spell descriptions above use that
snapshot and are not a fresh full spell-table verification. Retained source
hashes are pinned to the live release's build manifest. The checked `attack.cpp`
differs from the tracked overlay, so this audit uses the retained build source.
See [source evidence](source-evidence.json) and the
[release manifest](../../releases/aa-tbs-level1-20261013/build-manifest.json).

Reproduce with `python -X utf8 docs/audits/aa-class-ranks-20261013/analyze.py`.
The script writes only this audit directory. It uses the production policy
compiler, preserves identity and prerequisite closure, asserts level 1 for every
candidate row, retains every current legal rank, and admits no explicitly
deferred family or new later exception. The proposed config is an
[audit-only artifact](candidate-policy.json), not the active policy.

All 16 individual classes and eight representative triples have conservative
class-prerequisite-closed [coverage counts](coverage.csv). Counts omit race and
activation constraints; they are not encounter strength. For example,
PAL/WAR/MNK grows from 353 to 386 ranks; MAG/BST/NEC from 365 to 426.

Before deployment, test each offensive line at the current cap and proposed cap
with equal level, gear, spell selection and recorded spent points. Use creation,
mid-progression and level-50 profiles, with ordinary enemies, harder encounters,
and repeated pulls. Test both prerequisite-only investment and the combined pool.
Measure time to kill, incoming damage, resource drain, healing, deaths, recovery,
proc rates and reward acquisition. Do not substitute unlimited-AA stress results
for an achievable build.

Specific high-value comparisons:

1. PAL/WAR/MNK against undead and matched living targets, including Unrest and
   Lower Guk camps: rank 1/3/6/9 Slay, Master Wu, weapon/gear scaling, and kicks.
   Test Kick Mastery separately before expanding it because physical skill damage
   can feed Slay's multiplier too.
2. MAG/BST/NEC: the four proposed pet critical lines sum to **30** bonus points,
   versus 9 now. Confirm how every controlled pet receives them. Blindly opening
   all three pet-flurry lines would sum to **126**, versus 36 now; that is why
   flurry is a separate tuning task.
3. BRD/BST/PAL: the two GiveDoubleAttack contributions rise from 18 to **60**;
   the native formula also depends on skill/level and other double-attack bonuses.
   Measure that combination with Slay; 60 is not universally a 60% final chance.
4. WIZ plus a Fury-of-Magic class: the two contributions become **32** spell
   critical-chance points before other bonuses. NEC's reviewed DoT chain totals
   **31**. Keep critical-damage burns separate for this comparison.
5. CLR/SHD/SHM and pet/healer variants: Healing Adept/Gift, current Theft of Life,
   Soul Abrasion and proc heals must preserve mana pressure and recovery costs.
6. RNG bow and ROG backstab builds: compare ordinary and positional fights;
   reward their specializations without depending on fixed-damage executes.

If the user later approves implementation, first repair/test the Rogue activation
defect (or omit its expansion until repaired), regenerate the policy/header, rerun
native purchase/projection/save tests, and deploy a matching zone build through
the guarded runtime process. Normal AA reload cannot install a compiled policy.
Preserve earned purchases; newly legal earned ranks should reactivate without
repurchase. No client binary change is anticipated for these server-side changes;
publish accurate signed patch notes with that release. This audit itself creates
no launcher patch and makes no live QA acceptance claim.
