# Nightcap launcher development preview

Development implementation for issues #14/#15 and the full client-parity goal.
The Wails/Vue shell and guarded installer/controller are implemented. The
production release pipeline and remaining parity hooks are still being built.
This is not a production launcher release.

## Implemented

- Wails Windows shell: folder selection, inventory, update/repair, recovery,
  verified Play/Stop wiring, cancellation and session activity, backed by a
  serialized Go controller. Default release policy keeps Play disabled.
- Fresh signature/file verification for every update; no UI-supplied trust.
- Read-only local active-generation/checkpoint and pending-recovery inspection.
- Required signed configuration/catalog and exact PE patch-site preflight before
  public installation, sharing original-byte constants with the proxy.
- Ed25519 verification of compact, schema-specific canonical manifest bytes.
- Key validity, manifest expiry, launcher version and monotonic release checks.
- Exact trusted inventory, required flags, bounded sizes and lowercase SHA256.
- Strict Windows relative paths, owned tombstones and allowlisted HTTPS hosts.
- Read-only exact RoF2 executable identification, shared with the proxy guard.
- Signed local inventory diff by size/SHA256 with nonregular/link rejection.
- Complete private staging: rehash local copies, download changed/missing files,
  verify HTTPS redirects, bound streams and preserve signed metadata.
- Physical staging/client separation (including Windows junction aliases), final
  completion marker and explicit failed-cleanup reporting.
- Windows process/executable guard that excludes launch and concurrent updates.
- Journaled asset installation, full rollback/restart recovery, tombstones and
  same-release repair with a durable local release/digest checkpoint.

No release key is embedded yet. Tests generate ephemeral keys. Trust configuration
must come from the launcher/release trust chain, never a fetched manifest. The manifest
API returns validated metadata only. Asset inspection/staging adds file evidence,
not runtime patch health or authority to launch. Rollback and key rotation remain
separate signed protocols to implement; an ordinary downgrade fails closed.

## Build and tests

Run from `eq-launcher/` with Go 1.26 or later:

```powershell
go test ./...
go vet ./...
go build -trimpath -o build/nightcap-check.exe ./cmd/nightcap-check
./build/nightcap-check.exe -client 'path/to/eqgame.exe'
```

The diagnostic reads the executable without writing or loading it. Success
means the supported executable was identified. The diagnostic does not create
a session or grant Play; `ready_to_play` remains false.
Unsupported executables exit 2; I/O failures exit 1.

[Full development plan](../docs/ops/client-delivery-plan.md) and
[approved acceptance contract](../docs/superpowers/specs/2026-07-28-true-multiclass-production-spec.md).

## Staging boundary

`internal/assets.Inspect` and `Stage` accept raw signed metadata plus caller-owned
trust and verify before disk access. Stage requires an existing trusted staging
parent outside the client tree. It builds a complete random release directory:
`files/`, original `manifest.json`, `signature.json`, and final `complete.json`.
Current local files are copied and hashed again, so staging contains a complete
candidate even when only changed files use the network. Tombstones are planned
but not applied. Unknown user files are not inventory targets.

The completion marker is a discovery aid, not a trust credential. The installer
reverifies signatures/content under its exclusive executable guard before use.
Failures remove the new candidate; cleanup errors are joined with the original
error and an orphan can remain. Abrupt interruption may also leave an incomplete
candidate. The installer implements journaled asset recovery; orphan retention
management remains unfinished.
This package never marks a client generation active or grants Play. Test transport
injection is private; production Stage uses normal TLS verification and per-hop
host checks. Cached-current staging avoids downloads, but trusted offline Play
still requires the full active-generation and runtime health implementation.

## Installation and recovery boundary

`internal/installer.Install` accepts the client path, complete candidate path and
caller-owned trust. `Recover` needs only the client path and trusted ownership
inventory. Both use the native Windows game/update guard and require the exact
supported executable. The guard requests write access for exclusion without
writing executable bytes. Failed/unsupported preflight performs no installation.

Pending recovery blocks a new update. Immutable backups and a bounded canonical
journal restore all affected files and the previous active record on failure or
restart. A corrupt journal/backup fails closed with pending retained. The full
prior generation is checked before recovery completes. Backups and pre-journal
orphans remain retained; cleanup/retention management still needs implementation.

