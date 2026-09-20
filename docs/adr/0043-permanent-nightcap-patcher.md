# ADR 0043: Permanent starter and release-driven game patching

Accepted September 20, 2026: the owner approved automatic checks, patch-before-
Play, signed patch definitions independent of launcher versions, and launcher
self-updates. Preserve the installed game, character settings and update recovery.

## Decision

Ship a stable Windows Nightcap starter and a separately signed desktop launcher
channel. The starter verifies that channel with its compiled production key/host,
downloads only a changed desktop EXE into a content-addressed per-user cache,
and starts the verified version. It does not replace a running executable. The
shortcut remains stable. Launcher metadata has a distinct signed kind and its
own monotonic release counter; game manifests cannot authorize launcher updates.
Show progress/errors, serialize starts and keep existing versions for recovery.

The desktop launcher checks on opening/selecting a client. Play owns one operation
from fresh signed metadata through repair/update and game launch; file, process
and recovery locks remain effective for the whole operation. Network/signature/
installation failures cannot fall through to an outdated or partial game launch.
Unchanged files are verified and reused locally. Interrupted updates recover
before another automatic installation, with cancellation honored between phases.

Production accepts a signed game inventory within compiled, bounded game-asset
path scopes, retaining mandatory proxy/helper/config/catalog entries. Executable,
INI, updater state and unrelated files remain protected. Existing pinned stock
archive retirement remains explicit; broad scopes never authorize deletions.
Dynamic recovery journals retain the signed candidate inventory so an offline
rollback can validate every destination even after metadata expires. Legacy
fixed-inventory QA and its recovery journals remain supported.

Catalog/config bytes must come from the authenticated generation, retain the
pinned base RoF2 executable, validate bounded signatures/features, and pass exact
PE/site checks. The launch lease captures the runtime contract from that catalog;
health must match its schema/version/digest/masks plus process identity and nonce.
The health report never chooses its own expected contract. The signed helper and
proxy continue to perform their own compiled activation checks.

The release packager separates minimum supported launcher protocol from launcher
product version. Content updates use the existing compatible minimum. Changes
to the updater's protocol or trust roots may require a new starter; routine game
and desktop launcher releases do not.

## Slices and evidence

1. `manifest`, `preflight`, `runtimehealth`, `installer`, `session`: signed release
   policy, bounded catalog, exact recovery authority and lease-derived runtime
   checks. Test malicious/expired metadata, protected paths, missing core assets,
   new files, interrupted recovery and mismatched runtime identity.
2. `launcher`, `app.go`, frontend: automatic check and single-operation update-
   then-Play; test fresh/current/changed installs, tampering, cancellation,
   recovery and no launch after errors. Inspect the rendered launcher.
3. Starter/update package, signing/build tooling: independent launcher channel,
   verified version cache/process launch, startup failures and concurrency.
   Test actual Windows version-to-version update and tamper/recovery cases using
   disposable fixture executables, without touching the original EQ client.
4. Build transition launcher/starter, independently review, publish immutable
   files before channels, verify hosted signatures/hashes and preserve rollback.
   Record release evidence, remaining gameplay QA, CHANGES and phase report.

## Sources

- [Windows CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw): use an explicit executable path and retained process handles.
- [Go os](https://pkg.go.dev/os): rooted file operations and filesystem semantics.
- Existing Nightcap signed staging, file leases and recovery are the implementation
  baseline; this change must preserve their regression tests.
