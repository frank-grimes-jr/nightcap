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

No release key is embedded yet. Tests generate ephemeral keys. Trust configuration
must come from the launcher/release trust chain, never a fetched manifest. The
API returns validated metadata only; callers must not treat it as proof of local
files, runtime patches or authority to launch. Rollback and key rotation remain
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
