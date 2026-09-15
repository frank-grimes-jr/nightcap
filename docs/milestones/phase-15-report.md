# Phase 15 - Pre-entrypoint proxy bootstrap

September 15, 2026. Native development primitive for #10/#14/#15; not deployed.

## Outcome

An owned child can finish imported-DLL initialization before its executable entry
code runs. The successful fixture uses the DLL CRT and loads another Windows DLL;
its main marker appears only after health approval and explicit resume. The real
candidate proxy rejects an unsupported fixture executable before its main marker,
with process-bound failed health. This provides a testable earlier launch path
than the post-login DirectInput hook.

Implemented a checked one-byte entry breakpoint, remote PE/file identity checks,
child-relative initializer RVA, primary-thread suspension, bounded event handling,
health approval callback, checked termination/drain, and move-only process/job
ownership. Added the proxy's explicit initializer export, preserving original
DirectInput ordinals and advancing its compiled version to 0.3.0-dev.

## Verification

- x86 candidate DLL and bootstrap fixtures compile with the existing MSVC toolchain.
  The Wails Windows launcher rebuilds against the updated runtime catalog.
- Eleven bootstrap scenarios pass: success, five consecutive sessions, initializer
  error, timeout, exception, rejected health, wrong entry RVA, wrong original byte,
  wrong proxy identity, bootstrap-owner crash and actual candidate rejection.
- Failures never create the executable main marker. Owner-crash checks query the
  exact child PID/creation time and confirm termination. No arbitrary process kill
  or live eqgame launch is used.
- After one-time Windows debugger setup, handle counts remain 79 -> 79 across four
  further successful sessions in the same parent (initial count 72 -> 79).
- Existing runtime suite passes: 21 patch-writer fault cases, seven disposable
  fail-closed hosts, unload-before-forwarding and atomic health/collision checks.
- Shared-catalog drift and all 22 exact-client patch-site checks pass.
- Full Go package tests/vet pass with rebuilt native config/health fixtures and
  the real-executable read-only preflight. Original export ordinals 1-6 and new
  initializer ordinal 7 are verified with dumpbin.
- Independent entry-gate review found and prompted fixes for continuation after
  unconfirmed termination and a fallible operation after main-thread resume.
  Final bounded review found no remaining blocker in that primitive.

Commands from the repository root:

```powershell
./eq-client-dll/build.bat
./eq-client-dll/tests/build-bootstrap-tests.bat
python eq-client-dll/tests/test_bootstrap.py
./eq-client-dll/tests/build-runtime-tests.bat
python eq-client-dll/tests/test_runtime.py
python tools/generate-client-patch-catalog.py --check
```

Local research evidence: `artifacts/client-delivery-20260915/bootstrap-probe-results.json`
(the failed initial-system-breakpoint experiment), `bootstrap-entry-results.json`
(the subsequent entrypoint experiment) and `bootstrap-repeat.txt` (handle plateau).
The checked-in tests are the reproducible acceptance evidence for the final code.

## Not complete

No real game was started or modified. The production x86 bootstrap executable,
signed-generation read locks/PE export validation, private nonce/Go health IPC,
helper-to-launcher session ownership and cancel handling are next. Callback deadline
behavior and Windows API cleanup fallback still need integrated fault coverage.
The native mechanism must pass supported-RoF2/MQ2 and full in-game acceptance.

Play remains disabled. Production signing/distribution/rotation/rollback/self-update,
remaining multiclass client parity and the original all-class/held-slot QA contract
remain required. No issue closes from the fixture result alone.

[ADR 0034](../adr/0034-initialize-proxy-before-client-entry.md) records the decision,
trusted-input boundary, exact-client entry metadata and source documentation.
