# Classic sympathetic clicks on Lady Vox and Lord Nagafen

## Results and promotion boundary

**410 prepared fights** compare the final rank on five matched seeds, two dragons, two class combinations and three gear controls. The final rule adds one twentieth of the largest resolved direct HP component, rounded down, up to 48. A component below 20 produces zero. The 320 prepared and 121 unprepared draft fights are separately labeled. Flat +48 healing added 48 to a 40-point Minor Healing, an observed 120% increase. The final rank added two to that same heal, 5%. Its effective contribution over an entire cheap-heal attempt can fall below 5% after a dispel or when the target lacks sufficient missing HP.

| Prepared Polished Warrior / Cleric / Wizard, both clicks active at pull | Nagafen | Vox |
|---|---:|---:|
| Full-fight direct Strike contribution, median | 3.07% | 3.18% |
| Full-fight effective Healing contribution, median | 2.22% | 4.00% |
| Actual paired change in full-fight DPS, median | −1.35% | −22.71% |
| Actual paired change in full-fight HPS, median | −6.00% | +17.44% |
| Ordinary healing, first 60 s, off → both | 60.0 → 62.4 HP/s | 40.0 → 41.6 HP/s |
| Normal damage / fastest eligible nuke, both, full attempt | 34.78 / 2.04 DPS | 37.62 / 15.43 DPS |
| Normal damage / fastest eligible nuke per total mana | 1.71 / 0.20 | 1.88 / 1.48 |
| Normal healing / cheapest heal, both, full attempt | 70.29 / 7.56 HP/s | 45.54 / 7.29 HP/s |
| Normal healing / cheapest heal per total mana | 3.57 / 0.64 | 2.81 / 0.60 |

All 10 ordinary progression attempts with the buffs ended in player death, as did their paired off controls. In the first 60 seconds all 10 pairs survived and showed a 4% healing-rate gain. The median paired first-minute DPS changes were +36.02 on Nagafen and −15.67 on Vox. All five Nagafen cheapest-heal pairs lost at least one arm before 60 s; three Vox cheapest-heal pairs reached 60 s in both arms. The full-fight 3–5% paired sustained-output target remains open. [Every matched 20/60-second window](matched-windows.csv) · [per-cell comparisons and outcomes](comparisons.csv) · [per-attempt measurements](measurements.json.gz).

**Cheap casts at high gear.** In the original five-seed cohort, geared Vox Shock of Fire exceeded Conflagration on damage rate and damage per mana before clicking (192.01 vs 68.58 DPS, 50.03 vs 9.07 damage/mana) and after clicking (194.73 vs 68.93 DPS, 49.58 vs 8.97 damage/mana). Geared Lifespike already beat Drain Soul on both dragons without the click. With both buffs it dealt 116.63 vs 23.37 DPS on Nagafen and 108.92 vs 32.78 on Vox; it also used mana more efficiently. The two click buffs therefore cannot establish the condition that the strongest normal-rank spells win universally on both metrics.

The new five-seed crossover was **geared Vox, cheapest heal**. Before clicking, Minor Healing delivered 14.41 HP/s and 1.63 healing/mana vs Superior Healing's 28.87 and 3.78. With both buffs, these medians became 31.86 and 4.15 vs 29.71 and 3.91. Both candidate rotations timed out in all five fights. The explicit burst represented 0.43% of the cheap rotation's effective healing; much of the gap follows the encounter trajectory. This cell was selected for a separate five-seed holdout before handoff. The 750/750 synthetic stress also shows existing stacked power: without either buff, cheap fire nukes on Vox and cheap lifetaps on both bosses already win both damage metrics.

The independent five-seed sample reproduced the whole-rotation crossover: with both buffs, cheapest gave 31.888 HP/s and 4.942 healing/total mana vs normal 31.848 and 4.191. All ten of those both-buff attempts timed out. With both buffs off, cheapest gave 28.582 and 3.550 vs normal 31.486 and 4.143. The original sample already showed the crossover with **Strike alone and zero bonus healing**: 30.278 vs 30.212 HP/s and 4.188 vs 3.976 healing/total mana.

