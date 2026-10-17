# AA progression and release-pool review — October 17, 2026

The owner requested a progression/exclusion review after Palwar reached roughly
1,000 AA in his twenties. The owner prefers fast progression and more choices,
then explicitly requested reducing passive AA to 10%. **That rate is deployed;
the AA expansion ideas below are recommendations only.** No rank, purchase cost,
class mask, prerequisite, player record or combat formula changed.

## Production findings

The read-only 14:58 UTC snapshot has Palwar at level 27, Paladin/Warrior/Monk,
1,018 spent points, 80 banked, 2,897 partial AA XP (72.425% of the next point),
and allocation zero. These are saved values, not continuous telemetry or his
complete earning history. He was saved in Unrest, whose zone multiplier is 1.73.

All four live AA tables exactly match the reviewed catalog fixture. The deployed
build manifest matches the generated policy and XP source (allowing CRLF-only
normalization). Current policy remains 394 families / 1,051 ranks, available
from level 1 with class eligibility and prerequisites. His class/prerequisite
closure contains 139 families / 386 ranks costing 1,673 points. All those ranks
have unrestricted ordinary race/deity masks and status zero in the catalog.

Of Palwar's spent points, 1,015 fund currently legal ranks. The other three are
earned Combat Fury rank 4 (family 30, rank ID 443), preserved but excluded by the
three-rank cap. Do not erase, refund, or repurchase it as part of this review.
The normal ownership projection should restore it if that rank becomes legal.
There are 658 points of unbought legal ranks, or **578 new points needed after
his 80 banked points**. This is the full eligible catalog, not 578 points of
equally useful combat upgrades.

He already owns the released caps of Slay Undead 9, Master Wu 5, Healing Adept 9,
Healing Gift 12, Shield Specialist 5, Natural Durability 3, Combat Stability 3,
Combat Agility 3 and Monk Strikethrough 3. Recommending the October 13 Slay/Wu
expansion again would not give him new progression.

## What the percentage means

With focus off, normal leveling XP remains whole. The server separately computes
the full AA award, applies its modifiers, then awards 10% of that amount. Every
4,000 AA XP becomes one point; remainder carries. Focus on gives 100% of the full
AA award and no normal leveling XP or additional passive bonus. The AA window's
progress bar is progress toward one point; it is not this passive allocation rate.

The live normal and AA multipliers are both approximately 0.65. Modern scaling
and normalized-kills mode are disabled, with no AA award or banked-point cap.
The configured 25-white-kills rule is inactive while normalized mode is false.
Zone/con/level modifiers and rounding can change individual kills. A half-rate
award does not guarantee half as many displayed points on a particular kill.

With equal normal/AA modifiers, 10% and 4,000 XP/point imply roughly one passive
AA per 40,000 normal XP (previously 20,000). At a simplified unmodified level-50
threshold of 164,708,600 XP, continuous 10% earning from creation would produce
about 4,118 AA. This ignores deaths, boosts, quests with different modifier paths,
focus, prior rates and rounding; it cannot reconstruct Palwar's actual history.
Starting from his snapshot, 578 additional points cost about 23.12 million normal
XP, placing complete funding near level 35 on that ideal curve. See analysis.json.

The main concern is therefore **running out of worthwhile choices**, even at 10%.
The owner's observation that this build is not crushing encounters is encouraging,
but does not establish all-build balance. Measure healing, mitigation, downtime,
undead versus living targets, pet power and upcoming independent Monk attacks too.

## Recommended release candidates

Keep level-1 availability. Use deliberate rank ceilings, prerequisites and costs;
do not restore the rejected character-level purchase gates. Evaluate one combat
package at a time, with the current gear and buffs held constant.

| Candidate | Current → first candidate | Why / limitation |
| --- | --- | --- |
| Innate attributes and five resist lines | 3 → 15 | Adds steady gearing/resist options: raw bonus 6 → 30 per line. Twelve lines add 144 native-cost points. Stats may already be capped; do not advertise universal DPS gains. |
| Innate Run Speed; Lung Capacity | 3 → 5; 3 → 6 | Native movement bonus 21 → 35 and a final water-breathing effect. Ten additional points per line. Test escape/kiting and buff interactions. |
| Planar Power | 3 → 5 initially | Adds stat-cap headroom, not stats; four additional native-cost points. Useful only when gear reaches caps. |
| Combat Fury, family 30 | 3 → 4 first, then assess 5–6 | Restores Palwar's already-earned fourth rank; full six-rank prefix moves the crit-chance bonus input 75 → 150, not a 150% actual crit chance. Audit dependency unlocks before changing the cap. |
| Monk Strikethrough | 3 → 4 first, then assess 5–6 | A gradual damage-reliability option; bonus input 15 → 20 initially and 30 at rank 6. Fifteen points for all three extra ranks. Test against avoidance and combined melee classes. |
| Punch Mastery, family 3511 | 0 → 1, explicit later-era exception | New Monk choice: +15 skill-damage inputs, +30 for Dragon Punch. At low level this is substantial flat damage. Test with Slay Undead, Master Wu and the independent-cooldown candidate before release. Do not open all ranks by default. |
| Destructive Fury, families 397/398 | 0 → 1 as a separate caster experiment | Existing spell-crit prerequisites are now reachable after October 13. Test both families together when held classes qualify; spell-damage gear and critical bonuses compound. Preserve prerequisites. |
| Companion's Fury, family 1205 | 0 → 1, explicit later-era exception | Shallow additional pet-crit choice, assessed with existing pet crit families and all owned pets. Do not infer pet balance from Palwar. |
| Gate / Perfected Levitation | First rank, class masks preserved | New convenience choices outside the original cutoff. Travel, escape and terrain access matter; no broad class-mask widening. |

