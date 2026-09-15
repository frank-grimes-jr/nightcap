# Nightcap launcher core

Development implementation for issues #14/#15 and the full client-parity goal.
The player-facing Wails application, installer, release pipeline and new parity
hooks are still being built. This is not a production launcher release.

## Implemented

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
means the supported executable was identified; `ready_to_play` remains false
until installed-generation and required runtime-patch checks are implemented.
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

The completion marker is a discovery aid, not a trust credential. The future
installer must reverify signatures/content under its process lock before use.
Failures remove the new candidate; cleanup errors are joined with the original
error and an orphan can remain. Abrupt interruption may also leave an incomplete
candidate. Journaled activation/recovery and orphan management are not implemented.
This package never marks a client generation active or grants Play. Test transport
injection is private; production Stage uses normal TLS verification and per-hop
host checks. Cached-current staging avoids downloads, but trusted offline Play
still requires the full active-generation and runtime health implementation.
