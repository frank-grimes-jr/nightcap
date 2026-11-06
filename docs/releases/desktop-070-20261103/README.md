# Desktop 0.7.0 — published November 3, 2026

The owner approved main and server publication in chat. [PR #399](https://github.com/frank-grimes-jr/nightcap/pull/399)
merged at `acef354e`. Desktop **0.7.0**, launcher channel **2026110301**, is live.
The game channel is unchanged.

## What changed for players

Patch notes can carry database/server-side changes (`"kind": "server"`, a Server
badge) and an optional one-line `reason` shown as "Why: …". No game notes use
them yet. Desktop 0.6.0 rejects these fields, so the packager raises any manifest
that uses them to minimum launcher 0.7.0.

## Build

- Built from `release/desktop-070` (main `acef354e` plus a vite 8.3.0 → 8.3.5 patch
  bump, needed because `build-production.ps1` refuses high `npm audit` findings).
- Trust policy: the exact policy shipped with 0.6.0
  (`Documents/Codex/2026-10-12/th/.../policy_production_generated.go`) with only
  `LauncherVersion` changed to 0.7.0. Keys, hosts and recovery inventory are unchanged.
- Profile: `artifacts/desktop-070-20261103/profile.json` (version 0.7.0, minimum 0.6.0).
- Go 1.27.3 / Wails v2.16.0 on Windows. Default and production-tagged `go test ./...`,
  frontend build and all 11 Playwright tests passed.
- `build-production.ps1` signed the channel with `production-4acb02e67aeb0b51` and
  its release check passed against the compiled starter trust.

| Item | Value |
| --- | --- |
| Desktop exe | 12,592,640 bytes, `4a13096be5ffba28accbb81822c1e9d6232adb38daada468c48d84f9a6302824` |
| New launcher channel | `abd6a3bceba70aae02b7ddf178c23832ecdd665bf6a708a47e1e7a4c82172d9b`, expires 2026-12-03T16:28:42Z |
| Previous channel | `67a94a6d56fca08d21c0d808a2929855ec9e20bf8891ccd390f23cf1f18c3e8e` (0.6.0 / 2026101201) |

## Publication

`publish.py` runs under `.deployment.lock` in two modes, and each mode checks that
every other top-level public file is byte-identical. `selftest.py` exercised it on
the host against a temporary folder first (switch refused before the exe exists,
idempotent reruns, a drifted channel refused).

1. `--mode exe` (16:31 UTC) wrote `launcher/2026110301/nightcap-desktop.exe`. The
   HTTPS download matched the signed size and hash.
2. `--mode switch` (16:33 UTC), after owner approval, replaced `launcher-channel.json`.
   The HTTPS bytes match the new channel hash and pass `nightcap-releasecheck`.

No service was restarted. Note: the game container's health check
(`start.py --health`, socket connect timeout) had been failing since about 15:26 UTC,
an hour before this publication's first write. The disk migration session confirmed
it was healthy at 14:53 UTC and is investigating. Cause unknown at publication.

## Rollback and QA

To roll back, sign the 0.6.0 exe again as a **higher** launcher release and publish
that. Never republish 2026101201. Player QA: open the normal shortcut, confirm the
launcher shows 0.7.0, check that patch notes and Play still work.
