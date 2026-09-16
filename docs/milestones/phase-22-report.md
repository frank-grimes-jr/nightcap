# Phase 22: usable local QA launcher

Date: 2026-09-15. Scope: signed offline patching and supported-client launch.

## Built

- QA-only generated embedded Ed25519 release, four mandatory assets, complete
  signed-generation staging and normal journaled installation/repair.
- Portable settings, distinct singleton/title/badge/Windows metadata, saved-client
  discovery on startup, repeatable packager/controller QA tools and build script.
- Independent full RoF2 copy at the package path; no original-client mutation.
- Bounded post-exit writable-open probe for a reproduced Windows image-mapping
  teardown race. It never writes executable bytes.

## Verification

- Desktop Go tests and vet pass; actual-image preflight verified 22 patch sites.
- Eight Playwright UI checks pass, including explicit QA channel branding.
- Bundle signature/damage/missing/expiry/cancellation/size/canonical tests pass.
  Controller Check/Update tests prohibit HTTP and prove no fallback for a missing
  bundle. Default builds remain keyless and launch-disabled.
- Normal controller installed release **2026091501**, detected a deliberately
  changed QA config with Play disabled, then repaired all four assets successfully.
- Actual copied RoF2 started through Controller.Play: PID 19840, creation
  134339899344685006, runtime health ready, required/enabled/applied masks all 511.
  Game log reached successful renderer initialization and login UI configuration.
  Owned cancellation returned stopped/idle and re-enabled Play.
- Final packaged Wails UI: Check showed all four files verified, Repair completed,
  Play started actual EverQuest at the EULA screen (no login entered). Runtime
  PID6220, creation134339912430431720, masks511/511/511, ready; launcher showed
  running with update/folder/Play disabled and Stop available. Desktop Stop
  closed the game and restored Play with no cleanup error.
- Windows cleanup race reproduced 6/30 before fix. Initial transient probe passed
  50/50, full session suite five times. Independent review required bounding permanent
  external locks; final bounded version passed 30/30 normal cancellations,
  persistent-lock regression three times, full desktop tests and vet.
- Original eqgame.exe, dinput8.dll, eqclient.ini and eqhost.txt SHA256 unchanged.
- Final independent code review approved after the timeout regression fix.

## Package identity

Executable SHA256:
`d27ce3e65edcce72fcae36965e21334a17589b10650a4bbd8b93b62d3eb3527c`.
Manifest SHA256:
`b1d2e14632740d5dd33ca4fbfc55ca36e21e4960af4457ea05557fc2c00ccd06`.
Public key fingerprint:
`bdc8176fda05f9681d8d35065773bcf378cee8217321614470297070a2724105`.

Local evidence: `E:/EQ_Local_Dev/artifacts/nightcap-qa-20260915/evidence/`,
`launch-verification.log`, bundle audit/signature/manifest and launcher hash.
[Owner instructions and exact QA](../releases/launcher-qa-20260915.md).

## Cut / still open

No hosted production update channel, Authenticode, public game-client distribution,
new server deployment or completed in-game multiclass acceptance. The local
release expires October 15 at 23:50:31 UTC and must be rebuilt before expiry.
Gameplay/client-roadmap issues remain open for their original acceptance gates.
