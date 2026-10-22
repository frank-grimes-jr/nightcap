# All-dungeon Keeper follow-up — October 22, 2026

Status: main PR274 / 7792171 deployed for live QA. Installed UTF-8/LF source matches
SHA903086e695615f3c8f3f3a05ca1bf3bd96c1d8a6cff4700fc7ad6858215580b1.
All 12 aggregate quest reload acknowledgments arrived before the four NPC signals;
world/all 12 zone lifetimes, five service identities and waypoint hash were retained.
No restart occurred. Owner says Befallen is "Not tested yet"; all-zone visual QA
remains open. See deployment.json for the exact receipt. The user explicitly called out
the remaining zones after main/server deployment of the initial Befallen scope.

## Audit and scope

Fresh production queries cover all seven Keeper definitions, spawn/grid/roam
fields, exact zone/name/ID quest overrides, waypoint locations and available
non-corpse saved poses. All use the intact shared eye quest, normal targetability,
bodytype1/model0 and stationary spawns. Saved service rows found in Befallen,
Unrest and High Keep have empty buffs. No zone-specific override was found.
All seven production map hashes match the maps used by the native geometry probe;
all original Keeper anchors have valid ground. This does not prove client rendering.

Unrest, Najena, Permafrost and Nagafen's Lair still share exact XYZ with their
waypoints. High Keep and Cazic-Thule are already separate and retain their poses.
No additional rendering cause has been established for those two zones. The
earlier Befallen correction is preserved. Four fixed poses are added to the
same ID-and-zone guarded quest policy, applied on spawn or signal 20261022/20261014.

| Zone | Keeper ID | Player /loc after correction | Heading |
|---|---:|---|---:|
| Befallen (retained) |999227| -67,35,3.1 |256|
| Unrest |999228| -38,67,3.1 |384|
| Najena |999230| -61,858,4.1 |256|
| Permafrost |999232| -121,46,2.1 |128|
| Nagafen's Lair |999233| -424,-248,-108 |384|
| High Keep (unchanged) |999229| -16,88,4 |0|
| Cazic-Thule (unchanged) |999231| 71,-74,4 |0|

Four new destination/approach pairs pass 40 native ground/headroom samples and 8
clear rays. Nearby doors, spawns and zonepoint metadata were inspected. No door
intersects these areas. Najena moves north away from its existing skeleton;
other added destinations have no unrelated spawn within the audited 25-unit box.
The Native map's ground/headroom evidence is separate from in-game acceptance.

## Validation and activation

New regressions fail 8 checks against the Befallen-only quest. Candidate passes 52
Keeper assertions, 16 unchanged waypoint assertions, 10 position-recovery assertions,
8 operator tests and both quest syntax checks. Native GMMove, saved-state ordering
and guard preservation remain as reviewed for the Befallen release. No dungeon
actions, deadlines, credit, rewards, resets, discovery, waypoints, binaries or
client files change. The client model remains the shared race108 eye.

`python run.py check` verifies the scoped suite. `python run.py apply` requires
clean main-promoted files, exact installed3c22ca3d preimage, both deployment/GM
locks, retained original/candidate/recovery bytes and an atomic quest install.
It verifies 12 aggregate quest reload acknowledgments before signaling only the
four added NPC types. Native/service lifetimes and waypoint hash must match.
Shared logs do not identify each worker; signal transport is not visual proof.
The new payload preserves committed UTF-8 bytes, normalizing only CRLF. No restart
or timer reset is used; unbooted zones apply the policy on normal next load.

`python run.py rollback` installs the inverse-position helper for the four new
poses while preserving Befallen's prior correction. Retain it to normalize dormant
saved poses on their next load. Do not restore old player/dungeon/loot snapshots
or only the old quest bytes. Once this successor is installed, use its own guarded
recovery rather than the superseded Befallen operator.

## Exact in-game QA

In each of the seven zones, use the /loc table, select the eye directly, and hail
for the correct dungeon's Raid/Grind/Status choices. Confirm the eye/nameplate is
visible from both sides. In the five corrected zones, the waypoint must remain 15
units away at its prior location and discovery/recall must still work. High Keep
and Cazic-Thule have distant separate waypoints; do not expect one beside the Keeper.
Re-enter and repeat after a normal unloaded-zone boot or existing private-instance
entry. Existing run identity, deadline, credit and rewards must remain; do not reset.
If any eye remains invisible, `/target Instance_Keeper` is still a workaround and
the shared client appearance path remains open investigation. The owner has not tested Befallen yet; no visible resolution is accepted in any zone.

Wiki20261022-dungeon-keepers-v1 is published. All 465 public hashes and security
headers, five private-route denials, 16 Linux publisher tests and actual pointer
rollback rehearsal pass. Three guides/search changed; private guide, services and
web configuration were preserved. Guides retain Live testing and /target fallback.
Independent review found no blocker in the final exact geometry, source, recovery
or operator. See wiki-publication.json and wiki-public-verification.json.