The modest general options above add only hundreds of native-cost points, so they
will not by themselves provide a long endgame progression. Before a larger AA
release, choose an intended useful spend budget per representative triple and
price newly introduced ranks accordingly. Preserve existing purchased costs and
ownership; do not fill the pool with ineffective ranks simply to consume points.

## Exclusions that need more than a policy toggle

- **Rapid Strikes (273):** rank 1 supplies flurry bonus 7 and costs four points.
  The inspected native attack path attempts flurry only after a successful
  main-hand triple attack. A fresh production query has ClassicTripleAttack=false
  and the first positive Triple Attack skill cap at level 46 for Warrior/Monk
  (56 for Paladin). This is not a useful new level-27 button/passive without an
  activation review. Tracked attack.cpp/mob.cpp differ from the retained deployed
  file hashes, so confirm the exact deployed path before claiming a live defect
  or designing a repair. The source-level warning and live skill-cap data are
  sufficient to keep this out of the first simple unlock package.
- **Warrior Flurry (108):** its prerequisite is Combat Fury family 309, which
  is disabled. Family 309 is distinct from Palwar's enabled family 30. Removing
  the deferral alone does not create a purchasable, functional chain.
- **Critical Mend:** the next native rank jumps its bonus from 30 to 68 for two
  points. Test sustain before opening the full 84 endpoint.
- **Combat Stability/Agility:** retain a separate defensive review. Opening
  every in-era rank raises bonus inputs from 10 to 45/39; these are not direct
  damage-reduction percentages, and PAL/WAR/MNK already stacks healing/defense.
- **Finishing Blow, Headshot, Decapitation:** keep executes deferred initially.
  Finishing Blow rank 1 already carries a 16,000 damage parameter; exact native
  target/HP/level restrictions are essential at a level-50 cap.
- **Cannibalization, Gather Mana/Mana Draw, Mana Burn, Life Burn, Mortal Coil,
  Improved Twincast and stacked defensive rotations:** defer pending matched
  sustain/burst tests. Temporary AA timers were repaired October 16, but that
  makes reevaluation possible; it is not evidence these interactions are balanced.

## Next gameplay measurements

Compare current AA, then one proposed package, using the same weapons, armor,
augments and ordinary buffs. Include Palwar against living and undead Unrest
enemies, another melee triple, caster/healer and pet/DoT triples. Record target
level/HP, damage taken, kill time, mana/endurance use, recovery time and cooldown
use over repeated comparable fights at early, middle and level-50 progression.
Recheck saved ranks, purchases, banked points and class-release behavior across
zone/relog. Treat the independent Monk cooldown release as a distinct test input.

No new AA is enabled by this report. Native policy tests do not prove fun or
encounter balance, and one player's observations cannot establish all-build power.

## Evidence and reproduction

- production-snapshot.json.gz and analyze.py: four AA tables, Palwar snapshot,
  canonical purchases, rules and zone data; private repository evidence.
- analysis.json: exact legal costs, dormant rank and idealized progression math.
- preflight.json: current binary fingerprints, retained manifest and local source
  comparisons. The complete client_packet.cpp differs; do not claim all source
  bytes matched. XP and generated policy match as recorded.
- config/aa-policy.json; tools/aa_tbs_policy.py; server-mods/code/zone/exp.cpp;
  common/nightcap_aa_policy.h; inspected bonuses.cpp, attack.cpp and mob.cpp.
- Earlier effect/prerequisite inventory: docs/audits/aa-class-ranks-20261013/
  and docs/audits/aa-tbs-20261013/. The fresh catalog comparison validates their
  AA content for this review; it does not refresh old spell or gameplay evidence.

Run `python docs/ops/passive-aa-ten-20261017/analyze.py` from the task checkout.
