# Passive AA reduced to 10% — October 17, 2026

**Deployed at 15:09:05 UTC (11:09:05 a.m. Eastern)** under the owner's explicit
instruction, "We should reduce the percentage to 10% as well". Ruleset 1
AA:PassiveExpPercent changed from 20 to 10. Owner gameplay/balance QA is pending.
No additional AA release was requested or installed; see [the review](REVIEW.md).

Normal leveling XP remains whole at zero allocation. Eligible kill/quest/task
passive AA awards are halved before integer rounding. Full AA focus, 4,000 XP per
point, existing points, purchases and partial XP are preserved. Tiny awards can
round down; partial carry means displayed points per kill need not halve exactly.
Compiled defaults remain unchanged; retain the persistent production overrides.

## Verification

- Read-only content capture matches all four AA catalog tables to the reviewed
  fixture; current build manifest matches XP arithmetic and the generated policy.
- 157 native-method harness checks pass (129 existing plus 28 focused 10% checks).
  MSVC C++20 compiles the actual local XP methods; their normalized source hash
  matches production. Supporting client_packet.cpp differs from retained source;
  this is not a claim of a full native binary rebuild or exact deployed packet QA.
  Existing numeric-conversion warnings remain. The initial added quest expectation
  assumed level 10 instead of the harness's level 30; correcting that fixture made
  both failing cases pass. No production formula changed.
- Nine operation/recovery checks pass, including uncertain commit, external rule
  edits, evidence-storage failure, missing fresh reload logs and process changes.
  Sandbox temporary-file restrictions initially prevented fixtures; normal local
  fixture permissions resolved that environment failure.
- Fresh full PEQ backup passed gzip validation (458,000,213 uncompressed bytes).
  Guarded forward/inverse SQL was rehearsed inside a rolled-back transaction.
- Exactly one rule row changed. The complete rule-table comparison preserved all
  other values, including the October 17 idle-zone-worker reliability correction.
- World and all 12 zone workers completed the authenticated global Rules reload.
  PID/start identities remained unchanged and all five services stayed running;
  game and database were healthy. No restart, client update or player-row write.

[Activation receipt](result.json), [preflight](preflight.json),
[native checks](native-tests.txt), [operator](ops/apply.py).

## Recovery

Private backup/preimages and one-time receipt are under
`/opt/nightcap/backups/passive-aa-ten-20261017/`. Do not rerun the completed
operator. On an uncertain result, inspect that receipt and the actual row first.
The reused operator reverts only its own 10% row to 20% on failed verification
and verifies another reload; it preserves external changes and reports unresolved
recovery. Never restore an old player or database snapshot for an XP rate change.
An independently requested later rollback changes only future earning: capture
fresh preimages, guard 10 → 20, and verify world/every-zone reload acknowledgments.

## Exact owner QA still pending

1. On Palwar in Unrest, use #aaexp off. Record normal XP, banked points and the
   partial AA bar before comparable XP-eligible living and undead kills. Normal
   XP should retain its prior rate; raw passive AA is half the previous 20% rate.
2. Cross a 4,000-XP point boundary, purchase a legal rank, zone and camp/relog.
   Confirm points, purchases, remainder and allocation persist.
3. Compare #aaexp on with similar targets: full focused AA is unchanged, with no
   normal XP. Turn focus off afterward for passive leveling.
4. Confirm real quest/task rewards and later-level pacing. Catalog, arithmetic
   and reload evidence do not establish encounter balance or owner acceptance.

## Documentation/publication boundary

The relevant wiki guides, Features, home, command reference and Recent changes
are updated locally, alongside the installed Nightcap knowledge and fingerprints.
Whole-wiki review preserves unrelated candidate labels and generated reward
values. The source-drift ledger is not blindly advanced. Public wiki/player-site
publication is pending and is not claimed by this gameplay rule activation.
