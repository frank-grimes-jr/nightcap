# Phase 38: Advanced-loot client foundation

Date: 2026-09-30. In-progress feature on `feature/advanced-loot`; not deployed.

## Built

Native RoF2 screen lifecycle and exact `/advloot` hook in the Nightcap proxy,
server-snapshot client model, bounded action requests, search/paging/filter and
shared-loot controls, generated SIDL screen, and matching guarded patch catalog.
The x86 proxy build succeeds. Shared server decision policy and preference
storage source provide the next integration points.

## Cut

The earlier classic-loot-window prototype was removed from the ignored working
source. It did not supply the requested window and had an unrelated death hook.
No requested advanced-loot behavior is removed from the accepted scope.

## Shaky / incomplete

The server queue and actual item-transfer adapter are still required. The UI has
not been exercised inside eqgame; native rendering, skin reload and real packet
traffic remain unverified. The preference migration has not run. Successful
compilation does not establish runtime readiness or player acceptance.

Exact evidence and remaining requirements:
[advanced-loot implementation](../releases/advanced-loot/README.md).
