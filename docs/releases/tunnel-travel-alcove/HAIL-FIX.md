# Merrin hail repair — September 22, 2026

Production verification completed at 19:18:59 UTC (15:18 Eastern), then access
reopened after correcting the two travel helper paths and gracefully restarting
the existing game image. Reconnect and hail **Merrin — Tunnel Travel** in East
Commonlands, near the PoK book at `/loc -1537,-335,3.75`. His menu offers the ten
original city destinations. No launcher/client update is required.

September 30 follow-up: the owner confirmed Merrin is fixed and authorized
main/server publication. The gameplay changes were already on main through
[PR 75](https://github.com/frank-grimes-jr/nightcap/pull/75), and all three live
quest files still match main exactly. [Current verification](OWNER-QA.json)
passes the installed quest checks and the newer pet-release native hashes.
No server file replacement, SQL or restart was needed. This closes the reported
hail/destination-click issue; it does not record all ten round trips or the
complete appearance/pet QA matrix as passed. The click investigation did not
produce a separately identified root cause or an additional code patch.

## Cause and correction

The initial release installed `tunnel_travel.pl` and `tunnel_travel_data.pl` under
`quests/plugins/`. Production's native loader uses `plugins/`. The numeric quest
was correctly installed at `quests/ecommons/999810.pl`, but hailing it raised
`Undefined subroutine &plugin::tunnel_travel_hail`.

Installed the identical, hash-pinned main payloads under `plugins/`. Kept the
inert misplaced copies solely for the immutable original release's file guards
and full rollback. No database SQL, content geometry, destination, native binary,
image, supervisor or client asset changed. Existing restart policy rotated the
market once, epoch 6 to 7. Player data fingerprints were captured after graceful
shutdown and matched before access reopened.

## Verification and limits

[Sanitized evidence](HAIL-FIX.json) records the failing pre-fix check and passing
post-fix run. The test now reads the actual runtime configuration and resolves
plugin/quest paths before loading the installed files. It failed with zero
configured helper matches before the fix, then passed all 25 assertions: ten
links, exact landings, repeat/invalid/state guards and the numeric quest adapter.
This executes the installed Perl with stubbed game objects; it does not claim a
real client round trip or rendered appearance.

Four local regression cases cover misplaced helpers, default paths, array
overrides and empty-array scalar fallback. All six migration tests and the
original 25 source assertions still pass. Independent review found no blocker.
After restart, all 15 native executable hashes and 46 preservation fingerprints
matched; startup and follow-up checks found no quest API, native or DB errors.
The native path log reports `plugins`. Four TLS-verified public native handshakes
passed. [Appearance, all ten round trips, Find and pets](README.md#exact-in-game-qa)
still require owner acceptance.

## Recovery

**Current-target restriction (September 30):** production now runs
`nightcap-game:pet-management-20260922`. The commands below are historical and
pin `nightcap-game:tunnel-services-20260921`; do not run that rollback unchanged
against the newer runtime. A current travel-only rollback must preserve the
current native image and use its matching verification, with fresh scoped
content/preservation evidence. The [pet production record](../pet-management-20260922/PRODUCTION.md)
owns the current native release and its separate paired recovery. Do not roll
back pets merely to satisfy the old travel helper's image check.

Pinned helper/test/catalog and private preservation evidence:
`/opt/nightcap/releases/tunnel-travel-hail-fix-20260922/`.
Local packaging and transport evidence:
`E:/EQ_Local_Dev/artifacts/tunnel-travel-alcove-20260921/hail-fix-20260922/`.
The original package, full backup and preimages remain untouched at the locations
in [the initial production record](PRODUCTION.md).

Read-only verification:

```sh
sudo -n python3 /opt/nightcap/releases/tunnel-travel-hail-fix-20260922/hotfix.py verify
```

Authorized full alcove rollback:

```sh
sudo -n python3 /opt/nightcap/releases/tunnel-travel-hail-fix-20260922/hotfix.py rollback
```

This closes access, gracefully saves zones, validates current scoped content and
hashes, removes only the two matching active helpers, then invokes the original
guarded rollback to restore the stones and remove Merrin, his unambiguous cached
state and the three initial quest files. It verifies preservation and the
unchanged runtime before reopening. Do not call the old rollback directly after
this fix: it does not know about the active `plugins/` copies. Drift leaves access
closed for investigation. Never restore the old full backup over later progress.
