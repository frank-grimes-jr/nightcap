# Phase 35: Tunnel travel alcove

September 21, 2026. Dev/test candidate; manual acceptance pending.

September 22 follow-up: promoted to main and deployed to production at the
owner's explicit request. Full production backup restore, migration/rollback,
46 preservation checks, runtime hashes and four public transport checks passed.
[Production evidence](../releases/tunnel-travel-alcove/PRODUCTION.md).
Manual appearance and gameplay acceptance remain open.

The owner's subsequent hail test found that production had installed the helpers
outside its configured plugin path. Corrected the deployment and restarted at
19:18 UTC September 22. The installed-runtime check now resolves configuration
and passes 25 quest assertions; four regression cases catch path mistakes.
[Incident, verification and current rollback](../releases/tunnel-travel-alcove/HAIL-FIX.md).

September 30: the owner confirmed Merrin is fixed. The gameplay revision was
already on main and the three active quest files matched it on the newer pet
runtime. Reverified installed dialogue/destination handling, static content and
native hashes without changing or restarting production. The report resolves
the hail/click issue, while the full QA matrix below remains unclaimed.
[Current evidence](../releases/tunnel-travel-alcove/OWNER-QA.json).

Built one human travel guide and three rustic Commonlands props in place of the
ten PoK city stones. The guide preserves all ten exact landings and leaves all
twelve return/PoK books and existing services intact. Added guarded migration,
post-activity rollback, quest tests, database rehearsal and native geometry checks.

Cut: alternative ten-rock layout, new client assets and additional destinations.
The existing optional client map labels remain cosmetic legacy labels. The
initial corner failed ground checks; the final alcove has verified floor and
headroom. Renderer appearance, selection/Find, all round trips and pet passage
remain owner QA gates. Local and hosted content baselines differ; this patch
does not claim parity or deploy the separate tunnel-services release.

Evidence, current activation status and exact owner steps:
[release guide](../releases/tunnel-travel-alcove/README.md).
