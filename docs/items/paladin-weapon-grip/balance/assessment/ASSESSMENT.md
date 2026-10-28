# Paladin weapon assessment — October 27, 2026

**Recommendation: test the concrete package below; do not ship it yet.** Small
accuracy and shield-block bonuses are useful differentiation, but cannot rescue
the rejected weapon ratios. Restore a credible physical baseline, preserve the
support stats through the quest chain, and give Defender a modest defensive edge.
Accept that an earned shield-AA build can favor 1H damage. Do not advertise a
universal “2H damage / 1H defense” split under the current combat rules.

This is a design assessment only. No gameplay definitions, executable profiles,
quests, client package or production state were changed in this assessment.
The previously implemented numerical table remains rejected.

## Recommended first test package

Values are final proposed item values, not increments. Accuracy applies in both
grips. Shield Block is the additional percentage-point contribution, active only
with the supported weapon in primary, 1H grip, and a shield equipped. Normal
frontal eligibility, rear-block permissions, counters and strikethrough still apply.

| Quest stage | 1HS damage/delay | 2HS damage/delay | Accuracy | Added Shield Block |
|---|---:|---:|---:|---:|
| Ascended SoulFire | 26/30 | 46/45 | 10 | 0 pp |
| Ascended Fiery Avenger | 30/30 | 66/44 | 15 | 1 pp |
| Fiery Defender, normal epic | 32/30 | 64/40 | 20 | 2 pp |
| Ascended Fiery Defender, separate forge | 36/30 | 72/40 | 25 | 3 pp |

Keep new Avoidance, Shielding, haste, strikethrough and combat-effects bonuses at
**zero** in this candidate. Accuracy supplies modest offensive differentiation;
the small shield-block progression supplies a distinct defense benefit. Adding
multiple overlapping defensive systems would make attribution and tuning harder.
Shielding is a different mitigation statistic: do not write these block values
into the `items.shielding` field. Shield Block requires the existing SPA320 path
or a correctly gated native bonus. There is no observed worn effect on these
four weapons to preserve, but a new worn effect would still require client/spell
delivery and stacking validation.

The 1H physical floor is deliberate: at level 50 in the fixed-coefficient
comparison, SoulFire 26/30 and Ghoulbane 30/34 are equal before accuracy with no
shield-damage AA. SoulFire is only 0.83% behind with the 100% shield modifier,
before accuracy. SoulFire's added accuracy closes that narrow gap when uncapped
in this fixture.
Ghoulbane retains its undead proc and can remain better against undead.

The successive raw 1H ratio gains are 15.38%, 6.67% and 12.50%. Defender's proposed
2H ratio is 6.67% above Avenger, then its forge adds another 12.50%. **This requires
changing normal Defender's current 2H damage from 35 to 64 (+82.86%), and Ascended
Defender from 47 to 72 (+53.19%).** These are substantial progression repairs,
not a cosmetic consequence of the toggle. SoulFire and Avenger 2H values stay at
the freshly captured definitions. This proposal would affect existing Defender
owners too; implementation must make that scope explicit.

## Preserve the support progression

The new read-only capture found material support stats absent from the earlier
comparison. Ascended SoulFire already has healing 14, spell damage 7 and heroic
STR/WIS 4. Ascended Avenger has healing 30, spell damage 15 and heroic STR/WIS 8.
Normal Defender currently loses all of these, in addition to losing mana and
ordinary STR/WIS. Its AC, HP and stun are not universally interchangeable with
healing and casting benefits.

Recommended complete relevant stat totals, shared by both grips:

| Stat | Ascended SoulFire | Ascended Avenger | Normal Defender | Ascended Defender |
|---|---:|---:|---:|---:|
| AC | 0 | 0 | 15 | 30 |
| HP | 0 | 50 | 70 | 168 |
| Mana | 0 | 50 | **50** | 72 |
| STR | 14 | 30 | **30** | 40 |
| WIS | 14 | 30 | **30** | 30 |
| STA | 0 | 0 | 10 | 20 |
| Heroic STR | 4 | 8 | **8** | 10 |
| Heroic WIS | 4 | 8 | **8** | **10** |
| Heroic STA | 0 | 0 | 0 | 5 |
| Healing amount | 14 | 30 | **30** | **35** |
| Spell damage | 7 | 15 | **15** | 20 |
| Each of MR/FR/CR/PR/DR | 0 | 10 | 10 | 20 |

Bold values change the captured definitions. Other attributes remain unchanged;
for example Avenger retains its CHA 20, while Defender has none. This is a
combat/support progression target, not a promise that every miscellaneous stat
strictly increases. Ascended Defender healing 35 is a restrained +5 over the
preceding stage and +15 over its existing 20; a larger 40 was considered but is
unnecessary for the initial test. These are item ratings, not percentages of
healing or spell damage. Their actual contribution depends on the spell and
Nightcap's stat limits, and is excluded from the melee indices below.

