# Palwar / Vox: Wu and Way of Steel removal experiment

October 27,2026. Same captured character, native executable, gear/grips, buffs, controller, opponent and seeds as the earlier weapon matrix. Only the selected AA ownership rows were removed from synthetic character 1 in the isolated local database. No live character, AA definitions, weapon definitions or quests changed.

## Main comparison

First 20-second DPS uses native positive NPC HP loss over the same opening duration in every encounter. Whole-fight DPS and time also reflect healing, survival and different fight lengths. These are whole-build conditional comparisons, not isolated formula multipliers or additive shares of total damage.

### Palwar’s actual skills: 1HS 230 / 2HS 32

| AA state | First 20s DPS | Change from baseline | Wins / deaths / timeouts | Mean winning time | Whole-fight DPS |
|---|---:|---:|---:|---:|---:|
| Both active | 723.2 | +0.0% | 120 / 0 / 0 | 49.8s | 737.4 |
| Wu disabled | 343.9 | -52.4% | 120 / 0 / 0 | 190.0s | 328.3 |
| Way of Steel disabled | 155.9 | -78.4% | 86 / 34 / 0 | 410.7s | 148.8 |
| Both disabled | 85.9 | -88.1% | 48 / 72 / 0 | 562.5s | 77.3 |

Each row contains 120 executions: 24 loadouts × five seeds. Winning-time means exclude deaths/timeouts; do not compare them as if every run won. Full outcomes and per-loadout results are in the CSV.

### Matched skills: 1HS 230 / 2HS 230

| AA state | First 20s DPS | Change from baseline | Wins / deaths / timeouts | Mean winning time | Whole-fight DPS |
|---|---:|---:|---:|---:|---:|
| Both active | 747.6 | +0.0% | 120 / 0 / 0 | 47.7s | 755.4 |
| Wu disabled | 354.9 | -52.5% | 120 / 0 / 0 | 182.0s | 340.0 |
| Way of Steel disabled | 162.6 | -78.2% | 91 / 29 / 0 | 399.1s | 157.6 |
| Both disabled | 91.2 | -87.8% | 49 / 71 / 0 | 555.0s | 84.5 |

Each row contains 120 executions: 24 loadouts × five seeds. Winning-time means exclude deaths/timeouts; do not compare them as if every run won. Full outcomes and per-loadout results are in the CSV.

## Interaction between the AAs

| Skill setting | Wu gain with Steel active | Wu gain with Steel disabled | Steel gain with Wu active | Steel gain with Wu disabled | Interaction |
|---|---:|---:|---:|---:|---:|
| Actual | 379.3 DPS | 70.0 DPS | 567.3 DPS | 258.0 DPS | 309.3 DPS |
| Matched | 392.8 DPS | 71.4 DPS | 585.0 DPS | 263.7 DPS | 321.3 DPS |

Interaction is baseline − Wu-off − Steel-off + both-off, using first 20-second DPS. A positive value means the observed combined benefit exceeds the sum of their separate benefits measured with the other disabled. Do not add the two removal percentages: each includes their shared interaction. Five seeds per loadout do not establish precise population effects.

## Main weapon loadouts

Cells show first 20-second DPS and Vox kills out of five. All 1H rows use Palwar’s actual 1HS 230 and his owned shield; 2H rows here use matched 2HS 230. The CSV also contains all quality variants, actual-skill2H and comparison weapons.

| Weapon / grip | Both active | Wu disabled | Steel disabled | Both disabled |
|---|---:|---:|---:|---:|
| Ascended SoulFire 1H | 787.9; 5/5 | 312.8; 5/5 | 165.3; 5/5 | 96.7; 4/5 |
| Ascended SoulFire 2H | 734.9; 5/5 | 392.2; 5/5 | 152.4; 2/5 | 84.2; 0/5 |
| Ascended Fiery Avenger 1H | 717.0; 5/5 | 394.5; 5/5 | 196.3; 5/5 | 112.2; 5/5 |
| Ascended Fiery Avenger 2H | 767.0; 5/5 | 357.5; 5/5 | 185.9; 5/5 | 110.8; 0/5 |
| Fiery Defender 1H | 766.6; 5/5 | 373.9; 5/5 | 197.2; 5/5 | 105.8; 5/5 |
| Fiery Defender 2H | 793.5; 5/5 | 396.3; 5/5 | 176.6; 5/5 | 88.5; 0/5 |
| Ascended Fiery Defender 1H | 829.4; 5/5 | 388.2; 5/5 | 200.9; 5/5 | 109.3; 5/5 |
| Ascended Fiery Defender 2H | 848.5; 5/5 | 415.5; 5/5 | 203.6; 5/5 | 102.9; 2/5 |

