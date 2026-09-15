# Native x86 bootstrap helper

`build.bat` builds `../build/nightcap-bootstrap.exe` as an x86, asInvoker console
executable with ASLR/NX. Run it hidden with redirected pipes. This is an unsigned
candidate; it is not yet wired into Go/Wails or published as a signed release.
Never launch it from UI-supplied offsets or an unverified helper path.

## Required launcher ownership

1. Verify the helper as a required signed inventory asset and retain its read
   lock alongside the `LaunchLease`. Start exactly that helper path.
2. Make private inheritable duplicates of the lease executable/proxy handles and
   the launcher process handle (`SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION`).
   Use an explicit inherited-handle allowlist, including the redirected standard
   handles. Originals must remain non-inheritable. The helper is x86 and requires
   real inherited handle values fitting 32 bits, never pseudo-handles.
3. Create private stdin/stdout pipes with at least 4096-byte capacity and start a
   dedicated output reader before sending input. Set a fresh cryptographic
   16-byte lowercase-hex `NIGHTCAP_LAUNCH_NONCE` only in this helper's environment.
   The helper snapshots that environment for its owned child.
4. Keep the lease and pipes until session exit. Cancellation/teardown must close
   the helper's **stdin writer** or terminate this owned helper. Closing only its
   stdout reader does not cancel a running session. Parent-process loss is also
   watched. Never kill a discovered PID without owned process identity.

## Wire format

All integers are little-endian. `protocol.h` is the native layout contract.
The request is exactly 56 bytes, then `directory_units * 2` bytes of UTF-16LE
without a terminator. The helper permits at most 32,700 units and a local drive
path. Request framing has a five-second deadline. No command-line arguments are
accepted; the fixed game command is the held directory's `eqgame.exe patchme`.

| Offset | Field | Type |
|---|---|---|
| 0 | magic (`0x4e434231`) | uint32 |
| 4 | version (`1`) | uint32 |
| 8, 16, 24 | executable, proxy, parent inherited handles | uint64 each |
| 32, 36, 40 | entry RVA, initializer RVA, proxy image size | uint32 each |
| 44 | startup/health timeout, 1–60,000 milliseconds | uint32 |
| 48 | original entry byte, represented as uint32 | uint32 |
| 52 | directory UTF-16 code units | uint32 |

Every response is 88 bytes: magic/kind/PID/code as four uint32 values, process
creation FILETIME as uint64, then a zero-terminated/padded 64-byte ASCII reason.
Kinds are `0=Failure`, `1=HealthRequired`, `2=Started`, `3=Exited`. At most three
responses are sent, fitting the pipe even without reader progress. Validate
magic, kind, reason termination and the state transition of every response.

Before `HealthRequired`, the explicit proxy initializer completed but the game
entry thread is still suspended. Open/query the reported owned process and bind
its actual creation time to the response; read bounded runtime health and use
`runtimehealth.Validate` with that identity, the private nonce and signed config
hash. Approve only then by writing little-endian uint32 `1`. Any other value,
EOF or deadline failure rejects the launch. Do not derive trusted health fields
from the health file itself.

`Started` follows approval and successful entry resume. `Exited` carries the
observed game exit code. Both must retain the health request's PID/creation tuple.
Failure may occur before a child exists (PID/creation zero); EOF/helper death
without a complete valid transition is failure. The helper retains the kill-on-
close job and process handle through the game session. It observes parent loss
through a waitable handle and checks post-start stdin closure on a 50 ms poll.

## Native tests

From the repository root, with `pefile` available to Python:

```powershell
./eq-client-dll/bootstrap/build.bat
./eq-client-dll/tests/build-helper-tests.bat
python eq-client-dll/tests/test_helper.py
```

The actual-proxy rejection case additionally requires `eq-client-dll/build.bat`.
All game-shaped executables are disposable fixtures, including the file named
`eqgame.exe`; the installed client is never started by this test suite.

## Go owner integration

The candidate `eq-launcher/internal/session` package now implements this protocol.
It requires the helper in the verified signed inventory, assigns an outer Windows
job before sending a request, validates actual process-bound health before ACK,
and retains the launch lease until all owned processes terminate. Wails Play
wiring and supported-game acceptance remain pending. See
[ADR 0036](../../docs/adr/0036-own-bootstrap-session-in-go.md) and
[phase 19 evidence](../../docs/milestones/phase-19-report.md).
