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
supervisor tests, seven mocked rollout cases and five publication cases. Signed release 2026092005 and
launcher 0.2.2 are published. The owner authorized main promotion and production
deployment; both completed. All 15 running native hashes, 33 runtime files, 30
resident afterimages, 22 hosted client files and four encrypted native handshakes
pass. Eight preservation checks and all rules are unchanged; full backup retained.

Open: owner in-game acceptance of hails, all-class merchant filtering, scroll
levels/scribing and WTS/WTB delivery on the updated client. Automated and runtime
checks do not stand in for those observations.

[Release status, rollback and exact QA](../releases/production-bugfixes-20260920.md).
