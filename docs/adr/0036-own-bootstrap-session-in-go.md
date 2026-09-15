# ADR 0036 — Own the bootstrap session in Go

Date: 2026-09-15. Status: candidate implementation in draft PR #52.

## Context

A verified launch lease and native entry gate are insufficient unless one owner
retains files, helper and game through health approval and complete termination.
The helper may fail before Go receives a child PID. Binding its lifetime directly
to a request context would also kill a healthy session when that request ends.

## Decision

`internal/session.Start` consumes a prepared lease and starts the signed-inventory
helper with `exec.Command`, private pipes/environment and explicit inherited
handles. It assigns an outer kill-on-close Windows job before sending the request;
the signed helper cannot create a child before receiving that request. Native
child containment nests under that job; neither level permits breakaway.

A single goroutine owns protocol reads, health approval, process handles and
`cmd.Wait`. Health must match the actual child's creation time, fresh nonce,
signed configuration and compiled catalog/mask. The retained handle is used for
exit verification rather than reopening the PID. The public API accepts trusted
release policy, never helper addresses or an arbitrary existing process.

Startup context applies until Started. The returned session supplies Identity,
Done, Wait(ctx) and idempotent Close(ctx). Closing requests termination; timing
out a caller does not stop cleanup. EOF is not process termination: the owner
waits on the retained helper handle, terminating it if it remains alive, before
calling Wait. It then requires zero active job processes and child termination
before releasing the lease. If termination cannot be confirmed, ownership and
locks stay retained. Clean cancellation does not hide resource-close errors.

## Limits and validation

Windows job containment is a lifecycle guarantee, not a sandbox against a
malicious signed helper or privileged local user. Cached signatures retain their
expiry checks; future offline policy still needs production configuration.
Wails controller integration and supported-game startup acceptance remain open.
Tests run only owned disposable executable/proxy fixtures and offline copies.
[Verification and remaining contract](../milestones/phase-19-report.md).
