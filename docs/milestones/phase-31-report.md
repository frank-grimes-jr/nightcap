# Phase 31 — Coordinated hosted server/client update

September 20, 2026. Combined current main with production launcher and hosting
source. OVH now runs matching economy-aware native binaries with credential-log
hardening; launcher 0.2.1 and signed release2026092004 carry 22 files, including
Classic Lavastorm and both exact-hash EQG retirements.

Fresh native compilation, crypto tests, source stability, actual running hashes,
all hosted client hashes/signature and four WSS/native handshakes passed. The
repository suite passed 62 tests with one opt-in skip; launcher production and
desktop suites, frontend build, audit and five production checks passed. Reviewed
rollback/publication rehearsals cover seven success and failure scenarios.

All 33 managed quests/plugins and 30 resident afterimages already matched the
hosted snapshot. No database migration or quest replacement was needed. A complete
on-host backup preceded restart, eight preservation fingerprints stayed identical,
and the expected stock rotation advanced epoch1 to epoch2.

Remaining: native owner gameplay acceptance, Lavastorm client rollout/travel gate,
R2 backup/restore testing, GitHub Actions deployment, automatic patch-before-Play
and launcher EXE self-update. Local QA and workspace clients were unchanged.

Operational learning: certify matching native binaries before restoring newer
feature data; keep player ingress closed through preservation checks; inspect
the visible channel during interrupted publication recovery; verify read-only
containers through stdin rather than docker cp.

[Release evidence, recovery and exact owner QA](../releases/hosted-main-update-20260920.md).