There is also a proc activation gap: Avenger's captured proc level is 45;
both Defenders are 50. Recommend testing **Holy Shock activation at 45 for both
Defender qualities**, keeping its spell and proc rate unchanged. That explicitly
expands availability; it is not implemented. Otherwise a level 45–49 player loses
an active proc at hand-in. The captured spell definitions give Flame Shock up to
110 damage and Holy Shock 155 damage plus a 1.5-second stun, before resistance and
other modifiers. Neither proc guarantees success. Sword of the Morning's
Tishan's Clash has a longer stun, so Defender is not automatically best at control.

## How much do the added stats actually do?

The server uses opposed uniform integer rolls. With positive attacker rating A
and defender rating D, normal hit probability is `1 - D/(2A)` when A >= D, and
`A/(2D)` otherwise, including the 50% tie break. Item Accuracy is added to A;
it is **not** a percentage-point hit bonus. The captured item cap is 150.

At the captured level-50 Paladin skill caps, an otherwise unmodified attacker
has A = floor((weapon250 + offense200 + 17) × 1.21) = 565. For illustrative target
defense ratings 400–800, with no background item accuracy:

| Added Accuracy | More successful melee hits, relative | Hit chance at D=600 |
|---|---:|---:|
| 0 | baseline | 47.08% |
| 10 | 0.95–1.77% | 47.92% |
| 15 | 1.42–2.65% | 48.33% |
| 20 | 1.87–3.54% | 48.75% |
| 25 | 2.32–4.42% | 49.17% |

These are scenarios, not measured NPC ratings or whole-character DPS gains.
Accuracy can help applicable multiclass attacks as well as sword swings. If other
gear already provides 140 Accuracy, at most 10 points apply. At 150, these bonuses
provide no additional benefit. Other accuracy effects change the calculation.
Thus even +25 is a modest gain, and cannot compensate for the previous ~43% ratio
deficit. Do not increase the global accuracy cap for these weapons.

Shield Block is an additional block roll after other avoidance. Current retained
AA policy allows rank 3, whose captured contribution is 5 points. Assuming that
5-point AA contribution and no other block source, counter-block or strikethrough:

| Weapon addition | Resulting conditional block roll | Less eligible melee damage relative to existing 5% roll |
|---|---:|---:|
| 0 pp | 5% | 0% |
| 1 pp | 6% | 1.05% |
| 2 pp | 7% | 2.11% |
| 3 pp | 8% | 3.16% |

Without that AA, the marginal reductions are 1%, 2% and 3%. These percentages
exclude spell damage, ineligible rear attacks and attack counters. They do not
include the shield's existing AC benefit. The 3-point case increases survival
against this isolated eligible damage component by 3.26%, not against an entire
encounter by that amount. No explicit ShieldBlock cap was found in the reviewed
roll, so large additions or unexpectedly strong stacking sources would be unsafe
to assume balanced. This is why the proposed bonus is 0–3 points, not 10–20.

## What the resulting weapon comparison looks like

The following is a **comparative melee index, not DPS**: level 50 Paladin,
unaugmented, no background accuracy, target rating 600, fixed weapon coefficient
2, native damage caps and damage bonuses, equal attack opportunities. Proc,
heroic-stat damage, damage-interval distributions, crits, Slay Undead, haste,
stances and full multiattack behavior are excluded.

| Weapon | 1H, no shield-damage AA | 1H, 100% shield-damage AA | 2H |
|---|---:|---:|---:|
| Ascended Ghoulbane | 9.42 | 17.73 | — |
| Ascended SoulFire, proposal | 9.58 | 17.89 | 11.61 |
| Ascended Fiery Avenger, proposal | 10.96 | 20.62 | 16.26 |
| Normal Fiery Defender, proposal | 11.70 | 22.10 | 17.31 |
| Ascended Sword of the Morning | 12.67 | 23.93 | — |
| Ascended Wurmslayer | 12.83 | 24.60 | — |
| Ascended Fiery Defender, proposal | 13.11 | 24.91 | 19.42 |

Expected identity: SoulFire becomes a credible Ghoulbane alternative with healing
utility; Avenger advances damage and support; Defender adds physical progression
and defense while retaining support; the separate forge produces a weapon around
these stronger 1H comparators in the physical fixture, plus its epic utility.
Earlier stages deliberately do not beat every dedicated 1H weapon in melee.
Whether their support and proc benefits adequately compensate is an encounter
question, not something this index establishes.

**Grip-role conflict remains.** The same fixture gives 1H a 54.13%, 26.85%, 27.70%
and 28.27% lead over its corresponding 2H form with maximum Shield Specialist.
An isolated calculation including Knight's Advantage's captured +24% double-
attack bonus reduces, but does not remove, that lead: at level 50 and skill 225,
expected primary/double attacks are 1.55 for 1H versus 1.682 for 2H. Martial
multiclass membership can remove the knight restriction entirely. This is not
a full multiclass DPS prediction.