## Exactly what was disabled

- **Technique of Master Wu:** owned first-rank family 611, active rank 6. Its DoubleSpecialAttack effect is 120. Native code makes the first extra attack certain and tests further extras at 30%, 7%, then 1% conditionally; about 2.32121 total attempts per eligible activation, including the original. With ClassicMasterWu=false, extra attacks repeat the requested Monk skill.
- **Way of Steel:** owned first-rank family 12706, active rank 2. Removal includes all six +200 flat skill-damage effects and the associated Fists of Fury 23598 skill proc. This is a whole-AA test, not a damage-only edit.
- **Retained:** Kick Mastery 9 (+90 to the kicks), Strengthened Strike 3 (+15 to ordinary Kick), other earned AAs, class membership, 1979 recorded spent points and 2 unspent points. No points were refunded or reassigned. The other AA active quantities/charges were checked against baseline.
- Native exported flat Monk AA bonuses changed from `[305,290,200,200,200,290]` to `[105,90,0,0,0,90]` when Steel was removed (Kick, Round Kick, Tiger Claw, Eagle Strike, Dragon Punch, Flying Kick). Wu removal left these flat bonuses unchanged.

## Controls and interpretation

- 144 modified stat gates passed. Three baseline encounters reproduced the original complete JSON exactly. The executable SHA remained 88de63cddae472679f944f04df3662e508c4af125994d0f05adb03b20df8eb47; no native rebuild or gameplay patch was used.
- 720 new primary executions compare three removal states against 240 retained baseline executions. Each state has 70 duplicate unchanged1H actual/matched-skill encounter pairs; these are controls rather than independent samples. Exact replays for all three removal states are asserted.
- 120 new 50ms controls repeat the same eight main loadouts × five seeds for each removal state, compared with the retained 40 baseline50ms controls. The main matrix uses 32ms.
- All first 20-second measurements require the character and Vox to remain in the encounter through that window; the analysis fails rather than silently discarding a short death/kill. Equal seeds reproduce identical inputs but are not identical RNG trajectories after an AA changes the number of random draws.
- The six-button automated Monk rotation is unchanged. It measures consistent use of all native available cooldowns, not casual or necessarily optimal human play. These results concern this Paladin/Warrior/Monk build and single Vox encounter, not all Monks or later expansions.
- Native death sentinels are clamped in HP-loss metrics. Spell cast counts and proc packets are not successful-hit counts. Packet damage shares omit an un-emitted lethal packet; the common 20-second HP-loss metric does not use packet shares. Sampled HP minima are not continuous minima.
- No nerf or final tuning recommendation follows automatically. AAs are meant to be valuable. Their size and interaction should inform the intended progression curve, encounter pressure and class combinations.

## Timestep sensitivity

Mean first 20-second DPS at 50ms versus 32ms, over the same eight main loadouts and seeds; outcomes are kept separate.

| State |32ms opening DPS |50ms opening DPS | Change |50ms wins / deaths / timeouts |
|---|---:|---:|---:|---:|
| Both active | 780.6 | 777.9 | -0.3% | 40 / 0 / 0 |
| Wu disabled | 378.9 | 368.4 | -2.8% | 40 / 0 / 0 |
| Way of Steel disabled | 184.8 | 186.5 | +1.0% | 37 / 3 / 0 |
| Both disabled | 101.3 | 108.9 | +7.5% | 29 / 11 / 0 |

## Epic pacing decision

The owner also proposed awarding Ascended epics directly rather than requiring a second upgrade. The [separate pacing assessment](pacing-assessment.md) recommends that direction for this progression pace, while distinguishing an intended short useful life from measured replacement timing. Fresh later-item definitions leave replacement headroom, but ordinary-quality Luclin weapons do not automatically replace an Ascended epic. The current 47/40 Ascended Defender also has a meaningful raw-ratio regression from 66/44 Ascended Avenger that direct delivery alone would not fix. No reward-policy change was implemented.

## Evidence

[Full condition CSV](summary.csv) · [Per-run metrics and interaction calculations](summary.json) · [Manifest](evidence.json) · [Independent review](review.md) · [Wiki impact](wiki-impact.json).

Private raw snapshots, fixtures and native outputs remain in `C:/Users/verre/Documents/Codex/2026-10-26/make/work/palwar-vox`. The local synthetic database is restored to its baseline after the experiment. Production was only read for the separately requested public replacement assessment; no live player or content writes occurred.