| Stacked Vox, 10 seeds per arm | Normal HP/s | Cheap HP/s | Normal HP / all mana | Cheap HP / all mana | Normal HP / healing mana | Cheap HP / healing mana |
|---|---:|---:|---:|---:|---:|---:|
| Both off | 31.083 | 26.112 | 4.090 | 2.961 | 23.721 | 17.941 |
| Strike only | 29.587 | 29.248 | 3.884 | 3.920 | 23.551 | 17.519 |
| Healing only | 30.933 | 30.006 | 4.060 | 4.007 | 23.530 | 17.940 |
| Both active | 30.294 | 31.868 | 3.987 | 4.548 | 23.569 | 17.757 |

Cheap spent median 1,608 mana on heals and 4,575 on nukes with both clicks, against 1,176 and 5,490 on the normal rotation. Its median overheal was zero vs 5,233.5 on normal. The median direct effective burst was 122.5 HP over the cheap encounter and 96 over normal. The median healing rate in the first 20 and 60 seconds was zero in every stacked arm; those windows primarily capture the damage phase before the 55% healing trigger. Across the entire encounter, normal delivered more effective healing per point actually spent on heals in all four arms. The whole-rotation crossover remains a test finding under the stated total-spend screen. The Strike-only result gives a reason to keep the existing bound while investigating caster AI/rotation and player experience; the isolated data establish no across-the-board cheap-heal win. [Full attribution and independent-seed summary](holdout-comparisons.csv) · [80 attempt records including expenditure and per-heal size histograms](holdout.json).

The measured binary and the final worn-group arbitration binary are fingerprinted independently. The tested jewelry and combat gear have no higher worn group-heal effect. All 16 comparisons on seed 1713 (both profiles, progression/stacked gear, both dragons, off/both) reproduced every saved measurement exactly after the final correction. [Original bounded binary](diagnostic-build.json) · [final corrected binary](final-replay-build.json) · [exact replay cases and hashes](final-replay.json). Real-client and owner balance acceptance are pending.

## What the diagnostic measures

Each fight runs a synthetic level-50 player in the real zone code under RoF2 rules, with a fixture packet stream and no graphical client. The opponents are Lady Vox (73057) in Permafrost or Lord Nagafen (32040) in Solusek B. Both templates start at 32,000 HP. The runner loads each zone's own collision, water and pathfinding maps, positions the player in native melee range, and lets the dragon use its ordinary melee, spell list, resists, fear and dispel. The symmetric 50 ms pulse continues until death or 900 seconds. A zero-damage death is a valid attempt.

The same fighter equips and successfully clicks both Ascended items using the native item casting entry, confirms both resulting buffs, and swaps back to its original jewelry before combat. Control arms then remove the indicated click buff. This keeps clothing, elapsed preparation time, and starting clocks matched. The four prepared cover buffs are Resist Fire (60), Resist Cold (61), Resist Magic (64), and See Invisible (80). The controller pays their costs, rests to recover, then clicks. The separate unprepared pilot has no cover buffs. Both dragons can strip beneficial buffs with their breath; the prepared data records the last 500 ms sample showing each click active. Remaining buff time varies with the fight. The controller does not re-click in battle.

| Rotation | Warrior / Cleric / Wizard | Magician / Necromancer / Shaman |
|---|---|---|
| Normal | Ice Comet (732, 203 mana) on Nagafen or Conflagration (659, 250 mana) on Vox; Superior Healing (9, 185 mana) below 55% HP | Drain Soul (447, 248 mana); Greater Healing (15, 115 mana) below 55% HP |
| Fast hostile | Shock of Fire (376, 10 mana, 1.5 s); additional Nagafen control Shock of Ice (656, 23 mana, 2 s) | Lifespike (502, 13 mana, 1.5 s). Lifetap (341, 8 mana, 1.5 s) fails the Strike mana gate. |
| Cheapest direct heal | Replace only Superior Healing with Minor Healing (200, 10 mana, 1.5 s) | Same heal threshold in the two tap rotations |

