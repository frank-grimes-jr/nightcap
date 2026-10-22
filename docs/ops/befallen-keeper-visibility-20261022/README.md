# Befallen Keeper visibility — October 22, 2026

Status: historical Befallen-only release, superseded by [the all-dungeon follow-up](../dungeon-keeper-visibility-20261022/README.md). Use the successor recovery operator against the current shared quest. Visible acceptance remains pending.

The installed quest SHA is `3c22ca3d3e4a1b39b56c018ea97c5daea5abf735b633bf8a389ebb6ae7e8da4d`.
Twelve aggregate quest reload acknowledgments arrived before refresh signal 20261022.
World and all 12 zone PID/start times, five service identities/start times and the
waypoint quest remained unchanged. Befallen was unloaded at preflight; its next
normal boot applies EVENT_SPAWN. No restart, database rewrite or client patch.
The operator's nine tests pass; independent review approved the repaired
reload-before-signal ordering. See deployment.json; this is deployment evidence,
not proof of signal processing by an absent NPC or visible rendering.

The owner reports a targetable but invisible Instance Keeper in Befallen. A fresh
production read found Keeper 999227 / spawn 3266036 and waypoint 999240 / spawn
3266054 at identical DB XYZ `35,-82,3`, heading 0. Both saved public-zone NPCs
were at `35,-82,3.1`. The waypoint uses a portal nimbus over an invisible actor;
the Keeper uses a small eye. Overlap is confirmed. It is a plausible cause of
occlusion and poor selection, not proof of every rendering failure.

Before deployment, the installed Keeper quest was intact (SHA-256
`b4fc39bd29cbc0856b8ec9bd0072285e5cade672fa43cf853bf96009d30bf7a9`).
All seven Keeper definitions have bodytype 1, model override 0, and normal
targetability. The inspected E:/Nightcap client has both EYE and its Classic ZAP
alias and its October 21 log records loading that alias. That installation's
archive presence does not prove rendering on the reporting client.

## Released correction

The shared Keeper quest applies an absolute position only for NPC 999227 in
Befallen: DB XYZ `35,-67,3.1`, heading 256, or player `/loc -67,35,3.1`.
This places the eye 15 units into the entrance, facing arrivals. The native map
probe verifies the destination and approach against the same map bytes as
production. Ten ground/headroom samples and two approach rays pass. No nearby
static door was found; the existing nearby enemy spawn remains untouched.
Production pathgrid, roam distance/bounds and wp_spawns are all zero, so later
spawn initialization cannot replace the guard spot with a patrol or roam box.

`keeper_position()` runs after the eye appearance on EVENT_SPAWN and signals
20261014/20261022. It uses the exported `GMMove(x,y,z,heading,true)` binding,
including the NPC's guard spot, and ignores a pose already within 0.25 units.
The native spawn event runs before spawn publication. Saved-state construction
passes its old pose into the NPC before that event; subsequent state restoration
loads HP, loot and buffs, not position. Thus the correction covers fresh spawns,
old saved poses and loaded eyes, including private instances. The existing
`keeper_visual` early return cannot skip placement.

No instance action, reset, reward, deadline, corpse, discovery, portal, native
binary or client asset changes. This intentionally owns the service pose in its
quest rather than rewriting arbitrary saved dungeon state. The DB spawn remains
the historical anchor; future placement changes must update this quest policy.

## Checks

The expanded Keeper test fails against the previous quest at the new relocation
expectations. With the candidate, all 30 Keeper and 16 waypoint assertions pass;
Perl syntax passes. Coverage includes existing race-108 actors, fresh/saved spawn,
repeat and unrelated signals, exact NPC/zone guards, ground tolerance and all
prior native/legacy dialogue/reset authorization checks. Native binding and
spawn/saved-state ordering were inspected separately; Perl doubles do not prove
client rendering. Independent review found no blocking implementation issue;
its saved-state test wording and rollback caveats are addressed. See evidence.json for geometry fingerprints and observations.

## Activation boundary and recovery

The owner explicitly authorized main and server deployment on October 22. Before activation,
recheck the live quest hash and service/zone lifetimes under the deployment and
GM locks; retain the exact previous quest. Install the reviewed committed quest
atomically, use the supported quest reload without resetting timers, and send
the existing cross-zone NPC signal protocol to type 999227 with signal 20261022.
Verify reload completion/errors and unchanged native process lifetimes. Future
Befallen zone boots apply the same pose. No runtime restart or client patch is
required. Do not kill/repop a zone or reset a dungeon to refresh this NPC.

For rollback, retain the correction helper but set its canonical pose back to
`35,-82,3.1`, heading 0; reload and signal it. Keep that recovery helper installed
until any saved relocated NPCs have been normalized on load. Restoring only the
old quest bytes can leave a saved relocated pose behind. Never restore old player
snapshots, dungeon ledgers, loot or whole zone state for this cosmetic rollback.

## Exact owner QA

1. Enter public Befallen. At `/loc -82,35,3`, the waypoint remains in place.
   The small eye named Instance Keeper should be visibly separate, 15 units
   farther in, at `/loc -67,35,3.1`. Check its model and nameplate from both sides.
2. Click the eye directly and hail. Confirm Befallen Raid/Grind and Status options.
   Existing run identity/deadline/credit must remain unchanged. Do not reset it.
3. Zone out and back. Repeat after a naturally unloaded zone boots; verify the
   pose does not drift. Retest an existing Raid/Grind instance when convenient.
4. Confirm the original waypoint still discovers/recalls normally. Check another
   dungeon's Keeper is unchanged. If the separated eye is still invisible, keep
   this issue open and capture the reporting client's fresh model/target evidence.

The older October 13 acceptance remains historical and does not close this new
Befallen report. Deployment is verified; this report still has no owner rendering acceptance.

## Guarded operator

`python run.py check` checks syntax and all scoped regressions. After main promotion,
`python run.py apply` verifies the pinned live preimage under both deployment and
GM locks, retains original/candidate/recovery bytes and checks native lifetimes,
service identities, unchanged waypoint and quest reload acknowledgments.
`python run.py rollback` installs the retained position-recovery helper.
Receipts are retained in `/opt/nightcap/backups/befallen-keeper-visibility-20261022`.
An incomplete operation must be inspected; never blindly retry it.

## Wiki publication

Release `20261022-befallen-keeper-v1` updates Dungeon modes, In development,
Recent changes and search. The entire wiki impact review retains Features/home,
commands and all generated reward values. The guarded publisher verified 465
origin files, rehearsed pointer rollback, and preserved services/private downloads
and web configuration. Sixteen Linux publisher tests pass. An initial missing
nginx test fixture stopped before publication; its failure remains in the private
stage and the old pointer/stage hashes were verified before completion. Public
hashes and headers are independently recorded in wiki-public-verification.json.
This publication does not establish visual acceptance of the Keeper.

## Source encoding provenance

Committed LF quest bytes hash `e78eb53a54a8d39ac915efa0c131c0171094841d833842c5802f57895ae865a2`.
The installed `3c22ca3d...` payload came from Windows cp1252 decoding followed by
UTF-8 encoding in the inherited operator pattern. Only nine comment lines changed;
executable code and dialogue are identical. deployment.json records both hashes
for candidate and recovery. The historical operator now states this encoding
explicitly to preserve the exact retained recovery-byte guard. New release
operators should preserve UTF-8 bytes. No further runtime write was necessary.
The ninth operator regression verifies the comment-only boundary and payload pin.