The installed record captures verified bytes and local release identity. It is
not a Play authorization: the session backend must repeat configuration, patch
metadata and runtime-health checks. Release key provisioning/rotation, signed
rollback, Authenticode and self-update remain unfinished. The checkpoint uses the
local user's filesystem trust boundary; it is not protected from that user/admin
rewriting local state. Tests prove process-exit recovery, not sudden power-loss
or preservation of arbitrary Windows ACL/alternate-stream metadata.

[Transaction protocol](../docs/adr/0031-journal-client-generation-recovery.md)
and [native guard](../docs/adr/0030-exclude-game-launch-during-client-update.md).

## Desktop preview

Use Node 22.12+ (verified with 24.17), Go 1.26+ (verified with 1.27.1),
Wails CLI 2.16.0 and Windows WebView2. From `eq-launcher/`:

```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@v2.16.0
Push-Location frontend
npm ci
npm run build
npm test
Pop-Location
wails build -tags desktop
go test -tags desktop ./...
go vet -tags desktop ./...
```

Build the frontend before the first Wails build: binding generation compiles the
embedded `frontend/dist` before Wails runs its frontend build step. `main.go` and
`app.go` include both `desktop` and `bindings` build modes because Wails removes
its `desktop` tag when generating bindings. Output: `build/bin/nightcap-launcher.exe`.
The executable is an unsigned development preview, not a production release.

TypeScript is pinned to 6.0.3: vue-tsc 3.3.11 cannot load TypeScript 7's removed
`typescript/lib/tsc` entry point. The frontend lockfile is committed. Playwright
uses an installed Chrome in fresh temporary profiles, never an existing profile.
Browser-only preview disables all native operations. Tests inject a native bridge
fixture before loading the real UI; fixtures are not bundled in the product.

The native controller owns release policy. This build has no production release
keys/endpoints, so it can remember a client folder and identify the supported
executable, but cannot install or authorize Play. Settings live in
`%APPDATA%/NightcapLauncher/settings.json`; activity shows this session only.
Configured-policy fixture tests exercise signed check/stage/install/recovery.
Update always repeats verification rather than trusting an earlier UI snapshot.
Closing during an operation requests cancellation and keeps the window open
until that operation/rollback ends. Recovery itself runs to completion.

### Native manual QA still required

1. Start the built preview, choose a disposable copy of the supported RoF2 folder,
   and check it: supported-client message, no install action, Play disabled.
2. Restart: the chosen folder persists. Change to an unsupported executable and
   verify the error, then select the supported folder again.
3. Verify native folder-dialog cancellation, keyboard navigation, resize, Activity,
   player-guide link and second-instance focus. No client files should change.
4. Once a real signed channel is provisioned, verify updates, cancellation,
   running-game refusal, interrupted-install recovery and all required health gates.
   Browser fixture results do not constitute that release acceptance.

The September 15 default-loader native smoke attempt created a task-owned profile
but did not complete: Wails strips WebView debugging environment arguments, and
Windows UI Automation did not expose the hidden test window. No native interaction
pass is claimed. [Evidence and remaining work](../docs/milestones/phase-12-report.md).

## Required configuration and static patch preflight

Before `Install` can write a generation, its verified manifest must include
`nightcap-patches.cfg` and `nightcap-patch-sites.json` with `required: true` and
matching size/hash. Assemble them from `eq-client-dll/config/nightcap-patches.cfg`
and `eq-client-dll/config/patch-sites.json` respectively. The catalog must match
this launcher's embedded version. Required feature keys must all be explicitly
`1`; optional `mq2_survey` may be `0` or `1`. Missing/duplicate/unknown keys fail.
The candidate DLL consumes these configuration keys and emits process-bound
health; the launcher validator rejects stale or incomplete reports. The Go session owner now performs process/nonce/health orchestration and Wails
dispatches it. Production release policy and supported-game startup-order proof
remain unfinished.
[Runtime protocol and limits](../docs/adr/0033-bind-proxy-health-to-client-process.md).

Generate/check shared inputs from the repository root:

```powershell
python tools/generate-client-patch-catalog.py --check
```

Read-only diagnostic, after building `nightcap-check`, from `eq-launcher/`:

```powershell
./build/nightcap-check.exe -client 'path/to/eqgame.exe' `
  -config ../eq-client-dll/config/nightcap-patches.cfg `
  -catalog ../eq-client-dll/config/patch-sites.json
```

A pass reports `configuration_valid: true`, `sites_verified: 22` and
`static_preflight_valid: true`. `ready_to_play` remains false: installed-generation
integrity, required runtime health and full parity are separate gates. These are
the currently recorded sites, not proof that the remaining client gates exist.
Set `NIGHTCAP_TEST_EQGAME` to the supported executable path when running Go tests
to include the read-only real-executable integration case; otherwise it skips.
[Design and limits](../docs/adr/0032-share-client-patch-catalog-and-preflight.md).