Base mana/cast time come from the public PEQ spell capture. Each equipped item and gem passes native eligibility. Attempted and successful casts remain subject to native fizzle, fizzles' partial mana charges, cast time, recovery, resists, projectile handling, channeling, and character state. The tap character uses its own casts with no summoned pets to isolate owner tap competition. The diagnostic includes passive AA effects, automatic attacks and these timed gem decisions; it does not optimize active AA use or navigation.

The progression profile wears twenty Polished Classic-source pieces with 100 legal purchased points. The stacked profile wears twenty Ascended pieces (400 Spell Damage / 400 Heal Amount in this fixture) with the complete reachable allocation under the compiled native policy: 3,463 points for Warrior / Cleric / Wizard, 3,059 for Magician / Necromancer / Shaman. Native purchases check the compiled rank allowlist, class and prerequisite gates. The policy intentionally admits selected later-expansion ranks at Classic release. The separate cap stress retains that gear and fills the two caster totals to the actual 750/750 native item caps in the diagnostic's bonus pass. No obtainable 750/750 outfit is claimed. No augments, player profiles, saved inventories or live gameplay data are used.

## Reading the measurements

The per-seed archive contains result, duration, direct damage, post-overheal healing, requested/effective burst healing, overheal, actual mana spent by each spell (including fizzles), start/minimum/end sampled mana, initial and terminal health, and 20- and 60-second windows when reached. DPS counts owner-caused positive NPC HP loss over the full attempt, excluding overkill and nested double-counts. HPS uses actual positive HP restored. Damage/mana and healing/mana each divide by total charged mana for all spells during the attempt. A mixed rotation spends on both survival and damage. Net mana is initial minus terminal mana and includes regeneration. A killed player, early death, or timed-out healer belongs in the denominator; never compare raw elapsed durations as kill times across failed attempts.

The CSV reports cohort medians and the median of each seed's relative change against its matched off arm, omitting zero baseline denominators. Direct contribution divides the separately identified sympathetic amount by the same attempt's remaining damage or effective healing. This excludes the added action from the denominator but still reflects the player's changed survival, mana decisions, RNG and duration. It is distinct from subtracting the off-arm fight.

## Reproduction

1. Start an ephemeral MariaDB 10.11 container named `nightcap-sympathetic-balance` on the local game-container network with label `nightcap.fixture=sympathetic-classic`, `/var/lib/mysql` on tmpfs, no published ports, and a database named `nightcap_sympathetic_balance`. The root socket account is local to the container. Use a freshly created fixture.
2. On the host run `python prepare.py <September-21-public-content-backup> <EQEmu-source>`. It verifies the backup hash, imports only public table data, leaves account/character data empty, and overlays the dated October 23 combat capture. Run `python prepare.py candidate` for reviewed item/spell/text SQL and matched isolated caches. The retained map, Ninja and native diagnostic inputs from the November 12 Classic raid augment study are identified in `build.py`.
3. Use the committed `fixtures.json`. To regenerate it, run `python matrix.py templates --catalogs <Nov-12-native-AA-catalog-directory>`. Stage the files under `/tmp/nightcap-balance-sympathetic` in the local game container and copy the four candidate translation units and three headers listed in the manifest into its `candidate` subdirectory.
4. Inside only that diagnostic directory run `python3 build.py adapter`, `python3 build.py candidate`, and `python3 matrix.py batch --final`. Each parallel seed/cohort owns its own synthetic character and timers. The final rank uses the unmodified shipping bonus calculation. The explicitly labeled saturation stress is a fixture injection. `python3 matrix.py run --final --cohort caster --seed 1713 --unprepared` runs the separate unprotected control.
5. On the host run `python collect.py` and `python analyze.py` to make the compressed measurements and CSV. Re-running the analyzer on checked-in measurements needs only Python. The local release binary and activated local test server have separate verification. Manual client, encounter and owner balance acceptance remain open.
