# Keyless passage into The Hole — deployed October24

The owner requested removal of the key requirement for the passage into The
Hole. Production read-only capture on October 24 identifies Paineel's entrance
rock: `doors.id=10599`, door3, version0, `PAROCK105`, at `/loc 568,-896,-96`.
It requires Hole Key6379 and lockpick60. The patch clears both fields; either
remaining nonzero would retain a lock under `Doors::HandleClick`.

This is an access convenience. Encounters, levels, loot, instance admission,
and progression rewards are unchanged. Paineel city lift doors7301/7302 retain
Bone Crafted Key6378. The Hole's internal doors6863/6864 retain Sacred Key6380.
No key item, keyring entry, inventory or character row is removed.

## Implementation and verification

`tools/hole_passage.py` uses existing `content_patch.patch_sql` mechanics:
transactional table/no-trigger checks, locked exact-scope count and full-row
case-sensitive preimage checks. Only one UPDATE with two changed fields is
generated in each direction. SQL exceptions roll back. Repeated application
rejects instead of silently accepting an unknown state.

`production-before.json` is public content only, not a player backup and not a
permanent deployment preimage. `forward.sql` and `rollback.sql` are reviewed
candidate SQL. Capture fresh state before application and compare; investigate
any drift rather than regenerating away a failed guard.

Three focused Python tests pass. `rehearsal.json` records execution against an
isolated local MariaDB schema with all399 captured Paineel/Hole doors: exact
two-field forward change, inverse restoration, repeated-apply rejection,
key/lock/name-case/position drift rejection, and trigger/engine rejection.
Local PEQ and production were not written. The disposable schema was removed.

Source review: existing generator/escaping and full-row guards are reused;
no new runtime policy, native hot path, credentials or player mutation is added.
The actual SQL rehearsal checks preservation, rather than only matching text.
Observed native source: `akk-stack/code/zone/doors.cpp` HandleClick;
`zone/worldserver.cpp` Doors reload; `zone/zone.cpp` ReloadStaticData.
Confirm the deployed retained-source counterpart before activating reload.

## Activation and recovery

Owner approved main/live activation. PR318 merged as7f126acb; deployed.json
records the successful two-field production update at11:51UTC October24. Fresh
45.4MB compressed full PEQ backup was verified by decompression/hash. Paineel
was unloaded immediately before and after the commit, so its next normal boot
loads the new door values. All398 other captured doors, keys, native/service
lifetimes and health are preserved. No restart, static reload or client patch
was needed. Backups and exact before/after receipts are retained privately in
/opt/nightcap/backups/hole-keyless-passage-20261024. Owner gameplay acceptance
is still pending. The steps below remain the guarded recovery/refresh contract.

1. Take the shared deployment/GM locks and a fresh database backup. Hold entrance
   use during application/reload. Capture all Paineel/Hole doors again and compare
   against the reviewed preimage; confirm InnoDB and no doors triggers.
2. Apply the reviewed forward SQL through the private DB client configuration.
   Verify only id10599 keyitem/lockpick changed, with all399 captured rows
   otherwise exact (reconcile any independent drift explicitly).
3. Refresh Paineel through the supported `#reload doors` command in Paineel or
   authenticated equivalent targeted to that zone. This invokes ReloadStaticData,
   which also refreshes zone points, traps, ground spawns and objects; confirm
   no unrelated staged content in those scopes before issuing it. Quest reload
   alone does not reload doors. Do not kill a production zone process: the
   supervisor would restart the entire game runtime. If Paineel is unloaded,
   its next normal boot reads the new door data; re-entering an already running
   zone does not suffice.
4. Verify the matching reload acknowledgment, health, live row and player QA.
   No native/world/cache/client pairing changes are required.
5. For reversal, apply the guarded inverse only against its exact afterimage,
   then perform the same supported refresh. Restore only the two door fields;
   never restore player/keyring snapshots. If reload fails, retain the known
   database state and hold entrance use until reload/recovery is verified.

## Exact in-game QA

Use a non-GM character without Hole Key6379 in inventory or keyring and without
lock picks. In Paineel, approach the rock at `/loc 568,-896,-96`, click it, and
verify it opens without a key/locked message. Walk the passage and zone into The
Hole. Return and repeat after the rock closes; repeat with another non-GM player.
Confirm the Paineel city lift still requires its Bone Crafted Key and internal
Sacred Key doors still retain their existing locks. Check normal nearby objects
and zone transitions after the static reload. Record owner results separately
from SQL and runtime verification. All gameplay QA is pending.

## Whole-wiki impact review

Current wiki authority: feature/chapterhouse-wiki405aa570, with the candidate in
`E:/EQ_Local_Dev/_worktrees/hole-keyless-wiki` / feature/hole-keyless-wiki.
All24 maintained articles and447 generated reward routes were reviewed for scope.
Travel, Features, home, dungeon guidance, The Hole zone page and Recent changes
receive Live testing notes after verified activation. Commands, items, rewards, catalog values,
class guides and other zones have no changed behavior. No new gameplay command.
`check_refresh.py --repo .../hole-keyless-passage --ref HEAD --include-worktree`
correctly reports this candidate's sources as requiring review. Do not advance
the old source ledger to hide unrelated drift. Wiki20261024-hole-keyless-v1 is published:483 files verified,476 unchanged and
seven intended guide/search outputs updated. Publication rollback was rehearsed;
private downloads, configuration and all service lifetimes are preserved.
All68 Linux wiki tests pass. The build reproduces the published Windows HTML
newlines and exact shared asset bytes, including the existing CRLF build-lab.js;
normalizing those bytes changes every page asset hash. Both mismatched packages
were rejected before upload/publication. See wiki-package-review.json and
wiki-publication.json.
