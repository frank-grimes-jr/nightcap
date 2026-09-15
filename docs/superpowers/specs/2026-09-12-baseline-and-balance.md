# Baseline reconciliation and solo combat evidence

Date: 2026-09-12
Status: implementation in progress; user request is the accepted intent

## Objective and order

Reconcile the source, deployed data, and verification baseline. Build and run an
offline high-level encounter calculator for Vox and Nagafen using fully equipped
level-50 characters. Use the results to assess balance and reduce manual QA, then
continue the remaining project tasks. Preserve the solo-preferred, demanding,
balanced principle in AGENTS.md and the test/main human acceptance boundary.

## Baseline slice

- Work in `feature/baseline-reconciliation`, isolated from the user's main checkout.
- Integrate existing dev, main acceptance history, and the already-deployed
  `feature/spelldmg-healamt-scaling` history; preserve their provenance.
- Compare normalized mirrored source to the active tree and verify explicitly
  patched/unmirrored paths separately. Capture hashes, not a declaration of parity.
- Check PEQ rule values and every applicable tier's spell/healing stamps against
  the generator. Repair the missing level-1 AA rule with preconditions and rollback.
- Run C++ and existing custom regressions. Parse the C++ summary: its current main
  returns zero even on assertion failures, so exit status alone is insufficient.
- Record what remains unverified in runtime memory or manual QA.

## Calculator contract

- Use a versioned read-only PEQ snapshot of enemy, item, spell, loot, skill, and
  relevant rule data. Store query provenance, capture time, and source hashes.
  Exclude accounts, credentials, and player records from committed fixtures.
- Explicitly define level, race, held classes, equipment legality, era/drop
  availability, skill values, buffs, AA assumptions, and rotation for each build.
- Best-in-slot means best for a declared build objective over the verified eligible
  item pool. Record slot/item IDs, alternatives, and optimization criteria; do not
  call a handpicked or unproven cross-era collection universally BiS.
- Implement source-grounded damage, healing, HP/mana, attack timing, mitigation,
  hit/avoidance, resist, and enemy ability paths where needed. Reuse/extract server
  formulas or differential-test ports against C++ to avoid a second untested ruleset.
- Simulate resource exhaustion, heal timing, cooldowns, enemy damage and burst,
  kill/death/timeout, DoT/HoT durations, and repeatable seeded trials. Report
  sensitivity to uncertain behavior instead of disguising assumptions as facts.
- Compare current 250 caps to proposed alternatives and HP changes, plus lower
  equipment tiers. Include direct-caster, melee/sustain, and DoT/pet/control coverage
  before making a server-wide balance recommendation.
- Deliver machine-readable inputs/results and a readable report. Distinguish exact
  formula tests, modeled encounter outcomes, and remaining in-game acceptance.

## Tests and evidence

Start with failing tests for baseline drift, failed C++ summaries, missing AA rules,
gear legality and availability, cap application, integer truncation, duration-split
bonuses, event ordering, mana exhaustion, and seeded reproducibility. Use small
analytically solvable fixtures plus real PEQ encounters; a passing model alone is
not proof of parity with live combat.

No live character may be overwritten to manufacture a test result. No numerical
balance change is selected before evidence. Database repairs must be reversible;
destructive operations require a verified backup. Promotions to test include
specific NPC/zone/action/expected-result checklists; main still requires sign-off.

## Files and approach

`tools/balance/` will hold a Python standard-library command-line tool and unittest
suite (run from that directory). `docs/balance/` holds manifests and reports.
Existing SQL and PowerShell checks remain authoritative where suitable. Add an
interactive view only when it helps interpret completed model results.

The riskiest step is combat fidelity, especially spell/AA interactions and true
era-obtainable gear. An arbitrary DPS/HP spreadsheet would be quicker but would
not meet the requested evidence standard. A fully separate EQ server integration
fixture may be added if it supplies stronger automated evidence than a port.

## Subsequent queue

After baseline and calculator acceptance, refresh `docs/next-steps.md`, `tasks/plan.md`,
and the multiclass gate audit against actual evidence. Continue AA string cleanup,
bag pricing, feature page, zone augments, bard behavior, and remaining authorized
multiclass work in small tested slices. Preserve pre-existing owner QA/design gates;
do not mark the overall goal complete while required work remains.
