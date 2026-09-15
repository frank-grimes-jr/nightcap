# AA duration candidate verification

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Candidate only; no live deployment or restart.

The native `CalcBuffDuration` candidate excludes direct AA spell IDs from the
long self-buff override. Other duration formulas and focus calculations remain
native. See ADR 0008 for classification scope and limitations.

## Lifecycle results

All 18 controls pass with identical initial gear, skills and purchased AA ranks.
The six idle, Frenzied Devastation and Divine Arbitration controls reproduce
their prior native reports exactly. The five new regression tests also reject
the old permanent-AA reports, missing preparation buffs and changed comparisons.
The complete Python suite passes 154 tests.

| Buff | 200-point stage: initial ticks | All-purchasable stage: initial ticks |
| --- | ---: | ---: |
| Warlord's Tenacity | 11 | 19 |
| Improved Twincast | 20 | 21 |
| Frenzied Devastation | 20 | 36 |
| Arch Shielding | 999,999 first observed | 1,800,000 |
| Resolution | 1,000,000 | 1,800,000 |

Arch Shielding finishes casting between 500-ms trace samples; a native buff tick
runs before its first observation. The checker allows that one elapsed tick.
Preparation casts consume native mana and their buffs remain active at 150 seconds.
Low-rank Tenacity and both Twincast ranks expire within the 150-second controls.

The 200-point Tenacity control ends at 2,333 HP, versus 2,750 idle and 1,709 under
the prior permanent-duration behavior. Maximum-rank Tenacity still kills the
unhealed character starting at 40% health. Do not attribute all Tenacity harm to
permanence or count its increased maximum HP as sustained healing. Its native
negative HP effect and health at activation matter.

## Reproduction

The matched 144 boss encounters also completed and passed movement checks. All
54 cases with no activated AA reproduce the prior raw reports exactly. Two
200-point Vox cases change from boss death to player death: balanced seed 1731
and durability-first seed 1729, both using `burst_tenacity`. All other terminal
outcomes are unchanged; this does not imply their timing or resources are equal.
These three-seed samples establish a counterfactual, not a reliable win-rate
estimate. Inputs, full reports and comparisons are in `duration-encounter-*` and
`duration-encounters.json.gz`.

Run Python tests from `tools/balance`: `python -m unittest discover -s tests`.
From the worktree root:

```powershell
python tools/balance/aa_duration_controls.py --inputs docs/balance/duration-inputs.json --verify docs/balance/duration-controls.json.gz --baseline docs/balance/active-aa-controls.json.gz --output docs/balance/duration-checks.json
```

The isolated build uses `build_native.py --reuse-adapters --spells-source
/tmp/nightcap-balance-20260912/spells_duration_candidate.cpp`. Its manifest pins
the compiled candidate, original source and reused objects. This is not a fresh
full-source build or a production binary parity claim.
The compiled spells source had mixed Windows line endings. The evidence manifest
records both its raw hash and the directly verified LF-normalized hash used by Git.

## In-game QA required at promotion

On the test server, use a level-50 WAR/CLR/WIZ character with the documented
200-point and all-purchasable allocations from `duration-inputs.json`. In Plane
of Knowledge, with no opponent and ready cooldowns:

1. Cast Arch Shielding (67) and Resolution (314) separately. Confirm native mana
   costs and that each remains after 150 seconds; test clicking each off.
2. Activate each purchased Tenacity rank separately with full health, then with
   deliberately reduced health. Record HP/max HP each tick and expiration; have
   a recovery plan for the high-rank drain. Expect finite duration and unchanged
   shared cooldown with Celestial Regeneration.
3. Activate Improved Twincast. Verify finite duration, native charges and expiry
   without casting. Repeat with eligible damaging spells to check charge use.
4. Verify Frenzied Devastation still has finite duration/charges. Confirm the
   existing level-50 Celestial Regeneration rejection remains distinguishable
   from a successful heal; this candidate does not fix that separate issue.
5. Against Lord Nagafen in Solusek B and Lady Vox in Permafrost, record buffs
   before/after breath attacks. Distinguish dispels from charge consumption.

Final BiS, full preparation, representative pet/melee coverage and broader balance
tuning remain required before a balance sign-off.
