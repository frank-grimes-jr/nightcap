# Wiki production loot reader

Candidate October 22, 2026. **Not installed or published.** Owner choices: any
held class by default; automatic refresh. The active wiki is separately recorded
in `nightcap-wiki.md`. This runbook grants no standing deployment permission.

## Scope and operation

`wiki/loot_capture.py` runs fixed allowlisted SELECTs in a read-only consistent
snapshot, using `/run/secrets/db_backup_config` inside the existing DB container.
No accounts, player rows, arbitrary SQL, credentials or raw dumps are public.
Queries have a 45-second statement timeout; the service has a ten-minute timeout,
1 GiB memory cap and low scheduling priority. No game or client reload is needed.

`loot_model.py` resolves current production era, runtime/SQL content flags, ordinary
spawns, disabled spawn overrides, global loot, level ranges, multipliers and quality
rolls. Results describe newly generated database loot; saved loot, script-generated
content, current encounter access and looter eligibility can differ. The native
pool comparison uses the reviewed checkout method, not an assertion that every
currently running binary is byte-identical.

`loot_refresh.py` serializes one complete public generation, checks identity pairing,
then atomically switches a relative `wiki-data/current` symlink under an exclusive
process lock. Failed captures leave the last good generation. Retain eight (~2 hours)
for open tabs; after pruning, a stale detail link can reload the current index via
Try again. The UI timestamps data and warns after 45 minutes. A refresh runs at boot
and fifteen minutes after the previous run finishes, with up to thirty seconds jitter.

Public contract (GET/HEAD only, schema 1):

- `/loot-data/current/index.json`: capture time, active era, items/filter fields and
  immutable `base_url`; no browser-provided query reaches the database.
- `/loot-data/<16-hex-snapshot>/index.json` and `/item-<positive-id>.json` beneath the
  same snapshot: public stats, source NPC/zone, calculated min/max percentage and
  spawn locations/conditions. Coordinates display as `/loc y, x, z`.
- All other data paths, raw captures and manifests: denied by the wiki catch-all.

The current 6,293-item snapshot uses about327MB disk; keep at least4GB free for
eight snapshots plus staging. Local offline peak RSS633572KiB. Future growth must
recheck time, disk and memory. Compression is enabled only for the JSON route.

## Prepare and install after approval

1. Re-read current origin release/config, service identities and private download
   hashes. Reconcile intervening wiki publications; do not overwrite them with this
   candidate. Verify `check_refresh.py --repo CURRENT_CHECKOUT --ref HEAD
   --include-worktree` and its reviewed changes. Public content labels must be
   updated to released only with actual successful installation/publication.
2. Run Windows and offline Linux checks in `wiki/README.md`. Package the complete
   static wiki using `build.py --package ABSOLUTE_NEW.tar.gz`. The data snapshot is
   **not** inside that public HTML archive. No local raw capture needs uploading.
3. Stage the reviewed Python operator files (`deploy.py`, `loot_install.py`,
   `loot_capture.py`, `loot_model.py`, `loot_refresh.py`), JSON nginx fragment and
   two systemd unit files in a private host directory. Record exact hashes. Reject
   preexisting effective units, drop-ins, installed reader, or config drift.
4. As root run `python3 -B loot_install.py --expected-config-sha CURRENT_SHA
   --wiki-manifest /opt/nightcap/deploy/production/website-history/CURRENT_RELEASE/manifest.json`.
   This shares `website-history/.lock`, preserves the bind-mounted config inode,
   starts the actual sandboxed service once, requires a fresh capture, inserts
   only the wiki JSON route, tests/reloads nginx, verifies public/denied paths,
   rehearses the inverse, then enables the timer. Game services are untouched.
5. Publish static HTML with the existing guarded `update.py` using the installer's
   **new** config SHA and freshly verified previous release. Verify every public
   file, actual JSON and item navigation, timer activity and a second capture.
   Record installation, public verification and browser acceptance separately.

## Verify and recover

`systemctl status nightcap-wiki-loot.timer nightcap-wiki-loot.service` and
`journalctl -u nightcap-wiki-loot.service` show captures/failures. Logs include
counts, capture time and SQL error number, never credentials or captured rows.
Check timer LastTrigger/NextElapse and public `captured_at`; unchanged captures after
45minutes require investigation. This timer does not send chat notifications.

For rollback of this initial reader installation, revert the HTML to the prior
verified release with the normal guarded wiki updater, then invoke
`python3 -B loot_install.py --rollback /opt/nightcap/deploy/production/website-history/20261022-wiki-loot-reader-v1`.
It requires the exact installed config/file hashes, stops only owned units, restores
the config in place and verifies the data route closes while private resources and
container IDs/start times remain. Snapshot data/receipts are retained. If a later
operator changed config or files, it refuses; inspect and prepare a scoped inverse.

A failed installer attempts the same owned inverse; a failed stop/reload or ownership
drift is reported as manual recovery required. Do not overwrite concurrent changes.
Inspect receipt preimages and installed hashes before completing interrupted steps.
Never rerun the original whole-wiki installer or restart the game for this feature.
