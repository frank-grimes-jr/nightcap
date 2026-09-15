# ADR 0031: Recover the whole prior client asset generation

Date: 2026-09-15. Status: transaction core tested; production release acceptance pending.

Installation must never leave mixed generations usable after a failed or
interrupted update. Per-file backup-and-forget cannot restore the release as a
whole, and a process check alone cannot exclude a launch during replacement.

## Protocol

1. Verify signed candidate metadata, acquire the Windows executable guard, and
   repeat exact executable preflight through that same handle.
2. Reject pending recovery. Fold the prior local active checkpoint into the
   caller's monotonic release/digest state, reverify the manifest, and hash every
   staged file. Marker presence is not trusted.
3. Snapshot every affected owned/retired path and the prior active record into
   immutable bounded backups. Write the canonical journal and flush all files.
4. Publish a digest-bound pending record before changing an installed asset.
5. Copy/hash/flush each replacement to a transaction-specific temporary file in
   its pinned destination directory, then use rooted rename. Apply tombstones.
6. Rehash the installed inventory. Write the signed active record last. Removal
   of pending is the transaction commit point. Play remains false.
7. On failure, restore the entire snapshot. On restart, pending triggers the same
   recovery. Validate every backup before the first recovery write, preserve
   backups for retries, recheck all prior files, then clear pending.

Recovery checks canonical bounded JSON, transaction IDs, digests, duplicate
paths, total sizes, and ownership. Only current inventory, trusted retired paths
and one final active record are allowed destinations. Directory handles are
pinned component by component; links/junctions/nonregular files are rejected and
identity is checked across opens. Already-correct originals are verified and
left in place, allowing recovery when Windows holds an unchanged destination
open without delete sharing. Missing new files remain absent after rollback.

## Evidence and limits

Windows subprocess tests terminate at pending, each replacement, tombstone and
active-record boundaries. A separate test terminates recovery and then retries
it. Native handle tests prove launch/updater exclusion. Other tests cover repair,
downgrade rejection, corrupt staging/backups, malicious journal paths, locked
files, junctions and cancellation. Independent review found no remaining blockers.

The active checkpoint and journal share the local user's filesystem trust
boundary. This is not tamper-resistant storage against that owner/admin. Production
key provisioning/rotation and signed rollback authorization remain separate work.
File bytes and absence are restored; arbitrary ACL/alternate-stream metadata and
sudden power-loss/storage-controller behavior have not been certified. Process
exit is tested. Completed backups and pre-journal orphans are retained for now;
retention/cleanup management is unfinished. Failure messages preserve pending
state when recovery cannot be proven. No real game files were modified.

The core verifies configuration asset bytes, not configuration semantics or DLL
runtime health. A valid installed record is not permission to Play. Full Wails,
release signing, exact patch preflight/health and in-game parity remain required.
