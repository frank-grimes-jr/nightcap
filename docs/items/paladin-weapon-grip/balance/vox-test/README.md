# Palwar versus Lady Vox — isolated native experiment, October 27, 2026

**Completed: 240 primary fights, 40 timestep controls and one exact replay. All 281 retained encounters ended in a Vox kill.** The primary matrix contains 170 distinct encounter trajectories: 70 unchanged 1H skill-control pairs are exact duplicates. This is a five-seed pilot for each loadout, not 281 independent observations, a population win-rate estimate or final approval of the proposed stats. Palwar’s live inventory and production definitions were not changed.

Every proposed loadout was viable in this particular build. Ascended SoulFire had a shorter mean kill time than Ascended Ghoulbane in these trials, and Ascended Defender had the highest mean full-build DPS among the main progression weapons. However, Monk buttons supplied most damage, and small weapon rankings changed with timing and random events. These results do not establish monotonic progression, justify approving the whole stat package or support adding more defensive stats.

## Main progression at matched weapon skill

Both weapon skills start at 230 in this comparison. The 1H results are identical to the actual-skill runs because only the unused 2HS skill changes. Every entry is the mean of five native encounters at 32 ms. DPS includes the complete build, including Monk abilities and procs.

| Weapon | Proposed 1H / 2H damage-delay | 1H kill time | 2H kill time | 1H full-build DPS | 2H full-build DPS |
|---|---|---:|---:|---:|---:|
| Ascended SoulFire | 26/30 · 46/45 | 48.5s | 45.7s | 753 | 755 |
| Ascended Fiery Avenger | 30/30 · 66/44 | 43.3s | 44.1s | 798 | 779 |
| Fiery Defender | 32/30 · 64/40 | 45.3s | 45.1s | 808 | 780 |
| Ascended Fiery Defender | 36/30 · 72/40 | 40.7s | 41.1s | 851 | 843 |

## Every quality, using Palwar’s actual skills

Palwar starts with 1HS 230 and 2HS 32. Native learning remains enabled: actual-skill 2HS trials ended between 32 and 37. This table intentionally shows the practical training disadvantage; use the matched-skill table above when judging grip balance. The same owned Exalted Crested Mistmoore Shield (409310, AC 17, Accuracy 2) accompanies every 1H candidate/comparator. No shield accompanies 2H.

| Weapon | 1H damage/delay | 2H damage/delay | 1H mean kill | 2H mean kill | 1H / 2H full-build DPS |
|---|---:|---:|---:|---:|---:|
| SoulFire | 13/30 | 23/45 | 48.3s | 59.5s | 724 / 662 |
| Polished SoulFire | 18/30 | 31/45 | 45.7s | 60.8s | 757 / 633 |
| Exalted SoulFire | 22/30 | 38/45 | 45.1s | 58.7s | 760 / 642 |
| Ascended SoulFire | 26/30 | 46/45 | 48.5s | 52.6s | 753 / 705 |
| Fiery Avenger | 15/30 | 33/44 | 52.3s | 51.7s | 712 / 717 |
| Polished Fiery Avenger | 20/30 | 44/44 | 45.5s | 53.0s | 768 / 729 |
| Exalted Fiery Avenger | 25/30 | 55/44 | 45.5s | 54.6s | 770 / 691 |
| Ascended Fiery Avenger | 30/30 | 66/44 | 43.3s | 44.9s | 798 / 772 |
| Fiery Defender | 32/30 | 64/40 | 45.3s | 46.4s | 808 / 795 |
| Ascended Fiery Defender | 36/30 | 72/40 | 40.7s | 51.9s | 851 / 741 |

## Comparison weapons

| Control | Mean kill time (range) | Full-build DPS | Recorded slashing DPS |
|---|---:|---:|---:|
| Ghoulbane (Ascended) | 55.8s (44.0–87.1) | 661 | 40.2 |
| Sword of the Morning (Ascended) | 50.6s (42.0–62.9) | 745 | 55.1 |
| Wurmslayer (Ascended) | 47.6s (41.9–65.8) | 778 | 58.9 |
| Current saved SoulFire grip, no shield | 46.6s (43.1–49.1) | 728 | 13.8 |

The current saved SoulFire control resolves natively as 1HS 23/45 without a shield; it is not the rejected 7/30 implementation. It represents the saved server grip and does not reproduce the reported RoF2 cached-definition bug. Recorded slashing DPS excludes the un-emitted lethal packet.

Ascended Ghoulbane has an undead-specific proc; Vox is the living encounter requested here. This comparison does not measure Ghoulbane’s intended undead advantage. Sword of the Morning retains its native proc-level gate rather than receiving an artificial level 45 unlock.

## What the stats actually established

- All 48 loadout checks passed: original item IDs, correct skill type, proposed damage/delay, Accuracy, support stats, proc types/levels, shield eligibility and candidate block. Every owned AA entry and captured buff matched the snapshot; repeated bonus calculation did not accumulate block.
- The main candidates carry weapon Accuracy 10/15/20/25 in both grips and added block 0/1/2/3 percentage points only in 1H with a shield. Palwar already has 5 points of AA shield block and 100% Shield Specialist damage bonus. The shield contributes its own Accuracy 2.
- Normal Defender was tested with the proposed Avenger support floor: Mana 50, STR/WIS 30, heroic STR/WIS 8, Heal Amount 30 and Spell Damage 15. Ascended Defender was tested with heroic WIS 10 and Heal Amount 35. Both Defender proc thresholds were 45. These are explicit diagnostic overrides, not deployed definitions.
- Monk abilities accounted for 87.8–99.6% of recorded outgoing damage per primary run. Weapon damage/Accuracy are therefore only part of the result; STR and other support changes can affect the rest of the build.
- All 240 primary trials won, but healing was not irrelevant: 136 included accepted healing casts, 207 requested Mend, and the worst sampled HP was 13.4% in a Ghoulbane trial. Passive native healing also occurred. This is not an invulnerable dummy test.
- No stat-by-stat ablation was performed. Combined-package success cannot tell us how many of those wins depended on +Accuracy, +block, heroic stats, healing, proc access or the shield itself. Five seeds cannot resolve a 1–3 point defensive budget reliably.

