# Launcher Play incident — October 1, 2026

Severity: high; players can lose the client during startup. The owner explicitly
authorized the repair, main promotion and production publication. This incident
does not record acceptance of the outstanding gameplay/model appearance gates.

## Cause and repair

The affected production generation is game release `2026093006`. The reported
client log ends at `Error reading ncm01_chr.wld`, `eqpfs/share.hh` line 432,
after the first generated classic model import. The PFS writer emitted version
2 (`0x20000`) with 65,536-byte blocks. Exact supported RoF2 disassembly confirms
that version 2 selects an 8,192-byte capacity; 65,536 belongs to version 3.
The read routine's block-size assertion produces the recorded error.

`tools/classic_model_archives.py` now emits 8 KiB blocks and rejects oversized
version-2 blocks while reading. Independent tests cover the 8 KiB boundary,
multi-block payloads, a large filename table and a valid oversized input whose
declared lengths agree. They fail on the original code and pass on the fix.
The original reader accepted its own invalid output, hiding the incompatibility.

All 22 regenerated archives retain their version, model names, geometry,
textures and animations. Independent extraction compared all **14,858 entries**
with the shipped generation byte for byte. The import list and all model
registrations/remake mappings are unchanged. Rebuilt `dinput8.dll` and generated
Go/C++ hashes authorize the corrected archive bytes together.

## Release contract

Signed game repair **2026100101** has **46 files**, **149,778,397 bytes**.
Exactly 22 archives and their matching proxy change. The other 23 files retain
the hosted `2026093006` hashes, including helper, configuration, patch catalog,
advanced-loot UI, pet UI, spells and terrain. Existing starter/desktop, user INIs,
server binaries, quests and player data require no changes.

Channel SHA256:
`19dc86df5199642e9b30bdc5209ddd1f9c2ced9c405d002407bc440fd449fc78`.
Expiry: **2026-10-31 11:11:00 UTC**. The signature verifies against the already
shipped production public key; no new launcher download or key migration is
needed. The first incomplete local packaging attempt was retained and never
published; `production-publish-final` contains the published release.

## Verification and limits

- Three independent PFS regressions pass, including red/green proof. All 22
  malformed originals are rejected, and repaired archives pass native-sized
  extraction and inverse WLD/texture checks.
- Generated hashes agree with every repaired file; independent code/contract
  review found no blocking issues. Archive bytes increase by about 1.196%.
- Full Go suite passes; production packager verifies all 63 original patch
  sites and the supported executable identity. Native parser/health agreement
  and actual proxy bootstrap shape checks pass with their real fixtures.
- x86 DLL and native model tests pass; the three native advanced-loot tests
  pass. Existing spell/UI/policy Python suites pass (11 tests).
- Signed isolated QA update and real controller Play run for 120 seconds,
  reach login-UI initialization, and stop cleanly. This is **not** proof of
  post-login global model loading or rendered gameplay. Windows was locked
  during this run. The old five-second health check could not catch this crash.
- The legacy PowerShell patch-site verifier reports an unchanged `LootTable0`
  failure; it applies its `.text` RVA/file offset delta to `.rdata`. The Go
  verifier uses PE section mapping and checks the same 63 sites successfully.
  No patch-site or client executable change is included in this repair.
- Twelve publisher tests pass: public/service drift refusal, channel-last
  activation, interrupted-copy and rename recovery, immutable-file corruption
  refusal and original backup retention. Windows lock/directory-fsync stubs
  limit those tests; real staging and publication completed on the Linux host.
- Visible launcher acceptance remains open. The desktop was locked during
  isolated verification; the later computer-control request to open Nightcap
  was denied. No alternative game-launch method was used after that denial.

Local evidence: `E:/EQ_Local_Dev/artifacts/launcher-play-20261001/`, including
`native-pfs-v2-capacity.txt`, `pfs-regression-red-green.txt`,
`archive-independent-verification.json`, `final-contract-review.json`,
`go-tests.txt`, `native-agreement-tests.txt`, `qa-update.txt`, `qa-play.txt`,
`local-verification.json`, `publisher-test-results.txt`, `published.json`,
`hosted-verification.json` and `preservation-verification.json`. Private signing
seeds are outside that directory and excluded from the upload.

## Publication and recovery

The [guarded publisher](publish.py) stages immutable files before replacing
`channel.json` atomically, retains the prior channel for evidence, checks the
captured production/service baseline and uses the shared deployment lock.
Unexpected baseline or immutable-file drift must stop publication. Retrying
the same reviewed candidate is safe after an interrupted copy. No game restart
or database write is part of this deployment.

Release **2026100101** is active on OVH. The publisher verified all 46 assets
before activating its channel. A fresh post-publication snapshot confirms all
five service identities, images, start times, restart counts and health states
match the pre-publication baseline. Game and database remain healthy. The
desktop launcher channel, starter ZIP and guide hashes are unchanged.

Independent public HTTPS verification downloaded all 46 signed assets
(149,778,397 bytes), checked every size/hash and verified the channel signature
against the production key already shipped in launcher 0.3.1. The public channel
matches the reviewed release exactly. [Recorded verification](verification.json).
Source repair and deployment evidence are tracked in
[PR 98](https://github.com/frank-grimes-jr/nightcap/pull/98).

Host stage: `/opt/nightcap/releases/launcher-play-2026100101`.
Immutable assets: `/opt/nightcap/deploy/production/data/public/release/2026100101`.
Do not restore the lower release counter or republish the malformed original
archives. If another repair is needed, preserve current gameplay/receipt
contracts and publish reviewed corrected bytes under a **higher** game release.
The prior channel backup is forensic evidence, not a playable rollback.

## Exact startup acceptance

1. Close the game; reopen the usual `E:/Nightcap/nightcap-launcher.exe` shortcut.
   Use Play and confirm game release `2026100101` is installed automatically.
2. Confirm an EverQuest window opens, remains responsive and reaches login.
   Log in and select **Nightcap**; let loading finish, then select a character.
   The client must get past all `ncm*_chr` imports without `Error reading`.
3. Enter **East Commonlands** (`ecommons`), verify the world renders, then camp
   and repeat Play. Confirm the launcher returns to idle after normal exit.
4. Confirm existing settings, character inventory, pet UI and advanced-loot UI
   remain present. Detailed model appearance/animation acceptance stays in the
   [classic model checklist](../classic-models-20260930/QA.md).

Record the fresh client log/process-bound proxy log and installed generation.
Do not count a `playing` controller phase or proxy `ready` alone as acceptance.
