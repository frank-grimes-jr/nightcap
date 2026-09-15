# Docker data migration — 2026-09-13

Moved Docker Desktop's data disk from C: to E: after C: ran out of space and
container commands began returning I/O errors. The owner authorized the move and
the required shutdown/restart. No server candidate binary was deployed.

## Storage

- Working disk: `E:\Docker\wsl\disk\docker_data.vhdx`.
- Original path: `C:\Users\verre\AppData\Local\Docker\wsl\disk` is now a
  Windows directory junction targeting `E:\Docker\wsl\disk`.
- Offline rollback disk: `E:\Docker\migration-20260913\docker_data.rollback.vhdx`.
- Verification record and original Docker settings:
  `E:\Docker\migration-20260913\verified-copy.json` and
  `settings-store.before.json`.
- Docker Desktop itself and its small WSL system disk remain on C:.
- MariaDB data remains in the existing bind mount
  `E:\EQ_Local_Dev\akk-stack\data\mariadb`; it is not inside the Docker VHD.

Docker and WSL were stopped, and exclusive file access confirmed the disk was
unmounted before copying. The original and working copy both had SHA256
`56f0643a706d5f597b01d3528e1bd6df77ae220791a99607cb7b5d7c598ee36e`
at a size of 21,280,849,920 bytes. Only after those checksums matched was the
original moved to the rollback location and the junction created. The working
disk naturally changes after startup; this hash describes the offline copy.

## Recovery and verification

Normal Docker shutdown was unresponsive during the disk-full condition, requiring
`docker desktop stop --force` and `wsl --shutdown`. Initial restarts encountered
stale Windows socket endpoints. Only runtime directories were renamed to preserve
them and allow fresh endpoints:

- `%LOCALAPPDATA%\Docker\run-before-migration-20260913`
- `%LOCALAPPDATA%\Docker\run-stale-20260913-2`
- `%LOCALAPPDATA%\docker-secrets-engine-stale-20260913-2`

Verified after successful restart:

- All ten existing akk-stack containers retain their pre-shutdown IDs and run.
- Both fail2ban containers are healthy (previously unhealthy).
- All four akk-stack named volumes are present.
- Container exec and the interrupted build log are readable again.
- MariaDB reports crash recovery complete and ready for connections. Read queries
  return 20 live characters and zero synthetic characters in the balance clone.
- World, loginserver, UCS, and eight zone processes run under the existing launcher.
- C: has approximately 24 GiB free after restart.

These are service recovery checks, not in-game QA or a full database integrity
audit. The attempted machine-readable pre-shutdown Docker inventories failed as
the engine became unresponsive; container IDs were compared with the earlier
successful console snapshot instead.

## Rollback and maintenance

Keep E: available before starting Docker. Do not delete or relocate the junction
target while Docker or WSL is running. No Docker settings key was changed.

For rollback, fully stop Docker and WSL and confirm exclusive access to the disk.
Preserve the current E: disk first. Restore the saved offline disk to the working
E: location, or restore a real directory at the original C: location after checking
free space and removing only the junction itself. Never recursively delete through
the junction. Restoring the saved disk rewinds container and named-volume state to
the migration snapshot; the separate MariaDB bind mount is not rewound with it.

The interrupted candidate build remains under `/tmp/nightcap-release-20260913`
inside the original EQ container. Its recovered log shows the zone target linked,
then the test build was interrupted. A successful rebuild and test run are still
required before release promotion.
