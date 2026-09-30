# September 30 production operations

These are archived, reviewed inputs to this specific release, not generic
deployment commands. See [production evidence](../PRODUCTION.md) for the actual
result and [live QA](../LIVE-QA.md) for owner acceptance.

- `build.py`: fresh world/zone build over the manifest-verified hardened
  production source, with an exact 24-path allowlist and source stability checks.
- `production-source.patch.gz`: the complete resulting production source delta,
  compressed without changing the patch bytes.
- `package-server.py`: exact native hashes and scripts in the server package.
- `rollout.py`: preflight, private full backup/restore rehearsal, additive DDL,
  guarded activation, matching-client gate, and emergency hold.
- `appdb_probe.py`: actual game-account privilege probe; all writes roll back.
- `test_rollout.py` / `rollout-tests.log`: 13 isolated orchestration fault tests.
  They forbid real subprocesses; they do not validate actual gameplay.
- `publish-client.py`: verified immutable assets, then atomic signed channel
  replacement while player access is closed and the matching server is healthy.
- `verify-client.go`: public-key signature and complete local/HTTPS byte checks.

The installed scripts and manifests remain on the production host. Git attributes
preserve exact archived script/manifest bytes; the package manifest hashes the
installed files. Full native source fingerprints and build/configure logs
are retained as compressed files beside this directory.

## Recovery boundary

The helper durably records the first attempt to start a receipt-aware server.
After that boundary it never selects an older binary or restores an old PEQ dump.
A failed activation holds access closed and retains data for reconciliation.
Emergency `hold` works even if the staged manifest is corrupt or the gateway
container is absent; it attempts to stop the game and verifies both closures.

`open` is a one-time initial deployment gate. It requires the original preservation
fingerprints and is not a general reopening command after players have returned.
For a later repair, capture a fresh baseline and use reviewed receipt-aware code.
Retain claims, preferences, checkpoints, logs and subsequent player progress.

The backup and database diagnostic logs are private on the host. Do not commit
them or expose them under the public download directory. Production signing
material stays on the owner's machine and is absent from these artifacts.
Automatic approval review declined a local copy of detailed production evidence
because it may contain internal metadata. That copy was not performed; the public
record uses successful command outcomes and public/local artifact verification.