**Recommendation:** keep this as a tested candidate, not a release-approved table. Do not add further block/avoidance on the basis of these wins. Train/equalize 2HS when comparing grips, and retain both the full-build and weapon-attribution views. Before finalizing exact stat points, compare the package with each added bonus disabled under sustained incoming pressure and test a living/undead opponent pair. The client right-click/shield repair still needs its paired release and in-game acceptance.

## Repeatability and timestep sensitivity

The main matrix used 32 ms. Forty additional encounters repeated all four main progression stages in 1H and matched-skill 2H at 50 ms, with the same five seeds. Native RNG and distributions were retained; only their seed source was fixed. An exact 32 ms replay produced identical complete JSON, and all 70 same-seed 1H actual/equalized pairs produced identical encounter output. These are controls, not additional independent samples.

| Loadout | Mean32ms kill | Mean50ms kill | Mean DPS change |
|---|---:|---:|---:|
| Ascended SoulFire 1H | 48.5s | 44.5s | +5.6% |
| Ascended SoulFire 2H | 45.7s | 47.2s | -1.4% |
| Ascended Fiery Avenger 1H | 43.3s | 43.2s | +1.6% |
| Ascended Fiery Avenger 2H | 44.1s | 48.5s | -4.0% |
| Fiery Defender 1H | 45.3s | 43.5s | +3.3% |
| Fiery Defender 2H | 45.1s | 46.3s | -1.2% |
| Ascended Fiery Defender 1H | 40.7s | 43.1s | +0.3% |
| Ascended Fiery Defender 2H | 41.1s | 40.9s | -0.4% |

All 40 timestep controls won. Aggregate DPS shifted −4.0% to +5.6%; individual kill times moved substantially, and the direction of some grip comparisons changed. Event ordering, procs and Vox’s healing can change when the timestep changes. A small difference between mean weapon results is not a stable ranking. Higher DPS also need not mean a faster kill when Vox heals differently. The CSV retains ranges and the JSON retains every seeded result.

## Method and limits

- Fresh read-only Palwar snapshot: 2026-10-27 17:05UTC. Fresh public combat definitions/rules: 17:17UTC. Read-only table captures were separate transactions, not a single cross-table atomic snapshot. No account data was copied.
- Level 45 Dwarf Paladin/Warrior/Monk, actual mixed equipment/augments, owned shield, all 100 saved skill rows and 122 owned AA rows (1979 points spent). Native AA activation gates remained active. Full HP/mana/endurance at fight start; eight captured buffs restored with their saved native durations. No generic maximum-AA or maximum-skill character was substituted.
- Same learned Greater Healing (spell 15), threshold below 55% HP, native Monk buttons/cooldowns, Mend and return-to-melee controller. No optimized activated-AA rotation, external healer, new preparation buffs or surrounding raid-zone adds. This is a consistent automated play policy, not a claim to reproduce human play.
- Fresh Lady Vox 73057: level 55, 32000 HP, 5000 mana, AC 230, 85–218 base damage; native spells/abilities/AI and Permafrost maps. Engagement, LOS/range, reciprocal damage, spell availability and initial resources were asserted. Runtime loaded 1013 default rules and Classic expansion context.
- A restricted local test DB/user and separate diagnostic executable were used. Each fight starts a new native process; synthetic skills, AAs, buffs, spellbook, memorized spells and timers are reset sequentially. No live inventory, accounts, character profiles, item SQL or production services were modified.
- DPS is positive non-overkill HP loss from native depth-zero NPC Damage calls divided by fight duration. No nested calls occurred in these retained trials. Total damage can exceed 32000 because Vox heals/regenerates. Packet category metrics omit the lethal packet. NPC spell counts are cast starts, not verified landings. HP/fear observations are sampled at approximately 512 ms; they are not continuous minima/durations.
- This bypasses the client interface. It cannot prove right-click conversion, tooltip refresh, shield equipping in RoF2, zoning persistence or client/server release pairing. Proposed content remains diagnostic-only; the earlier numerical implementation remains rejected.

## Evidence and reproduction

[Summary CSV](results-summary.csv) · [Per-run metrics and hashes](results-summary.json) · [Executable/cache/source manifest](evidence.json) · [Independent review](review.md) · [Wiki impact](wiki-impact.json).

Private capture, fixtures and raw logs remain at `C:/Users/verre/Documents/Codex/2026-10-26/make/work/palwar-vox`; they are not copied to the wiki. Reproduction scripts under `adapters/` are exact snapshots and expect that private staging layout plus the retained paired October26 source/build in the local container. Setup refuses an existing destination DB/user; never blindly rerun or substitute a live database.

Docker’s local socket fault was recovered without deleting images/volumes: [dated recovery](../../../../ops/docker-stale-sockets-20261027.md). No game reload, client package or publication was performed for this experiment.