### Startup timing integration

The native x86 entrypoint gate now passes disposable-process tests, including the
actual candidate DLL rejecting an unsupported host before main. The Go session
backend now joins this helper to the verified lease and process-bound health.
Wails Play/Stop integration is implemented; native Wails and supported-game
acceptance remain open.
[Bootstrap contract](../docs/adr/0034-initialize-proxy-before-client-entry.md).

### Offline launch preparation

`installer.PrepareLaunch(ctx, directory, trust)` returns an owned `LaunchLease`
after checking cached signature/expiry/release floor, all managed files, required
config/catalog/proxy/helper, exact executable and patch sites. Retained Windows handles
allow reads/execution but block writes, replacement and ancestor renames. Keep
the lease alive for the entire game session; close on failure or session end.
User settings remain writable. UNC/reparse paths are rejected.

The lease also exposes validated PE entry/initializer RVAs and image size. The
proxy must be a conventional aligned PE32 DLL with a direct, unique initializer
in persistent read-only executable code; malformed or forwarded exports fail.
Files are bounded to 16 MiB for the proxy and 256 MiB for the loaded image.

This is a backend preparation boundary, not an enabled Play path. Set
`NIGHTCAP_TEST_EQGAME`, `NIGHTCAP_TEST_PROXY` and `NIGHTCAP_TEST_HELPER` for
the actual-image Go tests;
they read the originals and prepare disposable copies without launching the game.
[Contract and limits](../docs/adr/0035-hold-verified-files-through-client-launch.md).

### Owned session backend

`session.Start(ctx, directory, trust)` prepares the signed generation, starts its
required `nightcap-bootstrap.exe`, supplies explicit inherited handles and a fresh
private nonce, and validates actual child identity/health before approval.
Start's context controls startup only. The returned Session supplies Identity,
Done, Wait(ctx) and concurrent/idempotent Close(ctx). Close cancels the owned
session; a caller timeout leaves cleanup and verified file locks retained.
An outer Windows job covers even helper death before the child PID is known.
All owned processes must exit before the lease closes. Unexpected cleanup errors
are reported; a clean requested stop succeeds.

Build `eq-client-dll/tests/build-helper-tests.bat` before native session tests.
`NIGHTCAP_TEST_HELPER` points to the built helper with sibling test fixtures;
those tests execute disposable fixtures only. Public Start still requires the
exact supported game identity and signed generation. The Wails controller now dispatches this backend while retaining busy state until
cleanup finishes; production release policy and supported-game acceptance remain
open. [Wire contract](../eq-client-dll/bootstrap/README.md),
[ownership decision](../docs/adr/0036-own-bootstrap-session-in-go.md) and
[evidence](../docs/milestones/phase-19-report.md).

## Play/Stop candidate and native QA

`Policy.EnablePlay` is compiled release policy; the UI cannot set it. It defaults
to false. Enabling a trusted candidate also requires usable keys, configured
channel and required helper/proxy/config/catalog inventory. Cached local inspection
only offers a launch attempt; every Play rechecks signature, expiry, release floor,
files, executable and actual process-bound health. Play itself needs no network.
A failed release-service check can leave a valid cached candidate available.

While Play is pending, Stop game stays available and all conflicting actions stay
disabled. Keep the launcher open during gameplay. Closing its window during an
operation requests cancellation and vetoes that close; after cleanup, close the
window again. Cleanup errors appear in status/activity. Unconfirmed process
termination keeps the launcher busy and its verified files locked.

After a trusted candidate is provisioned, native acceptance must verify:

1. Current signed cached release launches with the network unavailable; changed,
   expired, missing-helper or pending-recovery installations fail before gameplay.
2. Starting, running and stopping states match actual process lifetime. Cancel
   during startup and Stop during play terminate only the owned game session.
3. Update, recovery, folder changes and a second Play remain blocked until cleanup
   completes. Natural exit returns to idle, abnormal exit is reported.
4. Closing during play requests shutdown; cleanup completes before another close
   exits the launcher. Test the real Wails bridge/window, not just browser fixtures.
5. Run the complete client-parity in-game matrix and preserve its acceptance gates.

[Integration evidence](../docs/milestones/phase-20-report.md). No production key or
new client deployment is introduced by this preview.
