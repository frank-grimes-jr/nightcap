# Hidden Everfrost entrance

The owner selected the hidden pathway before Permafrost. The Ashen Compact now
starts inside that narrow Everfrost bypass, away from the ice-giant guard rooms.
The patron, Keeper and Kael return all use Everfrost, zone 30.

| Service | In-game /loc (Y, X, Z) | Server NPC ID |
|---|---|---|
| Drazhul Blackmantle | 2158, -6974, -61.0625 | 998877 |
| Kael Keeper and public return | 2174, -6974, -61.0625 | 998860 |

Drazhul explains an ice-giant frostbound crossing to Kael. Accepting the Compact
seals the pledge; the Keeper retains the normal expedition menu. This is original
Nightcap fiction. It does not make Everfrost geographically adjacent to Kael or
add a new fetch quest, item prerequisite or fifteenth story objective.

## What changed

Exact-ID scripts move from quests/commons to quests/everfrost. Native Keeper and
Drazhul host checks, the final journal row, patron dialogue, generated spawns,
Kael outbound doors/zone points and access policy all use Everfrost. The disabled
candidate SQL and its runtime checks are regenerated together. Normal Everfrost
and Permafrost spawns, exits and progression are not changed.

The regression rejects the former Commonlands host and instanced Everfrost hosts,
accepts the public Everfrost entrance and Kael services, and preserves Camil and
Hate entrance mappings. The isolated SQL rehearsal exercises reference collisions,
rollback, repeat refusal and progress preservation.

## Placement and evidence

The installed client map identifies the northern hidden bypass before the
Permafrost zone line. Read-only local public content confirms Everfrost zone 30,
the Permafrost connection and the three nearby ice-giant guards. Both final NPC
locations have a level native floor at -61.0625 and 24 units of headroom at all
five radial samples. The return uses the Keeper's tested point. All 39 existing
Kael placement probes also pass. Positions were centered within the passage to
leave clearance from both walls.

everfrost-source.json records the public content; authored-geometry.json and
host-placement-probe.json record collision evidence. everfrost-placement.json
records exact positions and the comparison against dev fe15aaae. All NPC
definitions, private Kael spawns, reward items and combat settings are identical.
The original 24 combat clears remain tied to their pre-relocation binary through
calibration-receipt.json and calibration-native-build-manifest.json.

The unpublished wiki overlay is reconciled with the published custom-Features
source a0bd0faa. Home and Features remain unchanged; the existing preview anchor,
new quest guide, affected instructions and one dated log entry own the guidance.
Historical-anchor checks enumerate every historical article, while ordinary
page/link checks also cover the newly added quest and item pages.

## Acceptance boundary

See QA.md for visible placement, hails, ordinary Permafrost passage, entry,
return and stale-Commonlands checks. The native build and collision checks do
not establish in-game acceptance. This remains an uninstalled test candidate;
main, live runtime/client activation and wiki publication are not authorized by
this location change. The existing candidate client archives remain unchanged.
