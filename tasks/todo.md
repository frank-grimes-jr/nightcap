# Epic #10 Current Queue

## Ready

- [x] Post the approved production contract and ordered plan to GitHub #10.
- [x] Begin Phase 0 baseline/test-seam work on `feature/true-multiclass-m3`.
- [x] Fix and test native skill train-level resolution.
- [x] Check in the read-only legacy `skill_caps` audit and migration safety gate.
- [x] Generate the 480-row class × held-slot × capability acceptance matrix.
- [ ] Continue the exhaustive player-facing class-gate audit and acceptance matrix.

## External-state blocker

- [ ] Acquire a verified canonical PEQ `skill_caps` baseline. The official dump host did not resolve and all retained local backups postdate global widening.
- [ ] Only after that baseline exists: compare, review, back up, and test a reversible repair migration against a restored copy.

## Blocked by Phase 0 evidence

- [ ] Any live `skill_caps` repair or migration.
- [ ] Server gameplay implementation.
- [ ] RoF2 UI/equipment/trainer patch implementation.
- [ ] Launcher asset-sync implementation.

## Product decisions already resolved

- [x] All held classes behave as real classes in ordinary play.
- [x] Skills auto-grant at native unlock level with value `1`.
- [x] Skills improve normally through use/training.
- [x] Held-class trainers work as optional shortcuts.
- [x] `Monktest` is Cleric / Shadowknight / Monk and may be granted capped skills for QA only.
- [x] `Done` remains unchanged.
- [x] Clean-install launcher delivery is required before #10 closes.
- [x] `Monktest` is the sole capped-skill QA exception; other QA characters follow production policy.
- [x] Interim gameplay QA does not replace final sign-off after launcher/hardening work.
- [x] Multi-pet, self-buff stacking, progression, and unrelated THJ gaps are excluded.
