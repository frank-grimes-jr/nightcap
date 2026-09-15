# Phase 18 — Native helper protocol and session containment

Date: 2026-09-15. Candidate branch `feature/client-delivery`, draft PR #52.

## Built

Added an x86 helper around the proven entry gate. It consumes a bounded binary
request on private inherited pipes, uses explicit inherited executable/proxy and
parent handles, snapshots a private nonce environment, and asks its parent for
health approval before resuming the client. It retains process/job ownership
until observed game exit. A watchdog terminates the helper and its owned client
on parent loss or post-start stdin closure. Normal teardown joins the watcher
before releasing its process handle.

The [protocol/ownership contract](../../eq-client-dll/bootstrap/README.md) records
wire layouts, pipe capacity, timeout, parent-process rights, inherited-handle
allowlist and required Go health validation. These are requirements for the next
integration; this helper does not authenticate a downloaded release by itself.

## Verified

- The helper and fixtures build x86 with MSVC `/W4 /WX`, ASLR/NX and asInvoker.
- Seventeen native scenarios pass: success, fragmented input, rejection, invalid
  approval, missing approval, startup EOF, initializer failure/hang/exception,
  actual candidate proxy rejection, malformed/truncated requests, missing/bad
  nonce, parent crash before/after approval and post-start channel closure.
- Tests verify PID plus actual process-creation time, nonce propagation, absence
  of fixture main before approval, matching Started/Exited identities, observed
  exit codes and owned-child termination. A running fixture remains alive after
  Started until parent loss or cancellation, exercising retained job ownership.
- The actual DLL rejects the unsupported fixture before main and leaves matching
  failure health. No installed game executable was launched or modified.
- Independent implementation and final watchdog/test review found no blocker.
  Review prompted explicit parent-handle cleanup and documentation that teardown
  must close stdin or kill the helper; closing stdout alone does not cancel.

## Still open

The built helper is unsigned and not yet bound into a required signed inventory
or called by Go/Wails. Next: implement the Go owner with the explicit inherited
handle list, protocol state machine, real process-bound health validation,
cancellation and lease lifetime. Play remains disabled. The original full parity,
production signing/self-update/rollback and owner acceptance contract remains open.
