# ADR 0033: Bind proxy initialization health to the launched process

Date: 2026-09-15. Status: implemented development candidate; startup ordering
and production launch acceptance remain open. Epic #10; delivery #14/#15.

## Problem and decision

The old proxy started a background thread from DllMain and immediately forwarded
DirectInput calls. Patches could race client startup, and failed helpers did not
prevent play. A successful installer/static check alone could not prove that the
running process had applied its required patches.

Keep DllMain empty. The first forwarded export executes initialization through
Windows InitOnce; concurrent callers wait. Pin the proxy before reading config
or writing hooks. Reject recursive initialization and never return from required
failure: publish failed health when possible, terminate this process, and use
fail-fast if termination unexpectedly returns. DllCanUnloadNow returns S_FALSE.
The static CRT and thread-local equipment scope retain thread notifications.

Resolve config and logs relative to the pinned module using Unicode paths;
require the executable in the same directory. Read a bounded regular config
handle, rejecting file reparse points. Match the exact executable size/SHA and
resolve all six exports from an absolute System32 dinput8.dll before patching.
Every required feature must succeed. Existing caster/mana writers now reject
foreign/prepatched bytes and check write verification, instruction-cache flush
and restored protection; other patch helpers propagate cache failures too.
Failed patch writes terminate startup even if best-effort rollback fails.

The optional MQ2 offset survey defaults off. If requested it starts only after
required patches succeed, through _beginthreadex; its handle is closed. The pinned
proxy and log remain valid until process exit. Survey failure does not disable
required gameplay hooks and is reflected in the report.

## Process-bound protocol

Generated `runtime_contract.h` and the Go embedded catalog define runtime schema
1, proxy version, catalog SHA-256, feature names and the nine-bit required mask.
The DLL publishes `nightcap_health_<PID>.json` using CREATE_NEW for a private temp
name, exact write, FlushFileBuffers and atomic replace. A collision or failed
write/rename prevents readiness. Logs use `nightcap_dll_<PID>_<FILETIME>.log` and
allow shared readers without overwriting an existing log.

Canonical compact JSON contains, in order: schema, proxy_version,
catalog_sha256, config_sha256, pid, process_created (quoted decimal FILETIME),
nonce, state, required_mask, enabled_mask, applied_mask, mq2_survey and reason.
States are initializing, ready and failed. A ready report requires every required
bit and no failure reason. `NIGHTCAP_LAUNCH_NONCE` is a 32-character lowercase hex
launch nonce. Direct/manual launches may omit it for diagnostics; those reports
cannot pass the launcher's validator.

Go validation rejects stale PID/creation-time/nonce, config or compiled identity
mismatch, unknown/missing/duplicate JSON fields, noncanonical encoding, incomplete
or extra mask bits, and every state except ready. Expected values must come from
the actual process handle, a cryptographic launch nonce and the verified signed
manifest. They must never be taken from the report itself. This is process binding
within the existing local-user trust boundary, not attestation against a malicious
same-user process or administrator.

## Startup timing remains a release gate

Read-only disassembly of the exact supported executable found:

- `0x005FF971` calls input initialization at `0x005FEE00`.
- `0x005FEE62` calls `0x0079987C`, which jumps through DirectInput8Create IAT
  entry `0x009C0028` (the only dinput8 import in this executable).
- The enclosing startup path logs the server-selection format at `0x005FF7D6`
  and handles login strings before this input call.

This evidence does **not** establish initialization before login or before all
parity-sensitive window/eligibility code. Trace those constructors and first
consumers before relying on this bootstrap for production, or add a verified
earlier bootstrap. The launcher process/nonce/health handshake is still to be
implemented. Play remains disabled. No actual eqgame process was started or
modified for these tests.

## Alternatives and limits

Retaining background patching leaves the race intact. Heavy initialization in
DllMain runs under the loader lock. Synchronous first-export initialization avoids
those hazards but still needs the ordering proof above. No hot-unload support is
provided because installed hooks and callbacks retain proxy addresses.

This report covers the current nine features, not missing Skills/trainer/spell/AA/
Bard parity. Signed production distribution, rotation/authorized rollback,
Authenticode/self-update, full class/slot in-game QA and owner acceptance remain
required by the original production contract.

## Verification and sources

[Phase 14](../milestones/phase-14-report.md) records native failure injection,
disposable processes, C++/Go agreement and build results.

Microsoft documents [loader-lock constraints](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-best-practices),
[InitOnce retry semantics](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-initonceexecuteonce),
[module pinning](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulehandleexw)
and [DllMain/CRT restrictions](https://learn.microsoft.com/en-us/windows/win32/dlls/dllmain).
