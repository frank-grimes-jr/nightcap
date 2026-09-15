# Phase 19 — Go ownership of native client sessions

Date: 2026-09-15. Candidate branch `feature/client-delivery`, draft PR #52.

## Built

`session.Start` prepares the complete cached signed generation and retains its
launch lease through helper/client termination. Preparation now requires
`nightcap-bootstrap.exe` in the signed inventory, checks its x86 PE executable
shape and pins it alongside the proxy, configuration and every managed asset.

The Go owner mints a private nonce, passes an explicit inherited-handle list and
uses the native bounded pipe protocol. It retains the reported child's actual
process handle, verifies creation time and complete configuration-bound health,
then acknowledges initialization before the native helper resumes main. Started,
Exited and failure messages must obey sequence and identity constraints. Exit
status is checked against the retained process handle and terminal EOF is required.

An outer kill-on-close Windows job contains the helper before any request is sent.
Its descendants include the native helper's nested child job. This covers cleanup
when the helper fails before reporting a child PID. Startup context cancellation
stops preparation/startup; after success, `Session.Close` owns cancellation.
Concurrent Close/Wait are supported. File locks remain held until helper exit,
zero active job processes and any retained child's exit are confirmed. A caller's
cleanup timeout does not abandon ownership or release live files.

## Verification

- Full desktop Go package tests pass with supported-executable, candidate proxy
  and helper paths supplied. Supported-game files are read or copied for offline
  preparation only; the installed game is never run or modified.
- Native Go sessions use a disposable fixture executable and fixture proxy that
  emits health. Success, private nonce propagation, malformed/stale/incomplete
  health, initializer failure/hang/crash, startup cancellation before a child PID,
  retained locks, concurrent Close and startup-context detachment pass.
- Regression tests reject Started/Exited before HealthRequired and malformed wire
  data; helper inventory cannot be omitted or optional. Helper PE checks reject
  DLL/truncated images without closing borrowed handles.
- A helper that remains alive after terminal EOF is terminated before Wait;
  a real owned subprocess verifies this deadline behavior.
- Review found Close could hide a lease-release error joined with requested stop.
  The new regression failed before the fix and passes afterward. Clean stop is
  normalized separately; unexpected helper and resource-close errors are retained.
  A native session test injects lease-close failure and verifies it is reported.
- The native helper regression suite passes all 17 scenarios (four test methods).
  Fixture health publication links bcrypt; fixtures build with MSVC `/W4 /WX`.
- Go desktop vet and diff whitespace checks pass. Independent review covers
  ownership, error propagation, protocol state and cleanup.

## Remaining gates

This is backend integration; the Wails controller does not yet call Start and
Play remains disabled. No production key/channel or Authenticode signing has
been provisioned. Test signatures and fixture health do not establish supported
client acceptance. The full remaining spell/equipment/Skills/trainer/AA/Bard
parity, supported-game startup proof, signed rollback/key rotation/self-update,
launcher native QA and owner in-game acceptance remain open. No issue is closed
and no live client binary is deployed by this phase.

[Ownership decision](../adr/0036-own-bootstrap-session-in-go.md) ·
[Complete goal](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md).
