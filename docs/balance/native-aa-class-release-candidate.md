# Atomic class-release candidate

2026-09-13. Native candidate verified on feature/aa-ownership. Not
promoted, installed, or certified for player use. The committed before-state
reproduction remains in native-aa-class-release.md and its pinned artifacts.

The new native ReleaseMulticlassSlot accepts only integer slots 2 and 3. It
stages retained classes, canonical earned-AA refunds/removal, and skill clamps,
then commits class slots, skills, AA rows, wallet, spent and expended counters
in one InnoDB transaction. Shared families remain owned even when an expansion
suspends them. Class-only grants are removed without refunds; charged families
refund only when a charge remains, following the existing nominal-cost policy.

Session fields, skills, AA profile, bonuses and client updates follow an
acknowledged commit. No general Save, independent SetSkill write, or second
class read is used during release publication. On failure the class state and
AA ownership are invalidated, profile saving is disabled, and the transport
closes. Process terminates invalid sessions at entry and after packet handling
so they cannot enter linkdead AI. The native class setter uses conditional
writes against expected slots and rejects occupied replacement; its Lua binding
passes signed values without narrowing them first.

The quest plugin requires the matching boolean Perl binding. It performs no
release SQL and reports native failure or an unavailable binding without a
fallback mutation. The old purge entry point is retired and closes the session;
deploy plugin and binary together. The PoK content candidate remains separate.

## Verified candidate evidence

- Matched before/after use identical inputs and persisted skill fixtures. Six of
  seven contracts fail before; all seven pass after (36 operations per phase).
- Twenty extended release cases pass: real skill clamps, rollback after class
  and skill writes, stale skill/class state, grant-only and charged ownership,
  invalid/empty slots, and stale occupied-slot selection. Wizard spell-crit bonus
  is 9 after loading the earned family and zero immediately after native release,
  before the diagnostic recalculates bonuses.
- The packet sink observes committed slots, AA rows/counters and skills when the
  first ClearAA, SendAATable, RespondAA, AAExpUpdate or SkillUpdate is published.
  It requires no active transaction, ClearAA before table entries, the expected
  skill packets, and closed transport without success publication on failure.
  Observer queries do not retry. This is a mock transport, not client rendering.
- Thirteen purchase/grant regressions also pass against this same candidate.
  Together the candidate has 40 passing native cases and 131 operations.
- All synthetic character/AA rows and injected triggers are removed. Original
  class values/timestamps and skill rows are restored; the AA catalog is unchanged.
- Fifteen actual Perl assertions pass for the quest plugin, including failed or
  unavailable native release and invalid slots. Source guards check API and
  process boundaries; those guards do not constitute native session recovery QA.
- Fresh source snapshot: 2,787 files, no final hash mismatches. Reviewed zone
  SHA256: e79e7f2eacd50237a8c74aeda44896e124159d114b5b7c37979e9a1356eb645c.
  The diagnostic links 130 pinned objects. Final after diagnostic SHA256:
  775079f58b3b131c538146862c208a9091e5b6e5b96d4a9713b11597f60fdb82.
- The configured isolated C++ fixture passes all 87 tests. Initial and review
  test invocations lacked configuration and failed four IPC checks despite zero
  exit codes; both logs are retained. Only verified-cpp-checks/log certify 87/87.
- The final calculator/evidence suite passes all 348 tests in 125.934 seconds.
  Its log is aa-release-final-python-tests.log; the pre-final 344-test log is retained.

The first release invocation exposed a synthetic fixture mismatch: combat skill
ceilings were loaded in RAM but had no saved rows. The new preimage check refused
that state. The failure log is retained; matched before/after runs now explicitly
load saved skill fixtures. A diagnostic compile attempt also used private client
fields; the corrected probe uses public class loading and a controlled temporary
class-row change, then restores storage to model a stale session.

Independent review found and verified corrections for the post-packet linkdead
fallback, stale occupied-slot overwrite, trigger-execution assertions, original
fixture validation and packet ordering. A final reviewer independently recomputed
all release assessments from the recorded native reports.

The source bundle contains the changed engine files, diagnostic/runner sources,
and the complete source manifest. The parent sources and final build remain in
/tmp/nightcap-aa-release-20260913/source. The shared helper retains its prior
expended-counter comparison; concurrent external wallet edits are not certified.

## Remaining release gates

Actual Client::Process/OnDisconnect execution, fresh-session reconnect and
uncertain-COMMIT recovery still need native evidence. Class selection's broader
lifecycle, the other outstanding AA lifecycle gates, client rendering and explicit
in-game QA remain. No deployment, promotion, live binary replacement, or zone
restart occurred. The owner previously asked not to restart while playing.

Reproduce the native batches from this worktree with the retained runtimes:

    python -B tools/balance/run_aa_class_release.py --phase before --persisted-skills
    python -B tools/balance/run_aa_class_release.py --phase after --persisted-skills
    python -B tools/balance/run_aa_class_release_extended.py
    python -B tools/balance/run_aa_purchase.py --phase after --release-candidate

Run calculator/evidence unit discovery from tools/balance. Follow the existing
feature → dev → test → main policy; main still requires owner in-game sign-off.
