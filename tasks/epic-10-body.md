# Epic: True multiclass production parity

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../docs/status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Make primary, secondary, and tertiary classes function as real classes in ordinary play, with production-grade delivery comparable to the multiclass expectation in THJ.

## Confirmed Definition of Done

- [ ] Spells, disciplines, AAs, activated skills, passive skills, equipment, trainers, and client UI work for every held class.
- [ ] Eligible skills auto-unlock at their native character level with skill value **1**.
- [ ] Skills improve normally through use and optional training; production code never auto-maximizes them.
- [ ] The server remains authoritative for class, level, race, deity, slot, skill, item, and other stock restrictions.
- [ ] Exact-build client patches fail closed with hash/signature guards, per-feature config, tests, and useful logs.
- [ ] A branded, signed launcher verifies a signed anti-rollback manifest and installs, validates, repairs, and updates one complete required client-asset generation on a clean supported RoF2 client.
- [ ] The checked-in class-gate audit and all-class × held-slot × capability matrix have no unresolved rows.
- [ ] Automated tests, all-class evidence, and the full `Monktest` in-game matrix pass without changing `Done`.
- [ ] `test` receives explicit user sign-off before merge to `main`.

## Current implementation status

- **Working/partial:** spellbook and spell eligibility, discipline eligibility, mana/stat exposure, mana gauge, held-class skill-cap helpers, portions of skill/passive authorization.
- **Known gaps:** combat-ability dispatch still has base-class gates; empty-fist dual wield is base-class gated; held-class weapons can be equipped server-side but weapon damage rechecks the base class; level-up skill seeding uses a base-class-only check; the old adoption helper can maximize skills; RoF2 hides/rejects secondary-class skills, trainers, and equipment before the server receives a request.
- **Delivery gap:** the existing DLL is manual and caster-focused; the launcher does not yet synchronize client assets from a versioned manifest.

## Ordered delivery plan

### Phase 0 — Baseline, test seams, and exact client evidence

- [ ] Add deterministic held-class/skill/equipment test seams.
- [ ] Check in and close every row in a player-facing class-gate audit.
- [ ] Generate an acceptance matrix for every playable class as primary, secondary, and tertiary across every contracted capability.
- [ ] Capture exact RoF2 patch sites for spells/disciplines, combat abilities, Skills, trainers, and equip submission.
- [ ] Treat unresolved required sites as blockers; permit item serialization only when it is character-scoped, cache-isolated, and independently server-authorized.

### Phase 1 — Skill lifecycle and trainers

- [ ] Check in an exhaustive skill acquisition/restriction table and seed eligible held-class skills at value `1` after mask load, class adoption, and level-up.
- [ ] Preserve existing values, stock race/specialization rules, and stock acquisition for languages/universal tradeskills.
- [ ] Remove/neutralize skill-maximizing production behavior.
- [ ] Complete held/non-held, threshold, cap, and point validation for trainers.
- [ ] Verify class release removes unique capability while preserving skills shared by retained classes.

### Phase 2 — Server gameplay and equipment parity

- [ ] Make activated abilities and special attacks held-class aware.
- [ ] Fix empty-fist dual wield for a held Monk/Beastlord class.
- [ ] Use authoritative held-class legality for player weapon damage and item bonuses.
- [ ] Remediate the classified passive/innate class-gate audit in tested slices.
- [ ] Regression-test spell learning/book/memorization/casting/hotkeys, discipline listing/activation, AAs, mana/stats, persistence, and stock single-class play in all held slots.

### Phase 3 — RoF2 client parity

- [ ] Expose/submit held-class combat abilities and Skills.
- [ ] Permit held-class trainer interaction.
- [ ] Permit equip attempts while leaving authorization to the server.
- [ ] Add exact SHA/signature checks, per-feature config, runtime health, fail-closed logging, and static patch-site tests.
- [ ] Require parity-critical patches enabled and healthy; launcher preflight or runtime activation failure blocks play.

### Phase 4 — Integrated M3 QA

- [ ] Snapshot `Done`; create Human `Monktest` as Cleric / Shadowknight / Monk with an exact-ID/class-asserting local QA script.
- [ ] Validate normal unlocks at levels 1, 5, 10, 15, 17, 20, 25, 30, and 50.
- [ ] Prove natural use/training improvement before granting `Monktest` all eligible held-class skills to cap for the functional QA pass.
- [ ] Complete all-class/slot evidence and test skills/passives, trainers, equipment/damage, caster UI, negative restrictions, persistence, adoption/release, and controls.
- [ ] Compare `Done` after QA and fail on any difference.
- [ ] Promote to `test` with exact interim M3 steps; later launcher/hardening changes require a fresh final promotion and sign-off.

### Phase 5 — Branded launcher and asset sync

- [ ] Add an exhaustive client inventory and Ed25519-signed, monotonic manifest with key rotation and authorized rollback.
- [ ] Authenticode-sign release binaries.
- [ ] Reject absolute/traversal paths, untrusted hosts/redirects, invalid entries, duplicates, oversize releases, replay, and unauthorized rollback.
- [ ] Stage and verify a whole release, then journal activation/backup/rollback so mixed generations cannot launch.
- [ ] Guard against a running client; support offline play only when cached required files are valid.
- [ ] Add owned-file tombstones, EQ-directory selection, status, settings, patch notes, Play, tests, and release packaging.

### Phase 6 — Hardening and release

- [ ] Test clean, corrupt, partial, unsupported, interrupted, running-client, offline, tampered, replayed, and N → N+1 installations.
- [ ] Complete documentation, ADRs, changelog, milestone report, and release pipeline.
- [ ] Promote through `dev` → `test` → `main`; close the epic only after clean-install acceptance.

## QA fixture

`Monktest` is the sole capped-skill QA exception, not a production grant policy. Its local preparation is ID-scoped, class-asserting, snapshotted, audited, and reversible. Its Monk threshold checks include Kick/Mend/dual wield (1), Round Kick (5), Block/Tiger Claw (10), Double Attack (15), Feign Death (17), Eagle Strike (20), Dragon Punch (25), Flying Kick (30), and Triple Attack (50).

## Out of scope

Multi-pet, self-buff stacking, new progression systems, unrelated THJ gaps, and global item-table class widening.

## Tracking

- #11 spell eligibility
- #12 discipline eligibility
- #13 server/client parity umbrella
- #14 launcher/client sync
- #15 hardening/release
- #36 Monk skills/dual wield report
- #38 held-class equipment report
- #39 secondary/tertiary trainers

Detailed implementation artifacts are maintained in the local tracker until their planning commit enters the repository.
