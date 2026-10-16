# Passive AA reduced to 20% — October 13, 2026

Status: **20% passive AA is active on OVH**, with owner-authorized main promotion.
Owner gameplay/balance acceptance remains pending.
The owner reported four AA from a blue skeleton kill in Befallen on Palwar and
explicitly selected `AA:PassiveExpPercent=20`, down from 40. This halves future
passive AA awards before integer rounding. It does not reduce all AA awards to
one-fifth. The production `AA:ExpPerPoint=4000` override stays in place.

## Scope and existing progress

At zero AA allocation, kills and eligible quest/task rewards retain full normal
XP and award 20% of the full AA award. `#aaexp on` still selects full AA focus;
its award is unchanged. Existing AA points, purchases, raw partial XP, eligibility,
era policy and point costs are preserved. The compiled passive fallback remains
1%; deployments must retain the production database override.

No native/client/quest update or restart is required. Use the authenticated
global Rules reload and verify world plus every running zone. Never kill an OVH
zone to apply this rule: its supervisor restarts the whole runtime on child exit.
The local development database is outside this change.

## Verification and activation

- [Preflight](preflight.json) fingerprints the current production world/zone
  against the AA class-ranks release and all seven relevant source files.
- [Existing native suite](native-tests.txt): 129 checks pass against the exact
  retained deployed source. Cases include 20%/40% kill and quest/task rewards,
  percentage rewards, full normal XP, full focus, rounding and saved progress.
  The extracted profile-loading method has its existing signed-comparison warning.
- [Operation recovery tests](ops/test_apply.py): nine tests pass, including
  uncertain commits, external changes, missing fresh reload acknowledgments,
  process changes and evidence-write failure. This reuses the October 12
  point-cost operation's corrected recovery procedure.
- [Operator](ops/apply.py) locks deployment and GM operations, checks current
  binaries and prerequisite rules, captures private rule/Palwar preimages,
  validates a fresh full PEQ backup, rehearses forward/inverse SQL in a rolled-back
  transaction, then changes exactly the guarded default-ruleset row. It verifies
  the complete rule table, fresh world/all-zone reload logs, unchanged process
  identities and service health. It never writes character records.

The preflight saved snapshot showed Palwar at level 10 with zero AA allocation,
2,326 partial AA XP, 7 unspent and 71 spent points. This is a saved snapshot,
not a reconstruction of the reported kill or a promise of exactly two points
from another skeleton; point-boundary carry and each kill's award matter.

## Recovery

The one-shot operator restores only its own rule value on failed verification
and reloads again; unresolved recovery stays explicit. Do not rerun a completed
activation. For a later authorized rollback, capture fresh preimages/backup,
apply the [guarded inverse](rollback.sql), require one changed row and verify
`#reload rules global` in world and every zone. Retain all subsequently earned
points and remainder; never restore an old player or database snapshot.

## Exact owner QA — pending

1. On Palwar in Befallen with `#aaexp off`, record AA points/progress and normal
   XP, then kill XP-eligible blue skeletons of comparable level. Normal XP should
   retain its prior rate; raw passive AA should be half the prior rate before
   rounding. Carry from the partial AA bar can change the displayed point count.
2. Cross a 4,000-XP AA boundary, buy a legal AA, zone and camp/relog. Verify points,
   purchased ranks, partial progress and allocation persist.
3. Compare `#aaexp on` against the same type/level of mob: its full AA award should
   remain unchanged. Turn it off afterward for passive progression.
4. Confirm real quest/task rewards and later-level pacing. Native arithmetic and
   reload verification do not establish player combat or balance acceptance.

## Activation evidence

Activated at 2026-10-13T15:19:29Z; exactly one guarded rule row changed. The full PEQ backup
passed gzip validation (451,976,632 uncompressed bytes); forward/inverse rehearsal
passed. Fresh logs confirm world and all 12 zones reloaded rules, with unchanged
PIDs/start tokens and all five services running (game/database healthy). Every
other rule, including 4,000 XP per AA point, was preserved. No restart, player
record write or client update occurred.

Private backup and rule/player preimages remain under
`/opt/nightcap/backups/passive-aa-twenty-20261013/`. Independent review found no
blockers and independently reran all nine operation tests.
[Activation and reload receipt](result.json) · [Execution log](activation.log).
