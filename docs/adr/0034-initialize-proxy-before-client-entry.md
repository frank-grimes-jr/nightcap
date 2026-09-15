# ADR 0034: Initialize the proxy before the executable entrypoint

Date: 2026-09-15. Status: tested native bootstrap primitive; launcher integration
and supported-game acceptance remain open. Continues ADR 0033 and #10/#14/#15.

## Why another bootstrap is needed

The approved production contract requires parity-critical failures to stop before
login. RoF2's first traced DirectInput call follows server-selection/login setup,
so ordinary first-export initialization cannot establish that guarantee. Waiting
for health after a normal launch would preserve the timing defect.

An initial debugger-breakpoint experiment also stalled: while its primary thread
was suspended, the remote initializer never ran. A second experiment stopped at
the PE executable entrypoint instead; loader/CRT work in the imported fixture DLL
then completed while the executable's main code remained blocked. These are
Windows fixture results, not an actual RoF2 play test.

## Decision and implementation

`eq-client-dll/bootstrap/entry_gate.h` implements an x86 bootstrap primitive:

1. Create a new owned process under DEBUG_ONLY_THIS_PROCESS with a mutable quoted
   command line, explicit executable/directory and optional private Unicode env.
   Never attach to an existing PID. Keep a kill-on-close job and debugger
   kill-on-exit armed throughout preparation.
2. Match the debug event's executable file identity to the verified read-locked
   file, assign the child to its job, record creation FILETIME, and verify remote
   PE32/I386 headers and AddressOfEntryPoint against the supplied trusted metadata.
3. At the create-process event, replace exactly the expected entry byte with INT3,
   checking read/write/cache flush/protection restoration. Match the imported
   proxy's debug-event file identity and record its actual child load address.
4. Continue loader events and the initial system breakpoint. At the entrypoint
   trap, restore the exact original byte, require EIP=entry+1, rewind EIP and add
   an explicit suspension to the primary thread.
5. Call the verified proxy initializer at child module base + export RVA in a
   remote thread. Continue its debug events while the primary remains suspended.
   Require successful initializer exit, then invoke bounded health validation.
6. Detach the debugger and resume the primary only after successful validation.
   Transfer the process and still-armed job to a move-only owning result; its
   destructor closes containment. The session owner must keep these handles or
   explicitly transfer them before it exits. No fallible startup gate follows
   the resume operation.

Every failing pending event requests or observes child termination **before**
continuation. Drain exit events and wait for the retained process handle. An
unconfirmable cleanup failure terminates the dedicated bootstrap itself, allowing
Windows debugger/job cleanup; it must never fall back to normal launch. The real
proxy's self-termination may report initializer-thread, primary-thread or process exit first;
all are failure, never readiness.

Debug event file handles are closed explicitly. Event process/thread handles are
owned by Windows. Native inspection confirmed they were already invalid after
detach; closing their old numeric values again is unsafe. Independently returned
CreateProcess/CreateRemoteThread handles remain our responsibility. Repeated
fixture launches showed stable handle counts after one-time debugger setup.

The proxy exports `NightcapInitialize(void*)` using the Windows thread calling
convention. It invokes the existing serialized required initializer and returns
zero only after readiness. All six original DirectInput export ordinals remain
unchanged. Proxy version 0.3.0-dev and the shared catalog bind this new candidate;
health schema remains 1.

## Exact-client observations and remaining work

Read-only inspection of supported eqgame (SHA-256 beginning `2a8702ad9f72`):
entry RVA `0x004E3B4A`, VA `0x008E3B4A`, first bytes
`E8 CE 3E 01 00 E9 89 FE FF FF`, executable TLS-directory RVA zero.
The bootstrap has not been run against that executable. The native tests use
owned disposable hosts exclusively; no installed client files changed.

The primitive intentionally accepts trusted PE metadata and locked handles, not a
user-visible launch request. Before production use, the launcher must verify the
signed active generation, exact executable and required inventory under retained
read locks; parse and validate the proxy export RVA; provide a fresh private
nonce; validate actual PID/creation/config/catalog health through its existing Go
validator; and own session containment across helper handoff/cancel/exit. The
callback must honor its deadline. Failed/expired/offline-invalid generations must
not reach process creation. A normal-launch fallback is not permitted.

Build the signed x86 bootstrap helper and connect it to the x64 Wails launcher,
then test the supported game, normal and injected MQ2, startup/cancellation/crash
paths and full class/slot behavior. Play stays disabled until these and the other
production contract gates pass. This phase is a timing mechanism, not delivery
of the missing spell/Skills/trainer/AA/Bard client features.

## Sources and evidence

Microsoft documents [debug event ordering and handle ownership](https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events),
[debugger continuation rules](https://learn.microsoft.com/en-us/windows/win32/api/debugapi/nf-debugapi-continuedebugevent),
and [remote-thread loader serialization](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createremotethread).
The experiments, exact commands and limitations are in
[phase 15](../milestones/phase-15-report.md).
