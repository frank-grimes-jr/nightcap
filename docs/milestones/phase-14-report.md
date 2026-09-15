# Phase 14 - Synchronous proxy activation and process-bound health

September 15, 2026. Development candidate for #10/#14/#15; not deployed.

## Built

- Strict bounded runtime configuration consumption and generated feature identities.
- Pinned, serialized first-export initialization; required failure stops the process.
- Checked patch writes/cache flush/protection restoration; optional MQ2 survey off
  by default, running only after required patches succeed.
- Atomic process-specific health/log files and Go validation against trusted launch
  identity, signed config hash and compiled proxy/catalog requirements.
- Disposable native hosts and cross-language regression tests.

## Verification

- x86 proxy, four native test programs and the Wails Windows launcher build.
- Existing equipment item/thread/class-bit/nesting regression tests pass.
- 21 real-memory patch-writer cases pass across 5/6/16-byte sites: success,
  failed protection acquisition/restoration, failed cache flush, foreign replacement,
  changed precondition and unreadable memory. Page protections and bytes are checked.
- Seven disposable-host cases terminate with the required failure exit code and
  failed health: missing/disabled/unknown/oversize configuration, unsupported host,
  valid nonce and invalid nonce. Unicode/spaced paths and a different cwd pass.
- Load/unload before forwarding does not initialize; DllCanUnloadNow returns S_FALSE.
- Health replacement succeeds; occupied temp and directory-at-target failures
  preserve existing paths and do not leave a partial target/temp file.
- Full Go package suite and vet pass. Native C++/Go config differential and actual
  supported-executable preflight run; native health output passes the Go validator.
- The 22-site exact-client verifier and generated-catalog drift check pass.

Commands from the repository root:

```powershell
./eq-client-dll/build.bat
./eq-client-dll/tests/build-runtime-tests.bat
python eq-client-dll/tests/test_runtime.py
python tools/generate-client-patch-catalog.py --check
./eq-client-dll/tests/verify-exact-client-patch-sites.ps1 -EqgamePath 'path/to/eqgame.exe'
```

For Go tests, set NIGHTCAP_CPP_CONFIG_TEST and NIGHTCAP_CPP_HEALTH_TEST to the
built runtime-config.exe/runtime-health.exe, and NIGHTCAP_TEST_EQGAME to the
supported executable. Run `go test ./...` and `go vet ./...` in eq-launcher.
Absent native-test paths skip those optional integration cases.

Independent lifecycle and patch-writer review found no new blockers; the startup
ordering release gate below remains open. Local evidence includes
`artifacts/client-delivery-20260915/go-runtime-tests.jsonl`,
`runtime-build-hashes.json` and `input-startup-trace.txt`.

## Remaining and uncertain

The first DirectInput call follows login/server-selection setup. It has not yet
been proved to precede every affected character window or eligibility path.
[ADR 0033](../adr/0033-bind-proxy-health-to-client-process.md) records the exact
addresses and the required next trace. No real game was launched or patched.

The launcher still needs actual process creation, a fresh nonce, retained process
identity and bounded health waiting. Play remains disabled. Native launcher UI
acceptance, production trust/distribution/rotation/rollback/self-update, all
remaining client parity and the complete class/slot QA matrix are still required.
No issue is resolved by these runtime mechanics alone.
