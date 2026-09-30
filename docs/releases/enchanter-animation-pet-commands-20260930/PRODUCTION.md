# Enchanter animation commands: production deployment

Deployed September 30, 2026 to the OVH server at `play.nightcapgame.org`,
following the owner's explicit main/server instruction. Source fix: `1ce04d0`.
The earlier local akk-stack deployment did not update OVH; this record covers
the hosted deployment. Owner graphical/gameplay acceptance remains pending.

Animations accept standard commands without the PetCommands AA unlock, for
both primary Enchanters and Enchanter pets in another primary class's roster.
Advanced command AA permissions and attack validity/range checks remain.
No client update is required.

## Build and verification

The preserved production source and binaries matched their original manifests.
A fresh zone build changed only `zone/client_packet.cpp`, using the exact patch
from main. Source hashes remained stable during compilation. Existing production
hardening and the other four native binaries were retained byte for byte.

- Image: `nightcap-game:enchanter-animation-20260930`.
- Image ID: `sha256:5a2263643ce4660b632cc033558e9108473fb551fa1436767e2e4aee26622964`.
- Zone SHA256: `8079ef1c11c488d01aba9cf18160520146978298768cf9189c983f8374c6d110`.
- Startup: `2026-09-30T20:17:58.67600417Z`; all 15 native
  process hashes matched, including twelve zone workers; zero new restarts.
- Nine isolated native checks passed with no AA ranks: standard commands,
  shared roster commands including Kintaz's Animation (spell 690), Attack/Quick
  Attack and out-of-range rejection for primary and secondary Enchanters. The previous production diagnostic
  reproduced the rejected animation Guard command. Advanced Hold, Greater Hold,
  Spell Hold and Focus remained locked. All synthetic fixture rows were removed.
- The native diagnostic reuses production objects with recorded hashes and the patched
  command handler; the deployed executable was independently built from fresh
  sources. The compiled pet-selection regression and 19 rollout failure tests passed.
- A complete compressed PEQ backup was restored into a disposable database.
  All 46 player/rule/merchant fingerprints and
  8134 quest/plugin/Lua file hashes matched across activation.
  Normal world startup advanced the market epoch to 11.
- Native, quest API and database startup error scans passed, followed by four
  encrypted public native handshakes. These checks do not prove rendered client
  controls or owner gameplay acceptance; use [QA.md](QA.md).

Full source provenance is retained in the host package's `native-build-manifest.json`.
Local diagnostic inputs, outputs and verifier are retained under
`E:/EQ_Local_Dev/artifacts/enchanter-animation-20260930/`.

Exact hashes, counts and bounded evidence: [production.json](production.json).

## Recovery

The previous image `nightcap-game:pet-management-20260922` remains available at
`sha256:d9aadb51fc2d1b6cb773c102baea1747b734b764028a84e044cde03090e19806`. Host package:
`/opt/nightcap/releases/enchanter-animation-20260930`; private backup/evidence:
`/opt/nightcap/releases/enchanter-animation-evidence-20260930`.

The package's hash-pinned `rollout.py rollback` closes access, captures current
preservation fingerprints, recreates the previous image, verifies current player
data and runtime health, and then reopens access. It does not restore old player
data. Run under the deployment lock:

```sh
sudo flock -n /opt/nightcap/deploy/production/.deployment.lock python3 /opt/nightcap/releases/enchanter-animation-20260930/rollout.py rollback
```

The helper is specific to this image pair and refuses newer image drift. Keep
the backup private and retain later player progress when investigating recovery.
