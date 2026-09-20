# Permanent Nightcap patcher

The owner approved this flow on September 20, 2026. [ADR 0043](../adr/0043-permanent-nightcap-patcher.md) defines the trust and recovery boundaries.

Players extract `nightcap-friends.zip` once into a permanent folder, make a shortcut to `nightcap-launcher.exe`, and keep their existing RoF2 game folder. The starter verifies `/launcher-channel.json`, downloads a changed desktop EXE and opens it. Launcher settings stay in `%APPDATA%/NightcapLauncher`; versioned EXEs and the separate rollback checkpoint stay in `%LOCALAPPDATA%/NightcapLauncher/applications`. The starter remains alive until its desktop exits, serializing starts and retaining verified file handles. Old cached versions remain; they are never selected as an unsigned or expired offline fallback.

The desktop checks on opening/selecting a client. Play checks fresh signed game metadata, automatically recovers interrupted installations and applies required patches before starting the game. Downloads are per changed file, not binary deltas; unchanged files are rehashed and reused. Full copies still exist in staging/backups for recovery. Game settings and the original base executable remain protected.

## Release counters and compatibility

- Game manifests use their own increasing `release`. Production inventories can evolve within compiled game-asset scopes; the four core patch files stay mandatory. New EXEs/DLLs outside those core paths, user INIs and broad deletions are rejected.
- The production profile's `version` identifies the desktop. `minimum_launcher` identifies the game-update protocol minimum and defaults to `0.3.0`; do not increase it for an ordinary compatible content patch.
- Launcher channels use a separate increasing release counter, signed kind `nightcap-desktop`, schema 1 and platform `windows-amd64`. Game metadata cannot authorize an executable update.
- Launcher/game metadata expires after 30 days. Publish a newly signed higher release before expiry, even when its file hashes are unchanged. There is currently no automatic renewal job.
- The starter's compiled production trust expires September 20, 2028. Arrange a reviewed trust-key/starter migration before then. A protocol or trust-root change can require a new starter; routine desktop and gameplay releases do not. Downloads use Ed25519 verification, not Windows Authenticode.

## Packaging

Run from `eq-launcher` in a clean release worktree with Go, Wails and lockfile-pinned frontend dependencies. Generated policy creation is exclusive; keep previous build outputs in their release artifact directory. Keep the private signing seed outside source and all publish directories. Generate the production policy and game files with `go run ./cmd/nightcap-package -client <read-only eqgame.exe> -assets <generated assets> -key <local seed> -release <game release> -production-profile <profile> -publish <new game directory>`. Generated policy deliberately retains the prior exact inventory so old schema-1 recovery journals remain recoverable. New journals carry their candidate's signed inventory. Recovery verifies authority while allowing expired metadata; that exception cannot authorize installation or Play.

Build with `./build-production.ps1 -Destination <new friends directory> -Profile <profile> -Key <local seed> -LauncherRelease <launcher release> -LauncherPublish <new launcher directory> -Wails <wails.exe>`. It audits/builds the frontend, builds the desktop, signs its channel, verifies that channel against the exact compiled starter trust, builds the stable starter and packages the friends ZIP. A wrong signing key fails the build gate.

For future releases, reuse the shipped starter instead of requiring players to replace it. Run unit/native/UI checks and independently review executable update changes. Upload immutable game and desktop paths first; verify every size/hash, then publish the launcher channel, ZIP/guide and game channel atomically. Hosted files already work with the existing nginx configuration (`no-cache` for new launcher paths). No game-server restart is needed for static launcher publication. Do not put private keys on the server.

## Recovery and rollback

Keep previous public metadata, ZIP/guide and immutable binaries. Publication interrupted between channel renames is safe: each channel references files already present; the new desktop understands the previous game release. Resume the same reviewed publication after confirming current channels are either their expected old or new bytes. Never publish an older counter after clients may have observed the newer one.

To revert a bad desktop, sign its previous executable bytes as a **higher launcher release** and publish that channel. To revert game content, publish previous reviewed bytes in a **higher game release**. Do not reset players' checkpoints or disable signature checks. A same-release cached executable with a bad hash is redownloaded. An interrupted download leaves only a disposable `.partial`; its verified version is required before the checkpoint advances. Network/signature/hash failures stop startup with a visible error.

## Verification and player acceptance

Automated tests cover changed/unchanged downloads, version-to-version Windows execution, locked images, signatures/hosts/expiry/rollback, download interruption, automatic Play ordering/cancellation/repair, signed offline recovery and real RoF2 catalog validation. Native progress-window close/hide behavior and browser presentation are checked separately.

Player QA: close older launchers, extract the transition ZIP, use the stable shortcut, select the existing game folder, press Play and confirm the displayed release. Close the game/launcher and use the same shortcut again; no manual ZIP replacement should be needed. Owner gameplay QA for the production NPC/spell fixes remains [open](../releases/production-bugfixes-20260920.md#exact-owner-in-game-qa).
