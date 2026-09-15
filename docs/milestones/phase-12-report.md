# Phase 12 - Windows launcher shell and native release controller

September 15, 2026. Implemented the Wails/Vue shell and serialized native release
controller for #14/#15. The UI selects a client folder, reports inventory and
installed/available release IDs, invokes update/repair/recovery, cancels pending
work and shows up to 40 session events. Native policy supplies trust and URLs;
UI calls cannot replace them. Update repeats executable, checkpoint, signature,
expiry and file checks before staging/installing. The installer repeats its own
verification under the existing exclusive guard. Play remains disabled.

Local installed-generation inspection verifies signed active metadata, current
files and tombstones. Pending or corrupt recovery markers prevent updates.
An expired active signature is reported while preserving the local checkpoint,
so a fresh trusted repair can proceed without authorizing a downgrade.

## Verified

- `go test ./...`: 162 passing cases/subtests, no failures. The symlink-privilege
  test still skips on this Windows host; native junction tests execute.
- `go vet ./...`, `go test -tags desktop ./...`, `go vet -tags desktop ./...`: pass.
- `npm run build`: Vue type checking and Vite production assets pass.
- `wails build -tags desktop`: Windows amd64 executable and native bindings build.
- Six Playwright tests pass in isolated Chrome profiles: preview gates, inventory
  and update, cancellation with an unresolved native promise, recovery, escaped
  native error text/keyboard controls and narrow-screen overflow.
- Browser screenshots inspected. Update, recovery and Play tests use an injected
  bridge fixture; no fake bridge is included in production assets.
- Independent controller and native bridge/frontend reviews: no blockers.
- `npm audit`: zero reported vulnerabilities at capture time.

Local evidence: `artifacts/client-delivery-20260915/go-launcher-tests.jsonl`,
`launcher-ui-tests.json`, `launcher-update.png`, `launcher-preview.png`,
`launcher-narrow.png` and `launcher-build.json`. Binary is an unsigned preview.
The actual RoF2 client directory was not updated.

## What remains unverified or unfinished

The native interaction smoke test did not complete. The default WebView loader
strips debug environment arguments; Windows UI Automation did not find the hidden
test window. Both attempts used an isolated app-data directory and a disposable
copy of the executable; task-owned processes were closed. Native folder-dialog,
window, bridge interaction and second-instance acceptance remain manual gates.
A successful compile is not evidence of completed native or in-game acceptance.

No production key/channel is provisioned. Required configuration semantics,
patch metadata and runtime health, guarded Play/offline Play, signed rollback,
key rotation, Authenticode, launcher self-update, log/backup retention and the
remaining RoF2 equipment/Skills/trainers/spell/AA/Bard parity are still required.
The full approved production spec and fresh owner in-game acceptance remain the
completion standard. No issue is closed by this phase.

Build and exact preview QA: [launcher README](../../eq-launcher/README.md).
