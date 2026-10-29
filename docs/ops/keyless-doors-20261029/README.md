# Remove door keys and lock-picking requirements

Status: deployed to OVH at18:01UTC October29 after owner-approved main PR370
(7cb0ec4a) and operator corrections PR371/372 (final17509a22). All194 locks across
48zones are cleared, including129 negative lockpick sentinels. All19272 door rows
match their exact expected afterimage;19078 unrelated rows are unchanged. The
full backup is verified and the temporary native Paineel hold is released.
All12 worker/five service lifetimes remain unchanged; health passes. No restart.
Paineel naturally unloaded before SQL, so no affected loaded zone required a
static refresh. Subsequent normal zone loads read updated definitions.

`deployed.json` and independent `activation-guard.json` record verification.
Wiki20261029-keyless-doors-v1 is published; six files changed and493 preserved.
Fourteen activation/recovery tests, seven policy/Hole tests and nine real SQL
rehearsal groups pass. Owner gameplay acceptance remains pending; follow the
exact non-GM route below. Raw data/SQL remain private. See `AUTHORIZATION.md`,
`review.json` and `native-source-review.json` for authority and source review.

## Behavior and scope

Clear `doors.keyitem` and `doors.lockpick` for every existing locked door across
all zones and versions, including negative lock-picking sentinels. Ordinary
clicks then use the existing unlocked-door path. This includes Paineel's city
lift, internal Hole doors, Befallen locks and Plane of Sky key transports.
Clearing only keyitem is insufficient when lockpick is nonzero.

Only these two content columns change. Preserve guild ownership, trigger chains,
positions, animations, destinations, instance IDs, content/expansion gates,
adventure and dynamic-zone switches, quest scripts, zone flags and level gates.
No items, keyring entries, characters, encounters, loot or earned progression are
deleted or granted. Adventure admission items and scripted quest/zone eligibility
are distinct from ordinary door locks and remain in place.

This removes an exploration requirement as explicitly requested by the owner;
it does not retune encounters or rewards. Imported/reintroduced door content must
be reviewed for nonzero lock fields; this is a content migration, not a native
override of future content or quest-created locks.

## Source and evidence

- `tools/keyless_doors.py`: deterministic plan plus guarded forward/inverse SQL.
- `tools/keyless_doors_capture.py`: read-only complete content capture, with
  numeric strings matching the SQL preimage comparison (including FLOAT fields).
- `tools/tests/test_keyless_doors.py`: four policy/validation regression groups.
- `tools/tests/rehearse_keyless_doors.py`: real MariaDB rehearsal in a uniquely
  named disposable copy of local PEQ doors; never writes local/live PEQ.
- `rehearsal.json`: 19,264 rows, 195 locked rows; all eight check groups pass,
  including exact inverse, replay rejection, stale identity/position/lock values,
  new locks, deleted rows, unrelated edit preservation, triggers and table engine.
- `production-rehearsal.json`: all 19,272 captured production rows reconstructed
  exactly using DOUBLE-precision companions for native FLOAT storage. All nine
  check groups pass, including exact full-table inverse and 194-lock removal.
- Existing Hole regression tests: three pass unchanged.
- Native reference inspected in `E:/EQ_Local_Dev/akk-stack/code/zone/doors.cpp`,
  `Doors::HandleClick`: both zero fields choose the unlocked path, including
  teleport-door handling; guild/trigger/adventure checks remain separate.
  The matching retained source is authenticated in `native-source-review.json`.
  No native source or protected client data is changed.

## Production preparation and activation

1. Owner approval and the initial production capture are complete. The script
   requires `sudo -n docker compose` on OVH. Use pinned-host SSH with Python stdin
   and private local output; it reads door definitions only, not player data.
   Re-capture before activation and compare against the reviewed preimage.
   Capture deployed source identity and active zone/instance inventory too.
2. Generate `forward.sql` and `rollback.sql` from that exact complete capture:
   `python -B tools/keyless_doors.py CAPTURE.json --output PRIVATE_OUTPUT`.
   The 194-lock/48-zone plan and its exact production rehearsal are complete.
   Run `python -B tools/tests/rehearse_keyless_doors.py --capture CAPTURE.json`
   for any revised preimage before requesting main/live promotion. Do not use local captures
   or the older Paineel-only release as production input.
3. Owner main/server/wiki authorization is recorded in `AUTHORIZATION.md`. Take shared deployment/GM locks and a fresh
   verified full PEQ backup; prevent concurrent content editing. Hold door use
   while applying and refreshing. Re-capture and compare exact door preimages.
4. Execute the guarded forward once, without the MariaDB `--force` option.
   It requires InnoDB/no triggers, locks the affected scope, verifies all captured
   rows and detects additional locked rows. It updates only two columns in one
   transaction. On an uncertain result, inspect current rows and receipts;
   never blindly replay or regenerate an inverse from the uncertain state.
5. Verify all original door rows against the expected afterimage and zero rows
   with `keyitem <> 0 OR lockpick <> 0`. Preserve player and runtime evidence.
   Reload doors through the supported authenticated API for every affected loaded
   zone/instance, or an explicitly authorized controlled whole-runtime restart.
   `#reload doors` uses ReloadStaticData, also refreshing zone points, traps,
   ground spawns and objects: review staged content before using it. New normal
   zone loads read updated rows; re-entering an already loaded zone is insufficient.
   Do not kill individual production workers. Quest reload alone is insufficient.
