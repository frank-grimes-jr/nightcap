# Nightcap next steps

Updated 2026-09-15. The owner authorized all implemented changes for live QA.
See [combined deployment and rollback](releases/live-qa-20260915/README.md) and
[the exact per-feature test checklist](releases/live-qa-20260915/QA.md).

1. Run and record owner QA for PoK placement/shopping/class status, bag pricing,
   skills/trainers, level-1 AA XP, earned-AA purchase/refund/class release,
   weapon/pet/AA-buff fixes, waypoints and established caster UI.
2. Keep the combined release on test until explicit owner sign-off; no issue is
   closed merely because its candidate deployed. Main remains unchanged.
3. #16 missing-title audit found owned/system AAs. Preserve them while reviewing
   acquisition/effects, dependencies and supported title or audited removal options.
4. #23: HTML and documentation are published to dev/test; the static payload is
   on gh-pages. GitHub rejected Pages activation for this private repository
   under the current plan (422). Select hosting, then verify the public URL; see
   [the website runbook](ops/player-website.md).
5. #19 captures both movement speed and song landing while running (absorbs #20).
   Neither has a verified fix; use the listed controls to reproduce them.
6. #13 owns off-base equipment (absorbs #38); #36 owns skills and trainers
   (absorbs #39). Client blocks still require explicit in-game evidence/work.
7. #4 needs the AA column decision. #11 retains its original best-of-stat/regen
   gaps. #14/#15 launcher/hardening and #26 augment content remain unfinished.
   #17 native hub routing is deployed for QA; global tooltip widening remains.

Fifteen issues remain open after consolidation. Published historical evidence:
[issue audit](audits/github-issues-20260914.md),
[AA title findings](audits/aa-titles-20260915/README.md).

Operational lessons: deploy matching world/zone when custom rules change;
world deletes rules missing from its compiled catalog. Relocation must handle
scoped saved NPC state as well as spawn2. Both were corrected in this release.
