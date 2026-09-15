# Epic #10 Implementation Plan

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../docs/status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Spec: `docs/superpowers/specs/2026-07-28-true-multiclass-production-spec.md`

## Ordering and gates

No gameplay implementation begins until the contract and this plan are posted to GitHub #10. Work then proceeds in the following order because later phases depend on the authority and test seams established earlier.

### 0. Baseline, tests, and reverse-engineering evidence

- [x] Create a feature branch from `dev` for the first server slice.
- [x] Add a table-driven native skill train-level test seam that does not require a live zone process.
- [x] Fix native train-level resolution and pass the full 80-test CppUnit target.
- [x] Document the legacy globally widened `skill_caps` state and add a read-only comparison audit.
- [x] Acquire and verify an authoritative clean PEQ `skill_caps` baseline in an isolated container.
- [x] Compare live against canonical: 16,090 live-only, zero canonical-only, zero cap mismatches.
- [x] Rehearse guarded dry-run, repair, exact comparison, rollback, and deterministic reapply against a restored live copy.
- [x] Apply the guarded live repair, verify exact canonical equality, refresh caches, and restart all gameplay processes.
- [ ] Capture baseline behavior for `Done`, `Pups`, and a stock single-class control.
- [x] Create a checked-in audit of every player-facing `GetClass()`/class-switch gate with classification, owner, remediation, and test evidence. (`docs/audits/multiclass-class-gates.md`, coverage complete 2026-09-08.)
- [x] Generate the 480-row all-playable-class × primary/secondary/tertiary-slot × capability acceptance matrix.
- [ ] Find and document exact RoF2 patch sites for spells/disciplines, abilities, Skills, trainers, and equip submission.
- [ ] Treat every unresolved required site as a blocker unless its server-authoritative fallback is approved in #10.
- [ ] Record a go/no-go for the narrow equip patch; require character-scoped serialization/cache-isolation evidence before selecting the fallback.

### 1. Skill unlock and trainer slice

- [x] Check in the exhaustive `SkillUseTypes` acquisition/restriction table.
- [ ] Write failing tests for value-`1` seeding, idempotence, native thresholds, best held-class cap, acquisition policy, race/specialization restrictions, and non-regression. Policy, threshold, idempotence, and held-class resolution tests are complete; character integration remains.
- [x] Implement the authoritative seeding helper.
- [x] Invoke it after mask load, class adoption, and level-up.
- [x] Remove or neutralize the old production skill-maximizing behavior.
- [x] Write/complete trainer tests for held, non-held, early, capped, and out-of-points requests.
- [x] Test class release cleanup and retained-class shared skills.
- [x] Build the zone binary and run focused tests.
- [x] Commit the slice, update `CHANGES.md`, and merge through `dev`.

### 2. Server gameplay parity slices

Land separate tested commits for:

- [ ] Combat-ability packet dispatch and special attacks.
  - Held-Monk server dispatch is implemented for the six stock Monk attacks;
    held-class generic Kick, Berserker Frenzy rounds, and client button
    visibility remain.
- [ ] Empty-fist dual wield and held-class passive checks.
- [ ] Weapon/item runtime legality, damage, and bonuses.
- [ ] Remaining classified player mechanics, one coherent subsystem per commit.
- [ ] Spell learning/book/memorization/casting/hotkeys, discipline listing/activation, AAs, mana/stats, persistence, and stock single-class regression in every held slot.

For each commit:

- [ ] Start with a failing focused test or deterministic reproduction.
- [ ] Preserve NPC/base-class behavior unless explicitly covered.
- [ ] Update `CHANGES.md` and any architecture note affected.
- [ ] Rebuild and verify the running zone processes are newer than the binary.

### 3. RoF2 client slices

For each exact patch site:

- [ ] Add a failing static verification assertion.
- [ ] Implement the smallest patch that permits UI visibility/submission.
- [ ] Keep server authorization authoritative.
- [ ] Add per-feature configuration and useful logging.
- [ ] Verify exact executable size, SHA-256, and original bytes.
- [ ] Mark parity-critical patches required/enabled in production; make launcher preflight or runtime activation failure block play.
- [ ] Build `dinput8.dll` and run the exact-client test suite.

Land separate commits for abilities/Skills, trainers, and equipment.

### 4. Integrated M3 QA

- [x] Back up PEQ before any migration or broad character-data repair. No live mutation is permitted before the clean-baseline gate passes.
- [ ] Snapshot all relevant records for `Done`.
- [x] Create Human `Monktest` as Cleric / Shadowknight / Monk in Plane of Knowledge with an exact-ID/class-asserting local QA script.
- [ ] Exercise normal level-threshold unlocks at 1/5/10/15/17/20/25/30/50.
- [ ] Prove at least one value-`1` skill improves by successful use and optional training before any cap grant.
- [x] Grant `Monktest` all eligible held-class skills to current caps for the functional-only pass; record pre/post audit data and retain rollback.
- [ ] Complete the generated all-class/slot matrix and run activated skill, passive, trainer, equipment, spell, discipline, AA, persistence, adoption/release, negative authorization, and control-character tests.
- [ ] Compare `Done` to the snapshot and fail the checkpoint on any difference.
- [ ] Merge `dev` to `test` only with a written interim M3 in-game spike and wait for user sign-off.
- [ ] Treat this as a milestone checkpoint, not release approval; all later changes require a fresh final promotion and sign-off.

### 5. Launcher and release

- [ ] Specify/version the manifest schema and exhaustive version-controlled client asset inventory.
- [ ] Implement Ed25519 manifest signing, embedded trust, key rotation, monotonic releases, and separately signed rollback authorization.
- [ ] Authenticode-sign the launcher, updater, and DLL in release CI.
- [ ] Implement strict path/host/redirect/hash/size/release-budget validation.
- [ ] Implement whole-generation staging, verification, journaled activation, backup, rollback, and owned-file tombstones.
- [ ] Add running-client and offline-mode policies.
- [ ] Add directory detection/selection, status, settings, patch notes, and Play.
- [ ] Add Go unit tests plus local HTTP integration tests for tampering, wrong keys, replay/rollback, mixed-release recovery, and all normal failure modes.
- [ ] Package the launcher, manifest, DLL, spell data, string data, and owned UI files in CI.
- [ ] Test launcher self-update and full release N → N+1 transitions, including changed/retired assets, interruption, recovery, and authorized rollback.

### 6. Final hardening and promotion

- [ ] Run clean/corrupt/partial/unsupported/interrupted/running/offline acceptance cases.
- [ ] Confirm individual DLL patch failures are fail-closed and diagnosable.
- [ ] Require all parity-critical feature-health checks to pass before Play.
- [ ] Complete docs, ADRs, `CHANGES.md`, EQEmu skill notes, and milestone report.
- [ ] Promote the complete epic from `dev` to `test` with a fresh final clean-install and in-game QA spike.
- [ ] Merge to `main` only after explicit user sign-off.
- [ ] Close child issues and #10 only when the clean-install Definition of Done passes.