Forcing a 15% 2H lead even in the equal-opportunity, maximum-shield-AA coefficient-2
fixture would require roughly **89/45, 100/44, 98/40 and 110/40** respectively,
before testing augments or other class effects. I do not recommend such inflation
to satisfy an artificial universal ordering. If a reliable endgame 2H offensive
role is a requirement, item bonuses alone are insufficient: evaluate the shield-
damage AA/2H-stance relationship as a separate, broader balance project.

Low levels also differ: caps apply before Shield Specialist. At level 20 a Paladin
has a base-damage cap of 30, so several high-damage weapons collapse to the same
base damage and faster 1H wins even without that AA. Raising 2H damage cannot
repair that capped scenario. Keep existing caps; do not remove them for this feature.

## Existing lower-quality weapons

New quests still award Ascended SoulFire and Avenger. For existing lower-quality
items, use explicit per-quality profiles rather than upgrading their quality or
granting the Ascended bonuses. Support stats stay at the captured quality's values.
These six profiles are included in the native sensitivity output, but their
same-quality comparator and encounter acceptance remain required before release.

| Item | 1H | 2H retained | Accuracy | Added block |
|---|---:|---:|---:|---:|
| SoulFire | 13/30 | 23/45 | 4 | 0 |
| SoulFire, Polished | 18/30 | 31/45 | 6 | 0 |
| SoulFire, Exalted | 22/30 | 38/45 | 8 | 0 |
| Fiery Avenger | 15/30 | 33/44 | 5 | 0 |
| Fiery Avenger, Polished | 20/30 | 44/44 | 8 | 0 |
| Fiery Avenger, Exalted | 25/30 | 55/44 | 12 | 1 |

## Evidence, review and what remains

- `public-stats-reference.json`: October 27 16:24 UTC, approved read-only production
  capture of 26 selected public item definitions and 9 rule rows; no player/account
  data. Selected fields include attributes, heroic stats, mod2s and proc activation
  levels. This is not every item column or a proof of the runtime active ruleset.
- October 23 retained `docs/quests/camil-chapterhouse/balance-public-content.json.gz`:
  public spells, skills, AAs and rules. Refresh relevant spells/AA policy against
  the release target before implementation acceptance.
- `assess.py` executes extracted, unchanged native `DoDamageCaps` and
  `GetWeaponDamageBonus` functions across 1,248 cases, then produces 5,616
  comparative coefficient/AA/augment/defense scenarios, 243 accuracy cases and 18
  block cases. Levels 1/10/20/30/40/45/50/60; four primary-class cap categories;
  augment 0/+5/+10. Added augments are sensitivities, not a verified obtainable
  loadout. Alternate primary-class rows isolate caps, not complete class eligibility.
- Six independent exhaustive opposed-roll enumeration checks match the closed
  form. Native functions compiled and ran successfully. Every source and capture
  used by the script is SHA-256 recorded in `assessment-results.json`.
- Source: `server-mods/code/zone/attack.cpp` hit calculation 178–245 and 333–376;
  shield block 623–632; caps 1415–1527; shield modifier 1705–1708; knight membership
  671–683 and double attack 4039–4079; proc level 5164–5168. Item caps and worn
  application: `zone/bonuses.cpp` 289–292, 355–356 and 383–385. RNG semantics checked
  in `E:/EQ_Local_Dev/akk-stack/code/common/random.h` 74–92; that header is a local
  reference, not a verified production binary fingerprint.
- Independent fresh-context review found no blocking arithmetic defect. Its
  qualifications—limited comparator competitiveness, omitted support/proc output,
  conditional block savings and maximum-AA 1H advantage—are incorporated here.
  The final healing proposal was reduced from 40 to 35 after review to limit
  extra support power. This is not release certification.

Before release: verify complete current item/proc definitions and rules; implement
the explicitly chosen profile/support/proc changes; build the full paired server
and client; test lawful Paladin-only and martial/caster multiclass loadouts at
low levels, 40, 45 and 50 with/without purchased AAs and compatible augments.
Measure living/undead/stun-immune target kills, melee/proc damage, incoming damage,
healing and mana consumption. Include low-HP emergency sustain, named encounters,
accuracy-cap saturation and stacking with other Shield Block sources. Confirm
shield equip without zoning and toggling/persistence in the real client.

Full native encounter testing remains pending; the known local Docker startup
fault has not been repaired or retested in this assessment. The model is useful
for rejecting bad designs and selecting candidates, not approving deployment.
Fiery Defender's separate upgrade remains intact. No global AA/rule changes are
recommended as part of this item package.
