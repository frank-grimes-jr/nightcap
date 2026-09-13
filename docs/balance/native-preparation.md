# Native preparation and AA progression

Date: 2026-09-12. Isolated candidate measurements; no live deployment.

Thirty prepared WAR/CLR/WIZ encounters cover both dragons, three seeds and the
0/100/200/500/all-purchasable AA stages with fixed candidate gear. The finite
budgets retain the existing balanced purchase order (actual spending is explicit
in the reports). The native AA-duration candidate is included.

Preparation casts Arch Shielding (67), Resolution (314), Symbol of Naltron (488),
Resist Magic (64), then Resist Fire (60) for Nagafen or Resist Cold (61) for Vox.
All five remain at engagement. They add 925 HP; the zero-AA Nagafen control also
increases MR from 219 to 279 and FR from 158 to 198. Costs, buff ticks and native
sitting recovery are recorded. Recovery takes 66.60 seconds at 0/100 points,
60.55 seconds at 200/500, and 36.35 seconds at all purchasable AAs in these cases.
The encounter starts standing with the exact recovered native resources/buffs.

| AA budget | Nagafen wins / 3 | Vox wins / 3 | Nagafen fight seconds | Vox fight seconds |
| --- | ---: | ---: | --- | --- |
| 0 | 3 | 1 | 170.55–238.35 | 234.10–293.95 |
| 100 | 3 | 2 | 97.65–192.90 | 118.55–334.60 |
| 200 | 3 | 3 | 48.65–104.20 | 59.25–97.45 |
| 500 | 3 | 3 | 31.90–61.80 | 23.55–47.00 |
| All legal at 50 | 3 | 3 | 11.40–16.95 | 11.40 |

Fight ranges include deaths, not only kills. Three seeds are exploratory samples,
not estimated success probabilities. Preparation consumes native RNG and advances
the clock before engagement, so same-seed prepared/unprepared runs do not imply
identical subsequent random events. The unrestricted all-AA stage spends 13,738
points and is a stress ceiling, not an accepted Classic release target. See the
separate AA expansion review for the owner's proposed availability lever.

## Verification and reproduction

The saved 30 native reports pass preparation, activation, encounter and movement
checks. Python regression tests reject omitted preparation, changed resources,
clock resets, unfinished casts, missing buffs and appearance-only sitting. The
first experimental appearance-only capture was discarded after the checker
established it used standing regeneration; the saved reports use native posture
packets and demonstrate actual sitting.
All 160 Python tests pass. Ten no-preparation controls across both bosses and all
five AA stages reproduce their prior native reports byte for byte. Four native
controls reject duplicate buffs, a spell above the held-class level requirement,
a detrimental preparation spell and an invalid time limit. The isolated account
and character tables remain empty.

Run tests from `tools/balance` with `python -m unittest discover -s tests`.
From the worktree root:

```powershell
python tools/balance/preparation_controls.py --inputs docs/balance/preparation-inputs.json --verify docs/balance/preparation-encounters.json.gz --output docs/balance/preparation-checks.json
```

The build manifest pins the isolated executable, source and reused native objects.
This is not a fresh full-source build or complete live/client parity certification.

## QA at promotion

With a level-50 WAR/CLR/WIZ using the recorded gear and AA allocations, start at
full resources without buffs. Cast the five listed spells in order, sit to recover,
and record HP, mana, resists, buff slots and recovery time. Verify buff durations
continue ticking and mana returns through regeneration. Stand and engage Lord
Nagafen in Solusek B or Lady Vox in Permafrost; record dispels, Twincast charges,
fear recovery, kill/death time and final resources. Repeat at each AA stage.

The observed power gap needs curated AA availability, final gear selection and
melee/pet comparisons before numerical tuning. Full BiS, all archetypes, later
release ceilings and in-game acceptance remain open.
