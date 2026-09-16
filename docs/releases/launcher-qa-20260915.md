# Local launcher QA package — September 15, 2026

## Open this build

`E:\EQ_Local_Dev\artifacts\nightcap-qa-20260915\nightcap-launcher-qa.exe`

The title and badge must say **LOCAL QA CANDIDATE**. The old development preview
still reports that updates are unavailable; use this separate executable.

The selected client is `E:\EQ_Local_Dev\artifacts\nightcap-qa-20260915\client`.
It is a complete ordinary-file copy, with `Host=localhost:5998`. Original client
executable, proxy, user INI and login-target hashes remain unchanged. Settings and
staging are under the package's `launcher-state` folder, independent of preview.

## Owner confirmation

On September 15, 2026, after receiving and testing this QA launcher, the owner
confirmed: **"It works."** This records owner acceptance that the delivered local
QA launcher works. Individual repair/recovery edge cases and the in-game
multiclass, equipment, skills, Bard and PoK acceptance matrix were not separately
reported by that confirmation; their existing issue gates remain open.

## Exact owner QA

1. Open the QA executable. Confirm the copied client path and installed release
   **2026091501**. If selecting a folder again, select this QA copy.
2. **Check for updates** should show four verified files. **Repair files** should
   complete and leave all four verified. This build carries its patch release
   internally; no hosted service is needed.
3. **Play Nightcap** should start EverQuest. The copied client may show its EULA
   on first launch; review it yourself before continuing. Keep the launcher open. Its state
   should become running; updating/changing folders/another Play remain disabled.
4. Log into the local server yourself. Test Darth and the exact multiclass,
   equipment, mana, Skills/Actions, held-Monk and PoK matrix in
   [the consolidated checklist](test-consolidation-20260915.md).
5. Quit normally, then launch again and use **Stop game**. Expect the owned game
   to close and Play to become available. Report any error in Activity.
6. Closing the launcher while the game runs first requests shutdown; close again
   after cleanup to exit the launcher.

## Package identity and limits

- Release: 2026091501; expires **2026-10-15 23:50:31 UTC**.
- Required files: proxy, bootstrap helper, feature config, patch-site catalog.
- `audit.json`, `manifest.json`, `signature.json`, `launcher-sha256.json` beside the
  launcher record exact public key, asset hashes and executable identity.
- Signing seed is outside the package; never share it or the copied client.
- This package applies/repairs its bundled release. New updates require a rebuilt
  QA executable. Hosted production updates and Authenticode are not delivered.
- Startup/repair evidence does not certify the in-game multiclass behavior.

## Build/rebuild

Run from `eq-launcher` after building the x86 proxy and bootstrap. Go and Wails
must be on PATH; frontend dependencies must already be installed from its lockfile.
Use an access-restricted signing-key directory outside source and the package.

```powershell
go run ./cmd/nightcap-package -client <absolute-QA-eqgame.exe> -key <absolute-private-seed> -new-key -release <new-increasing-number>
./build-qa.ps1 -Destination <absolute-package-directory>
```

Omit `-new-key` when reusing the private seed. Bundle generation exclusively
creates `internal/launcher/qabundle` and `policy_qa_generated.go`; use a fresh
checkout/output for each generation. Build one Wails package at a time per
checkout and close its QA launcher before replacing the executable. The script
restores the exact normal `wails.json` after generating QA Windows metadata.

For repeatable controller integration, use `go run -tags qacandidate
./cmd/nightcap-qa -client <QA-copy> -home <package/launcher-state> -action
check|update|play`. Play observes the game for 20 seconds then stops its owned
session; `-hold` changes this duration. This uses the public controller path.

## Recovery and rollback

Use the launcher's recovery action when an interrupted update is reported. The
installer retains journaled backups and verifies each complete generation. No
original client or server database was changed. To return to the previous client,
stop the QA game/launcher and launch the untouched original through its existing
method. Keep the QA directory and evidence until manual acceptance is complete.
