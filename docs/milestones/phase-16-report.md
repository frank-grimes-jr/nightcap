# Phase 16 — Retain verified client files for launch

Date: 2026-09-15. Candidate branch `feature/client-delivery`, draft PR #52.

## Built

Added a Windows read-sharing lock set and `installer.PrepareLaunch`. Preparation
verifies the cached signed generation, every inventory file, required proxy/config/
catalog, supported executable and original patch sites through retained handles.
Directory pins prevent path replacement; successful preparation returns an owned
lease. Failure and cancellation close all handles. See [ADR 0035](../adr/0035-hold-verified-files-through-client-launch.md).

Shared checkpoint decoding and required-config policy with existing inspection
and installation. The full suite exposed a stale test that searched `dllmain.cpp`
for a size constant moved into the generated header. The repaired test now checks
actual generated size and SHA-256 bytes, rather than a hash comment.

## Verified

- Windows lock tests: concurrent readers, updater exclusion, denied write/rename/
  delete, ancestor/subdirectory rename denial, existing-writer rejection, failure
  cleanup, unsafe paths, root/nested junctions and hard-link mutation denial.
- A disposable copy of the Go test executable starts under the read lock. The
  actual game executable was never launched or modified.
- Twelve signed-generation rejection scenarios, five preflight rejection cases,
  cancellation and post-failure writable-file checks pass. Checkpoint and all
  inventory handles remain protected after successful generation verification.
- Public offline preparation passes against a disposable copy of the supported
  RoF2 executable; user settings remain writable and close releases its lock.
- Full `go test -tags desktop ./... -count=1` and `go vet -tags desktop ./...`
  pass with `NIGHTCAP_TEST_EQGAME` set for executable verification. Subsequent
  test-only additions pass in the installer/launchlock packages. Catalog
  generation check passes for all 22 sites.
- Independent implementation review found no blocking issue.

## Still open

No Play action, client deployment or in-game acceptance is claimed. The lease
must next connect to a signed x86 helper with validated PE entry/export data,
private nonce/health exchange and process/job ownership. All remaining parity,
production signing, self-update, rollback/key rotation and full owner QA from the
[original contract](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md)
remain required. GitHub still reports 14 open issues; none closed in this phase.
