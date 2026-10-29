# Remove door keys and lock-picking requirements

Status: tested content candidate on `feature/keyless-doors`, based on current
`origin/main` 85a42253. Not deployed, published or accepted in game.
The production content capture awaits owner approval after automatic approval
review rejected exporting the complete production doors table. No production
door count or generated production migration is claimed.

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
- Existing Hole regression tests: three pass unchanged.
- Native reference inspected in `E:/EQ_Local_Dev/akk-stack/code/zone/doors.cpp`,
  `Doors::HandleClick`: both zero fields choose the unlocked path, including
  teleport-door handling; guild/trigger/adventure checks remain separate.
  Authenticate the currently deployed retained-source counterpart before reload.
  No native source or protected client data is changed.

## Production preparation and activation

1. Obtain approval for the blocked read-only production door capture. Run the
   capture script over pinned-host SSH with Python stdin and save its JSON in a
   private evidence directory. It reads door definitions only, not player data.
   Capture the deployed source identity and active zone/instance inventory too.
2. Generate `forward.sql` and `rollback.sql` from that exact complete capture:
   `python -B tools/keyless_doors.py CAPTURE.json --output PRIVATE_OUTPUT`.
   Review the actual affected count/zones and rehearse that production preimage
   in isolation before requesting main/live promotion. Do not use local captures
   or the older Paineel-only release as production input.
3. Main promotion needs owner sign-off under AGENTS.md. Coordinate an authorized
   maintenance window for activation. Take shared deployment/GM locks and a fresh
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
6. Verify acknowledgments, health and actual non-GM access before reopening use.
   Record database application, runtime refresh and owner acceptance separately.
   No binary, shared-item cache or signed-client update is needed. If a full
   restart is chosen, preserve the current release and authenticate normal market
   rotation rather than restoring a stale market/player snapshot.
7. Recovery uses the original guarded inverse, only against its exact afterimage,
   followed by the same supported refresh. It restores the two lock fields only;
   never restore player/keyring data. Retain later unrelated edits. Drift requires
   review and a scoped forward repair, not weakening the guards.

## Exact owner QA after activation

Use an ordinary non-GM character with no matching keys in inventory/keyring and
no lock picks. Use the fresh capture's door IDs and XYZ positions to locate locks.

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
explicit Not released notes. Current deployed Hole-only guidance and historical
October24 receipts remain accurate until activation. On activation, replace the
Travel restriction with the global policy, reconcile the generated Hole guidance,
promote the candidate labels and publish only after an authorized public release.
Home navigation, commands, equipment/reward stats and catalog values do not change
for this candidate. Historical Change Log entries retain their dated scope.
Run `wiki/check_refresh.py --repo THIS_CHECKOUT --ref HEAD --include-worktree`;
historical source drift remains review-required, not permission to advance pins.
