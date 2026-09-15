# Consolidated test branch — September 15, 2026

Owner instruction: "I merged it. Merge everything else into test".

## Included source and branch audit

PR #52 was merged into dev as `8e933f5542843e2ec48a0ca4459d5042e669dcad`.
Prior test was `b2ccbdc`, 17 commits behind dev with no test-only commits.
This promotion includes the complete client-delivery work, scoped equipment
submission candidate, verified launcher/backend, Play/Stop wiring, Darth's
Classic kit macro, and their documentation and tests. Earlier server/gameplay
work already belongs to both branches.

All local and remote source branch tips are included. Two historical local refs
needed ancestry reconciliation only:

- Login-banner commit `654a970` already exists as `921ecf6` with newer QA text.
  Merge `9b08317` retains the current canonical Lua handler and changelog.
- Local main's old promotion merges add no missing code. Merge `9cea43c` retains
  the current changelog, including the already-recorded balance agreement.

Both resolutions were verified to have no file changes. The resulting tree is
byte-identical to the reviewed/tested client commit `0f7b076` and merged dev.
The promotion adds only the current branch/QA documentation after those merges.
The standalone `gh-pages` publication branch is excluded from source merging;
its index.html already matches the source. No branch was force-pushed or deleted.
The dirty root checkout and its installed runtime files are preserved.

## Verification

Fresh checks: canonical login-banner regression, generated patch-catalog check,
zero content diff for both historical merge resolutions, and ancestry coverage
of every local/remote source branch tip. No open PR remains after #52's merge.

The unchanged code inherits the passing desktop Go tests/vet, 17 native helper
scenarios, seven Chrome tests, frontend typecheck and Windows Wails build recorded
in [phase 19](../milestones/phase-19-report.md) and
[phase 20](../milestones/phase-20-report.md). Tests were not reinterpreted as
manual acceptance. This operation publishes source to test; it does not deploy
binaries, apply SQL, enable preview Play or restart the live server.

## QA now: launcher preview and test tools

1. Build the test branch using [the launcher build instructions](../../eq-launcher/README.md).
   Open the Windows preview and select an isolated copy of the supported RoF2
   client. Expected: recognized client, responsive folder dialog and activity;
   Play stays disabled because the default policy has no production release keys.
   Canceling the folder dialog must preserve the selected path.
2. Check the window at its minimum size, keyboard navigation and second-instance
   focus. Record client/launcher hashes and screenshots. Browser fixture passes
   do not prove the native window or Wails bridge.
3. For the requested GM kit only, use level-50 Paladin Darth in Plane of Knowledge,
   clear the cursor and provide bag space, then run `/mac darthclassic` with the
   versioned macro installed in MQ. Expected: the documented Classic Ascended kit,
   no automatic equipment/level/class changes, no later-era/Fabled items. The
   macro must refuse a different character or an occupied cursor. Record actual
   items against [the kit manifest](../../tools/macros/darthclassic-items.json).
   See [macro prerequisites and limitations](../../tools/macros/README.md).

## QA after trusted candidate provisioning

The new client candidate is not yet a signed player release. Provision its
trusted inventory/key policy and preserve an isolated client before this matrix.
Do not infer deployment from the source merge or enable the preview to bypass
missing release/health checks.

1. **Launcher lifecycle:** launch a valid cached signed release while offline.
   Expect fresh file/configuration/health verification before gameplay. Altered,
   expired, missing-helper or pending-recovery installations must fail before
   main. Cancel during startup, Stop during play, and exit naturally; update,
   recovery, folder changes and a second Play stay blocked until cleanup finishes.
   Closing the window requests shutdown; close it again after cleanup completes.
2. **PoK setup:** use the Ancient Chronicler at database x=-285, y=-74, near the
   arrival hub x=-285, y=-148, z=-159. On disposable characters verify Primary,
   Second and Third classes agree on login, hail, `#classes` and `/say !classes`.
   Camp/relog and repeat. Do not alter Done for these tests.
3. **Equipment client change:** use a Warrior holding Necromancer in Second,
   then Third, and a race/deity/level-legal original Necromancer-only robe.
   Record its exact item ID. Expect legal bag-to-chest equip, truthful tooltip,
   stats and zone/relog persistence. Removing Necromancer must reject that robe;
   race/deity/level/wrong-slot restrictions must still reject invalid items.
   Repeat occupied-slot swaps, normal weapons, shields, bags and augmented items.
   [Complete equipment matrix](../../eq-client-dll/docs/equipment-qa.md).
4. **Held Monk regression:** use the authorized level-50 Cleric/Shadowknight/Monk
   Monktest fixture. Verify its PoK banner, then `#zone arena -73.5 -979 49.9`.
   Target the training dummy; if Classic filtering hides it, a GM can use
   `#npctypespawn 77002`. Through Actions → Abilities, assign and activate each
   documented Monk skill. Expected: normal animation/damage/reuse, one Kick per
   activation, persistence across relog. [Exact ability table](../qa/2026-07-29-held-monk-combat-qa.md).
5. **Remaining full parity:** preserve the spellbook/gem, Skills/trainers, AA and
   Bard movement/song matrices in the [full production contract](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md).
   Record failures as open gates; partial equipment or launcher success does not
   complete those features.

Existing server QA remains in [the combined live checklist](live-qa-20260915/QA.md):
all sixteen PoK merchants, utility placement and Find, class selection/release,
22 bag prices, earned-AA persistence/refunds, AA XP, pets, weapon damage and
waypoint discovery. This promotion adds no new server deployment to that record.

## Acceptance and rollback

Record PASS/FAIL with character/classes/level, exact steps, expected/observed
result and relevant logs/hashes. Main promotion and player release remain separate
from this test consolidation; no issue acceptance gate is closed here.
If source rollback is required, preserve test history with a revert. If a later
candidate is deployed, use its file/database/binary rollback procedure; changing
Git alone cannot undo installed or database state.
