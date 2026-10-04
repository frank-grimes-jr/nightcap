# Phase 47: Compact resident campfire

The six named residents gather closer around a native small campfire.
Glorphyndel becomes a High Elf with his existing Valorium and sword/shield.
Nalin keeps social facing without full-body emotes; SoulFire uses the correct
two-handed attack skill. No client asset or progression changes.

Checks pass: 16 MariaDB forward/recovery cases, 24 rollout fault tests,
75 resident/porter assertions, 65 ground samples and six approach rays against
119 actors and eight walking routes. Native CAMPFIRE is verified in the installed
archive. Independent review found no blocking defect. Direct main/server release
is complete via PR 115. Automated deployment checks passed. Detailed operational
evidence is retained privately.

Remaining: rendered fire height/scale/click behavior, Glorphyndel's appearance,
and Nalin's intermittent sword pose across idle cycles and zoning/reconnect.
[Scope and exact QA](../releases/tunnel-campfire-20261002/README.md).
