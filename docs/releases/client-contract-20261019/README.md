# Client runtime contract repair — October 19, 2026

Status: **signed and verified candidate; publication and new native Play QA pending**.
Source: `feature/client-contract-repair`, based on current main `73358d0`.
The owner reports the same Play failure on this PC and other players' PCs.

## Cause and exact repair

Public game release 2026101802 signs proxy 0.11.0 alongside the retained 0.10.0
catalog. The five-file custom delta omitted `nightcap-patch-sites.json`.
All 138 file hashes and the signature can pass while that pair still cannot launch.
The October 18 hosted-verification receipt proves delivery integrity, not runtime
compatibility; its earlier pairing claim is superseded by this incident.

The installed DLL SHA256 is
`9dd6ad400d7390f95c3af88ffe70a67c180368a213e13cc951cee20fefb63380`.
It reports catalog `2599919e5701d4b2dc43e569da72a3d99e503ae6f511f690d7a09fe581f1a8b4`;
the installed and signed catalog instead hashes to
`42351ac8e1f402b03f04dc55ab9aa20ec6a6946c65f20d314f94bc682d9e55a7`.
The local 2026-10-19 04:53 EDT health report is `ready`, with all 17 required
features applied (mask 131071). The launcher correctly rejects its contract.
`bootstrap helper exit: exit status 3` follows that rejection.

Prepared signed game **2026101901** changes only the 9,542-byte catalog, using
the reviewed source bytes that match the DLL. All 137 other file descriptors,
including URLs, remain exact. Desktop 0.6.0, starter, server, database, client
settings, patch history and retirement policy remain intact. The candidate lives
at `E:/EQ_Local_Dev/artifacts/client-contract-20261019/`; `verification.json`
records its exact hash and validation scope. No game-directory writes occurred.

## Verification and prevention

- RED: the new packaging regression accepts the known broken pair without the
  gate, reproducing the missing release check.
- GREEN: the gate rejects that exact signed DLL/old catalog and accepts the
  same DLL/corrected catalog. It also rejects missing identity, malformed PE,
  overlay-only identity, mismatched versions and unsafe sections.
- The actual pinned eqgame executable and corrected catalog pass all 107 sites.
- Offline replay of the recorded health JSON yields the reported error with the
  old catalog and passes the unchanged validator with the corrected catalog.
  Reusing recorded identity is diagnostic only; this does not authorize a launch.
- Complete launcher `go test ./...` passes outside the Windows sandbox, whose
  socket, junction, credential and rename restrictions initially blocked tests.
  Native helper integration fixtures requiring optional environment paths remain
  their normal skipped scope. No new desktop or DLL build is required for repair.
- Six publisher tests pass on Windows and Linux, including interruption/retry,
  candidate/baseline drift, retained-asset drift and immutable-path protection.

`preflight.CheckProxyCatalog` checks the exact PE's mapped read-only hash/version
constants before signing. It is called by the ordinary packager and this repair's
`prepare.go`. It detects accidental mixed builds; signature authentication and
process-bound runtime health remain required. Custom publishers must validate the
complete assembled pair, even when one member comes from a retained baseline.
The patch-history test now follows the current repository release instead of
hardcoding October 17's counter and entry count; future-release rejection remains.

## Publication and recovery

Owner approval is required before changing the public channel. Upload only the
candidate channel/catalog, retained `previous-channel.json`, and reviewed
`publish.py` into a new private release stage. Under the deployment lock, the
publisher requires the pinned old/new channel, healthy unchanged five-service
identities, all 137 inherited file hashes and unchanged public controls. It
durably writes the new immutable catalog before atomically replacing the channel.
It is safe to retry after the tested interruption. No service restart is needed.

After publication verify the served envelope with the shipped key, all 138 HTTPS
asset hashes, and DLL/catalog pairing, then record the public release and native
QA separately. Do not lower counters, reset player checkpoints or restore the
broken 2026101802 pair. Recovery after clients see 2026101901 requires another
higher signed release containing a valid pair. If publication is interrupted,
resume only when the old/new channel and all retained assets still match.

## Exact owner QA

1. Close EverQuest and the launcher. Open the normal Nightcap shortcut and use
   the existing game directory. Confirm update 2026101901 and its launch-fix note.
2. Press Play. Expect no runtime contract error and normal login/server selection.
3. Enter Palwar in East Commonlands; confirm the existing character, inventory
   and UI settings are retained. Close normally, reopen and repeat Play.
4. Repeat the normal update/Play on another previously affected player's PC.
   No fresh install, access-code reset or manual DLL copying should be necessary.

Wiki: Launcher, home, In development and Recent changes carry explicitly pending
repair notices. All 21 guides and 432 generated routes were reviewed for impact;
gameplay Features, commands, item values, zones and mechanics remain unchanged.
Local documentation is not a public wiki release. See `wiki-review.json`.
