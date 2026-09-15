# Phase 13 - Shared configuration and static client patch preflight

September 15, 2026. Added a canonical catalog shared by launcher preflight and
proxy original-byte guards, strict feature configuration validation, required
manifest-bound preflight assets and a public-install gate under the exclusive
executable handle. The read-only diagnostic exposes the same checks.

## Verification

- 207 Go cases/subtests pass, including the real executable integration test;
  one Windows symlink-privilege test skips, while junction tests run. Vet passes.
- Real RoF2 diagnostic: supported executable, valid configuration, 22 sites
  verified, static preflight valid, `ready_to_play: false`.
- Disabled-equipment configuration: diagnostic exits 2, reports invalid
  configuration and identifies the disabled required feature.
- PE/configuration/manifest tests cover every known required feature disabled,
  missing/duplicate/unknown keys, metadata mismatch, bad executable identity,
  malformed PE/architecture/image base, altered original bytes and unsafe RVA
  mappings. Public installation rejects missing required assets before mutation.
- Shared generator check and existing PowerShell exact-client/source checks pass.
- x86 DLL build and equipment-scope tests pass; Wails Windows launcher builds.
- Independent review found no blockers in bounds, mutation ordering, signed asset
  binding or shared catalog generation.

Local evidence: `artifacts/client-delivery-20260915/go-preflight-tests.jsonl` and
`static-preflight-evidence.json` (diagnostic results and binary hashes).
No new binary/configuration was deployed to the actual game client.

## Remaining scope

The catalog covers the 22 previously recorded sites, not the missing client
capabilities. Runtime configuration consumption, versioned health, startup
blocking on required failure and lifecycle hardening are not implemented by
this phase. The launcher still cannot authorize Play. Native UI QA, production
signing/trust/rollback/rotation/self-update, remaining Skills/trainer/spell/AA/Bard
parity and the full in-game acceptance matrix remain open under the original
production contract. No issue closes from this static verification.

[ADR 0032](../adr/0032-share-client-patch-catalog-and-preflight.md) defines release
paths, input semantics and the generated-data contract. [Launcher guide](../../eq-launcher/README.md)
contains diagnostic commands and current manual QA.
