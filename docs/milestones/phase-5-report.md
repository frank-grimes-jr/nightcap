# Phase 5 — Combined live QA deployment

2026-09-15. Owner authorized all implemented changes for live testing.

## Delivered

The reviewed AA ownership/atomic release candidate, five server fixes, PoK
arrival hub/class guidance, and bag pricing are deployed. Matching world and
zone binaries are running; the inherited skill and waypoint implementation is
available for QA. PR #49 merged the release to dev and the same commit f200325
advanced to test. Main was not promoted and no gameplay issue was closed.

## Verification and operational corrections

351 server/AA evidence tests, four planner tests, 14 MariaDB hub controls, three
bag-pricing tests, 13 AA-title tests, merged Lua/Perl checks, and independent
source/binary/plugin review passed. All 2,787 pinned source hashes matched.
A full backup was verified before mutation; exact rollback assets remain local.

The old world deleted the custom AA XP rule as unknown during startup. A matching
world build now retains value 1. Seventeen stale PoK custom-NPC saved states
would have restored old locations; exact rollback rehearsal preceded scoped
eviction, preserving the remaining 245 states. One world and eight zone workers
passed executable-hash and startup-log checks after the corrected restart.

## Remaining and excluded

Owner in-game checks remain for every deployed feature, particularly transactions,
network reconnect, client rendering, terrain clearance and merchant interactions.
Unimplemented client gates, missing-title remediation, Bard fixes, augment content,
launcher delivery and experimental balance policies were not represented as
shipped. Website publication initially required specific public-destination
approval; the owner subsequently provided it. See [phase 6](phase-6-report.md)
for the website/documentation follow-up.

[Deployment evidence and rollback](../releases/live-qa-20260915/README.md).
[Exact owner QA checklist](../releases/live-qa-20260915/QA.md).
