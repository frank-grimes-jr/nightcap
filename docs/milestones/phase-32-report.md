# Phase 32 — Production NPC and spell-access repair

Built: real Perl OOC adapter; canonical held-class spell authorization; guarded
client merchant, scroll scribing and spell-level projection; canonical packaged
class levels; production binary/quest startup compatibility check. Regressions
cover the reported class tuple and class-release/identity boundaries.

Cut: database-wide rewrites, numerical balance changes and unrelated client hooks.
The original client is read-only. Unknown custom learnable spells require an
explicit catalog update rather than inheriting globally widened eligibility.

Verified: full Linux native build, five client runtime tests, exact signatures,
69 repository tests, 13 Go test packages, frontend/Wails builds, five production
supervisor tests and seven mocked rollout cases. Signed release 2026092005 and
launcher 0.2.2 are staged.

Open: explicit production upload/deployment approval after an automatic review
rejection, followed by hosted verification and owner in-game acceptance. The separate
2026092004 deployment has corrected the old hosted economy binaries, but this
task's OOC and spell changes remain a candidate until its own verified rollout.

[Release status, rollback and exact QA](../releases/production-bugfixes-20260920.md).
