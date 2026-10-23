# Chapterhouse level-50 capstone calibration

Candidate only; no deployment or player acceptance. The owner selected a demanding target even at maximum legal power.

Fresh read-only production public content was captured on 2026-10-23 at 19:59 UTC. Rules, all four AA tables, spells, skill caps and the tested equipment definitions were copied only into the isolated synthetic database. Classic expansion 0, level 50, current custom combat rules and current compiled AA policy apply. No player data was captured.

The WAR/PAL/MNK fixture purchases the entire reachable legal AA closure: **3,319 points**, not an arbitrary 10,000-point grant. It includes Slay Undead IX, Weapon Affinity V, Spell Casting Fury III, Fury of Magic IX, Destructive Fury VI, Combat Fury VI, Twinproc I and Holy Shield. Native purchase prerequisites remain enforced; exclusions are in capstone-aa.json.

Both strong equipment loadouts use Ascended current-drop gear and legal augments. Weapon controls are Balanced Tonfa of Serenity (662038) and Ascended Ghoulbane (605403); Ghoulbane retains its native Dismiss Undead proc (6846). Ghoulbane has no added incompatible weapon augment. Contemporary public Classic-zone drop paths are retained in balance-gear-sources.txt. These are strong legal builds, **not a proof of globally optimal BiS**. Instrument of Nife (2583) and Valor (312) are cast through the native preparation lifecycle and mana recovery. Original Paladin access and hub availability were checked; widened class columns alone were not used as acquisition proof.

Combat uses real native attack, all six Monk buttons, Stun, Mend, self-healing, owned Rage of Rallos, proc, critical and Slay paths. Seeds: 101, 2718, 8675309. Raid starts with 135% HP and the diagnostic link overrides only the RaidNPC predicate for the synthetic enemy, letting the real CommonDamage path apply 115% damage after calculation. Production sources and objects are not patched. Initial observed HP was checked against the authored mode value.

| Boss / mode | Kill seconds, both weapons | Lowest HP, % of buffed max | Lowest mana, % |
|---|---:|---:|---:|
| Sered / Grind | 43.0–50.0 | 69.1 | 98.9 |
| Sered / Raid | 58.0–64.0 | 53.1 | 98.9 |
| Halvyr / Grind | 57.0–74.0 | 36.7 | 95.2 |
| Halvyr / Raid | 80.9–88.9 | 4.0 | 92.4 |
| Vaelen / Grind | 72.9–83.8 | 31.0 | 90.6 |
| Vaelen / Raid | 105.1–121.5 | 23.6 | 86.9 |
| Shadow / Grind | 88.0–128.0 | -2.1 | 81.5 |
| Shadow / Raid | 129.0–151.0 | 7.2 | 80.6 |

All 48 maximum-AA cases killed the boss with this controller. One native Delay Death window allowed HP briefly below zero before recovery; retain that near-death result, rather than clipping it into a safe-looking floor. Quest Perl timers, adds, guardian defense, Chapterhouse movement and player decision-making are **excluded** from this arena. Therefore these results establish burst and melee-pressure calibration, not success of the complete encounter or its failure rate.

The explicit Ghoulbane/undead control (Shadow Grind, seed 101) produced 164 native Slay messages, eight Ghoulbane proc damage events totaling 7,001 effective damage, and three Instrument of Nife proc events totaling 2,892. The other spell contribution (Dragon Force) comes from the Monk controller. Slay damage remains in the physical ledger; message counts are not a separate damage total. The identical living-body control has no Slay messages or successful undead-only proc damage: kill time rises from 95.9 to 136.0 seconds. The undead identity is valuable and preserved.

The 98/500-AA mostly-Polished progression controls died in 17–32 seconds. Their deterministic bounded purchase order is not optimized; they are explicit undergeared/underdeveloped controls, not an intended solo entry target. This content is a level-50 endgame capstone requiring substantial preparation; level eligibility alone does not imply readiness.

The initial 24-case calibration used older October18 expansion/rule/spell settings and weak original NPC values. It is superseded, archived compressed, and must not be cited as current-legal balance. The failed unsupported no-Stun controller request did not execute combat and is not a result.

Reproduce: chapterhouse_balance_capture.py capture/restore (production SELECT-only, synthetic restore only), chapterhouse_balance.py diagnostics/build, chapterhouse_capstone.py and --controls. Exact per-case inputs/results/logs are retained in native-combat-fixtures.tar.gz with a verified SHA256 inventory. Content hashes, the diagnostic manifest and compact results remain directly readable. Manual acceptance steps are in QA.md.
