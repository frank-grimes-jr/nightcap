# September 19 live activation

The owner explicitly requested completion of live deployment and then promotion
of the changes to main. This release is authorized before manual acceptance;
the [exact gameplay checklist](client-gameplay-20260919.md) remains open.

## Verified live state

At 2026-09-19 16:14:32 UTC, world and all eight zones were running the candidate
binaries. Hashes were read from each running process's `/proc/PID/exe`, not only
from files on disk. All 22 deployed source/build files matched the candidate.

| Component | SHA256 |
|---|---|
| World | `f7db30da4c3c337637b6a42dce82dc0290818e7c692584652a4bb99fc13149cd` |
| Zone | `f941d7d4ffd7b414e8e0aefc2a74d4b3078829e34153349a47edf337d765a4fd` |
| Previous world | `4ce4709f866889bbcde05f59690cff3cefb7760f85029cff1ee277d85f3d762f` |
| Previous zone | `e79e7f2eacd50237a8c74aeda44896e124159d114b5b7c37979e9a1356eb645c` |

`Character:AAExpMinLevel=1`, `Expansion:CurrentExpansion=0`, and
`Zone:StateSavingOnShutdown=true` survived startup. `character_pet_armor` has the
expected 18 columns and initially zero rows. All five hub content tables matched
the exact planned afterimage after startup. Class merchant stock remains 1,747
listings / 1,229 distinct items; all 1,769 captured merchant rows are unchanged.
The 14 checked fresh world/zone log files contained no Error/Fatal lines.

This verifies deployment, not rendering, gameplay balance or owner acceptance.
PoK's new models, UI behavior, effects and pet transfers still need the linked
in-game checklist.

## Backup and activation evidence

Local evidence is in
`E:\EQ_Local_Dev\artifacts\client-gameplay-20260919\live-activation`.
Private configuration and database dumps remain local and are not committed.

- `binary-manifest.json`, `file-manifest.json`, `before/`, and `world.before` /
  `zone.before` preserve the previous deployment, including zone CMake registrations.
- `pok-shutdown.log` records Healtest's save and all 267 PoK state rows saved.
  The supervisor was paused while zones received SIGTERM. No zone was force-killed;
  exited zombies were treated as exited until their parent could reap them.
  Spire's official stop disabled its automatic launcher flags before DB writes.
- `peq-before.sql.gz` passed full gzip decompression: 46,396,614 compressed bytes,
  441,566,517 uncompressed bytes. SHA256:
  `fd71103dd8d1fb208b8dde4369bb310133422a39ee669390ec1c2d6cedf0078e`.
- `hub-before.json` was captured after shutdown. Fresh `hub-v4` forward/rollback
  SQL passed all 26 independent MariaDB controls; the scratch schema was removed.
  The live forward migration invalidated exactly 22 affected non-corpse,
  instance-0 states while preserving other saved states and merchant stock.
- The additive pet schema was created once. Hub application independently matched
  its exact expected afterimage. Schema creation and hub application are separate
  operations: do not blindly rerun both if only the latter needs recovery.
- Candidate binaries were staged and hashed before replacement. Initial chmod
  stopped because Docker copied the staged files as root; the corrected operation
  used container root for ownership and mode changes. Neither original binary
  had been replaced at that failure. Final installed and running hashes match.
- `installed.json` and `live-verification.json` record successful installation,
  startup, rules, schema, source hashes and log checks.

## Client delivery status

The new signed launcher is
`E:\EQ_Local_Dev\artifacts\client-gameplay-20260919\launcher-auto-ui\nightcap-launcher-qa.exe`.
Its SHA256 is `cfe6f65dc32742b88707c10346d072613eb8c88264308ac5bdca48ce0bd2fc7e`.
Release 2026091904 contains 13 files, 34 guarded code sites and 12 required runtime
features. It selects Nightcap during native character UI loading; no slash
command is required. The manifest expires 2026-10-19T15:48:53Z.

Native hook tests, exact-client verification, both Go suites, frontend compilation
and eight browser tests passed. Final client installation and real startup remain
pending because the owner still has release 1903 running. The user manually
installed that earlier package into the original client folder. The repository's
original-folder protection requires an explicit override before this agent updates
that location; the separate QA copy is the alternative. No claim of 1904 runtime
or in-game acceptance is made here.

## Recovery

Stop zones gracefully and verify fresh saves before recovery. The old world/zone
binaries and all changed source preimages are retained locally. Restore matching
source/build files and binary pair together; new source paths are identified by
null preimages in the manifest. Validate hashes before and after any replacement.

The generated `hub-v4/rollback.sql` guards the exact content afterimage and never
restores stale saved-state rows. If PoK has since generated new affected states,
stop it and recapture/reconcile those states rather than weakening the guards.

Never drop or truncate `character_pet_armor`: it owns real items once used. Reclaim
all items with the compatible candidate before removing armor support, or retain
a compatible recovery build. A full PEQ restore after new gameplay loses subsequent
progress and requires a separate owner decision. Client recovery uses the signed
installer's journal/backups for the authorized selected client folder.
