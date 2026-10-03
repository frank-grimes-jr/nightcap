# Phase 50: Compact tunnel service areas

The owner accepted the resident campfire group and requested tighter organization
for the remaining services. Four class gatherings now pair all 16 trainers with
their merchants, the tradeskill workshop is about 48% smaller, and traders and
walking routes follow the new arrangement. All 119 NPC definitions and gameplay
functions are preserved, including the accepted residents and their fire.

The implementation includes guarded forward/rollback SQL, focused layout tests,
real-schema database rehearsal, native map collision probes and the reviewed
deployment adapter. PR 119 is on main and live after full-backup restoration,
19 database checks, 75 installed quest assertions and server/public-session
verification. The current loot-server build, runtime files and client assets
were retained.
Cut: no custom textures or client download; native campfires supply landmarks.
Still open: rendered crowding, fire scale, name readability and actual station
interactions need the owner's in-game inspection.
[Design, scope, checks and exact QA](../releases/tunnel-compact-20261002/README.md).
