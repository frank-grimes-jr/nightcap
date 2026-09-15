# Phase 20 — Connect verified sessions to the launcher

Date: 2026-09-15. Candidate branch `feature/client-delivery`, draft PR #52.

## Built

The Wails Play action now calls the verified session backend. The controller owns
its busy state throughout startup, gameplay and cleanup, excluding another Play,
updates, recovery and folder changes. A separate Cancel call remains available
while the Play promise is pending. After startup it becomes Stop game; cancellation
waits for confirmed session cleanup, and cleanup errors remain visible.

Folder selection inspects the cached signed generation without network access.
A valid cached generation remains a launch candidate when checking the release
service fails. Every Play refreshes trust time and calls the full signed/preflight/
runtime verifier again; the UI's CanPlay field only offers an attempt. Required
helper/proxy/config/catalog inventory, usable release keys and a compiled EnablePlay
switch gate dispatch. DefaultPolicy keeps the switch off and has no release keys.

The UI presents starting, running, stopping and stopped states, preserves access
to Stop while Play is pending, and explains that the launcher must stay open while
the game runs. Closing the window during an operation requests cancellation and
vetoes that close. After cleanup the user closes the window again. This retains
the existing close behavior and avoids abandoning an owned running process.

## Verified

- Controller tests cover disabled/incomplete/expired policy, fresh offline trust,
  cached candidate discovery, recovery and failed new-folder inspection, conflicting
  actions, cancellation during startup and exactly as startup returns, immediate
  success/abnormal exit, cleanup ownership and cleanup error reporting.
- Full desktop Go tests and vet pass, including the native session tests with
  disposable fixtures and read-only supported-client preparation.
- Frontend typecheck/build passes. Seven isolated Chrome tests pass, including
  Play pending while Stop is callable, blocked folder/update/second-Play actions,
  return to idle, default launch-disabled preview and existing UI regressions.
  The running-session screenshot was inspected. Browser tests use a test-only
  native bridge; they do not launch the actual game or prove Wails runtime behavior.
- The Windows amd64 Wails executable builds with regenerated Play binding.
  Dependency tidy records the already-pinned x/sys version as a direct dependency;
  no dependency version changed.
- Independent controller, policy, native bridge and UI review found no blocker.

## Remaining gates

The built preview remains unsigned and launch-disabled. Provision a trusted
candidate release and complete native Wails and supported-game startup acceptance
before enabling it for players. Production signing, key rotation, signed rollback,
self-update, remaining full multiclass parity and owner in-game acceptance remain
open. No live client deployment, issue closure or gameplay promotion occurs here.

[Session ownership](phase-19-report.md) ·
[Full contract](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md).
