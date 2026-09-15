# Native AA availability comparisons

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Diagnostic candidates for WAR/CLR/WIZ; no live availability change.

The owner proposed removing overpowered AAs and unlocking more with expansions.
The explicit policy in `aa-pool-policy.json` measures a modest combat core, deeper
ranks of that core, and removal of selected burst families. It is not a complete
Classic whitelist: utility, other classes and pet builds still require review.
The comparison preserves the existing six free baseline ranks, including the two
late-expansion culture ranks supplying 20 HP. Keeping those fixed isolates these
comparisons; it does not recommend them for release.

## Candidate pools and results

The early core caps Natural Durability, Combat Stability, Combat Agility, Spell
Casting Mastery, Mental Clarity, Healing Adept, Healing Gift, Spell Casting Fury,
and wizard Spell Casting Fury Mastery at rank 3. It contains 114 spent points.
The balanced order spends 98 at a 100-point budget. Its 200/500/all cases exhaust
at 114 and produce identical combat for matching seeds. Deeper core caps of six
cost 201 points; families with fewer legal ranks stop at their available maximum.

All cases use the same candidate gear, five ordinary preparation buffs, native
sitting recovery, and existing nuke/heal controller. Native purchase validation
still applies. The table reports three seeds per dragon; fight ranges include
deaths and are not win-rate estimates.

| Pool / stage | Actual spend | Nagafen wins / 3 | Nagafen seconds | Vox wins / 3 | Vox seconds |
| --- | ---: | ---: | --- | ---: | --- |
| Early core, 0 | 0 | 3 | 170.55–238.35 | 1 | 234.10–293.95 |
| Early core, 100 | 98 | 3 | 110.75–207.05 | 2 | 320.90–615.15 |
| Early core, completed | 114 | 3 | 153.95–186.35 | 2 | 132.60–820.95 |
| Deeper core, completed | 201 | 3 | 118.90–192.90 | 3 | 289.65–779.10 |
| Unrestricted, without Twincast family | 13,702 | 3 | 15.45–31.35 | 3 | 23.80–33.90 |
| Unrestricted, without Frenzied family | 13,564 | 3 | 16.70–25.80 | 3 | 11.15–16.70 |
| Unrestricted, without both families | 13,528 | 3 | 31.40–48.50 | 3 | 20.75–72.35 |

The saved unrestricted prepared baseline spends 13,738 and kills these bosses in
11.40–16.95 seconds. Even after removing both selected burst families, sampled HP
never falls below 82.1% of starting HP. Removing those two families alone therefore
does not establish a demanding Classic ceiling in these controls. The modest core
retains danger but sometimes produces very long Vox fights. Neither observation
is a complete tuning prescription: final BiS, additional builds, broader seeds and
native/client parity remain necessary.

## Prerequisites and interpretation

The generator filters allowed ranks before resolving purchases. It never bypasses
a missing prerequisite to keep a desired rank. Consequently:

- Removing Improved Twincast also removes Hastened Improved Twincast (a cooldown
  reduction), for 36 points total.
- Removing Frenzied Devastation also removes Prolonged Destruction, Sustained
  Destruction, Hastened Destruction and Improved Sustained Destruction, for 174
  points total.

The audit lists every removed rank and its cost. These are family comparisons,
not independent estimates of only the base activation's value. No spent points
are reassigned to alternative AAs in removal cases. Changes in spells cast and
preparation also alter subsequent RNG consumption; matching seeds do not force
identical combat events. Non-monotonic small-sample results are not proof that
extra AA ranks weaken a build.

## Verification and reproduction

Fifty-four native reports pass purchase, preparation, activation, terminal-state
and movement checks. Six zero-spend encounters match the prior prepared baseline
exactly. Twelve 200/500 controls match their exhausted-pool all-stage fights exactly.
The allocations, prerequisite-removal audits and complete input matrix regenerate
exactly from the frozen catalog and saved policy. The diagnostic binary is reused
unchanged from the native preparation phase.
All 164 Python tests pass.

From `tools/balance`, run `python -m unittest discover -s tests`. From the worktree root:

```powershell
python tools/balance/aa_pool_controls.py --inputs docs/balance/aa-pool-inputs.json --verify docs/balance/aa-pool-encounters.json.gz --output docs/balance/aa-pool-checks.json
```

## Release and in-game QA boundary

This is purchase-selection simulation, not server enforcement of an availability
policy. Before promotion, select a reviewed release pool, implement purchase and
activation gates consistently, and audit existing purchases and client display.
In-game QA must use the recorded level-50 WAR/CLR/WIZ gear and ranks, cast the five
preparation buffs, then test Lord Nagafen in Solusek B and Lady Vox in Permafrost.
Verify the nine early-core rank caps and actual 114-point exhaustion; verify that
excluded families cannot be purchased or activated under an enforced policy.
Those enforcement tests cannot be claimed complete from these simulations.