6. Verify acknowledgments, health and lock ownership before releasing the hold.
   Perform actual non-GM access tests using the owner QA route below; record
   database application, runtime refresh and owner acceptance separately.
   No binary, shared-item cache or signed-client update is needed. If a full
   restart is chosen, preserve the current release and authenticate normal market
   rotation rather than restoring a stale market/player snapshot.
7. Recovery uses the original guarded inverse, only against its exact afterimage,
   followed by the same supported refresh. It restores the two lock fields only;
   never restore player/keyring data. Retain later unrelated edits. Drift requires
   review and a scoped forward repair, not weakening the guards.

## Exact owner QA after activation

Use an ordinary non-GM character with no matching keys in inventory/keyring and
no lock picks. Use `private/qa-doors.json` for captured door IDs and positions (/loc is Y,X,Z).
Befallen IDs124/131/136, Paineel7301/7302, Hole6863/6864 and Sky5321/5328
are concrete targets. Paw40328 retains its triggertype254 and other metadata.

1. Befallen: click its formerly locked interior doors, pass through, let them
   close and repeat. No key, lock-picking or locked-message requirement remains.
2. Paineel: use both city-lift controls without Bone Crafted Key 6378; verify the
   lift operates and returns. The rock at `/loc 568,-896,-96` remains keyless.
3. The Hole: open internal Sacred Key 6380 doors without that key. Check reopening
   and returning through the passage after normal auto-close.
4. Plane of Sky: use a captured key transport with lockpick=-1 before migration,
   without its key; verify the intended destination and any ordinary zone gates.
5. Repeat representative doors in an existing private Raid/Grind instance and a
   newly created instance after refresh. Preserve the run and journal progress.
6. Test an unrelated ordinary door, a paired/triggered door and an authorized
   guild door. Guild outsiders remain restricted; trigger-only objects retain
   their activation mechanism. Check normal doors with an unrelated cursor item.
7. Repeat with a second non-GM character after normal zone unload/reload.
   Record practical shortcut/progression effects and gameplay acceptance.

## Wiki impact

All 40 authored article surfaces and generated catalog sources were scanned for
door/key/access claims. Travel, Features, In development and Change Log receive
Live testing guidance in the approved release. Travel and generated Hole guidance
now describe global keyless doors. Historical October24 entries retain their scope.
The immutable package changes exactly five HTML pages plus search; all 493 other
public files match the current 499-file baseline. Publish only after activation.
Home navigation, commands, equipment/reward stats and catalog values do not change
for this candidate. Historical Change Log entries retain their dated scope.
Run `wiki/check_refresh.py --repo THIS_CHECKOUT --ref HEAD --include-worktree`;
historical source drift remains review-required, not permission to advance pins.

## One-time operator

`run_activation.py` pins private inputs and the merged main revision, then sends
`activate.py` over pinned-host SSH. It holds shared deployment/GM fences, takes a
verified full PEQ backup, and uses the authenticated world protocol in `runtime.py`.
Paineel is the only affected loaded zone. An owned native zone-75 admission hold
and 125-second auth drain precede its empty-zone refresh. All 12 worker identities,
service lifetimes, exact full door afterimage and native reload logs must match.
No binary/client/cache update or service restart occurred. Ordinary future zone
loads read the updated content. The operator refuses additional affected loaded
zones until their static content is reviewed.

Remote receipts and backup are under `/opt/nightcap/backups/keyless-doors-20261029`.
Never rerun a partial operation: inspect `result.json`, exact DB state and native
lock list. An uncertain lock acknowledgment retains its recorded preimage; release
only the owned zone-75 hold against its exact postimage. Uncertain SQL must be
reconciled, never replayed. A committed update with refresh failure keeps the hold
for audited continuation. Full database rollback is not part of recovery.

## Activation acknowledgment correction

The first operator verified its backup and applied the native Paineel hold, then
stopped before SQL because successful lock broadcasts do not return to a
status-only world connection. Fresh read-only reconciliation proved every door
unchanged, locks [] -> [75], and the same empty Paineel worker. `runtime.py` now
checks an ordered explicit List response, filtering unrelated broadcasts.
`resume_activation.py` only accepts this exact pre-SQL receipt/preimage state,
persists a one-use interruption fence, and repeats the full auth drain before
using the reviewed activation tail. Thirteen tests cover this recovery and
no-broadcast/interleaved-broadcast cases; independent review has no blockers.

The subsequent125second drain correctly stopped before SQL when Paineel naturally
unloaded. All12 worker lifetimes and all door preimages remained exact; no affected
zones were loaded. `resume_unloaded.py` accepts only that receipt state and verifies
no affected loaded/booting zone before and after its one SQL transaction. Native
TriggerBootup publishes its boot state before sending the worker boot packet;
status exposes a zone or `...`, which the parser rejects. This continuation needs
no static refresh: subsequent normal loads read the new definitions. It retains
the owned hold until exact afterimage, health and unchanged services/workers pass.
Fourteen operator/regression groups pass, including newly loaded target rejection.
