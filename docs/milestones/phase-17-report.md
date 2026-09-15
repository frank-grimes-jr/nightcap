# Phase 17 — Validate bootstrap PE addresses

Date: 2026-09-15. Candidate branch `feature/client-delivery`, draft PR #52.

## Built

`preflight.BootstrapOpen` reads through retained file handles and rechecks the
compiled executable identity. It returns the executable entry RVA/original byte,
proxy `NightcapInitialize` RVA and proxy image size. `PrepareLaunch` calls it after
signed inventory verification and keeps the metadata as a value copy in the lease.
No preferred-base virtual addresses or UI-supplied offsets enter this boundary.

The accepted image profile is conventional PE32/I386: bounded headers, sections,
image/file sizes and export tables; no deprecated COFF tables; standard aligned
raw/virtual mappings; no overlapping sections. Targets must be raw-backed,
readable/executable, non-writable and non-discardable. The executable may not have
TLS startup callbacks or an existing entry breakpoint. Proxy names are bounded,
strictly sorted and unique; invalid ordinals, missing initializer, forwarders and
out-of-range targets fail closed. Proxy files are capped at 16 MiB and images at
256 MiB. A PE parse is not authentication; proxy trust still comes from the signed
inventory verified first by the installer.

## Verified

- Synthetic tests reject malformed/truncated headers, COFF allocation fields,
  alignment/overlap/section bounds, export tables/names/ordinals/forwarders,
  zero-filled or non-code targets, TLS and unsafe entry bytes.
- Read-only actual binaries produce entry RVA `0x4e3b4a`, original byte `0xe8`,
  initializer RVA `0x4af0` and proxy image size `0x26000`. These match independent
  `pefile` inspection of this candidate build; proxy offsets may change on rebuild.
- Public preparation passes with disposable copies of the supported executable
  and built proxy signed by a generated test key. A signed non-PE proxy is rejected
  and every file lock is released. Returned metadata cannot mutate the lease.
- Full `go test -tags desktop ./... -count=1` and `go vet -tags desktop ./...` pass.
  Both `NIGHTCAP_TEST_EQGAME` and `NIGHTCAP_TEST_PROXY` were set. Designated Windows
  release verification must set both; ordinary tests otherwise skip these cases.
- `go test ./internal/preflight -run '^$' -fuzz '^FuzzBootstrapPE$'
  -fuzztime=30s -parallel=2` passes after 533,913 executions. Fuzz inputs are capped
  at 2 MiB; separate deterministic tests cover the proxy file-size bound.
- Independent review identified missing PE alignment rules in the initial parser.
  Those rules and regression cases were added; final review found no blockers.

## Remaining scope

No game process was started and no installed client was modified. Next: connect
this lease/metadata to the signed x86 helper, private nonce and health exchange,
and owned process/job session lifetime. The launcher still cannot authorize Play.
Remaining client/server parity, production delivery/signing, self-update,
rollback/key rotation and the complete owner acceptance matrix remain required by
[the full specification](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md).

[PE format reference](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
