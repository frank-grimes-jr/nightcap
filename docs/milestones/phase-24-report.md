# Phase 24 — Automatic UI loading and live activation

September 19, 2026. The owner requested automatic UI loading, then explicitly
authorized making the changes live and merging everything into main.

## Built and verified

The exact-build proxy redirects the two native character UI skin assignments to
`nightcap`, covering saved/default/custom/missing preferences and reloads. Native
window layout handling remains in place. The stock character-selection screen
retains its original path. Signed release 2026091904 requires all 12 features and
34 guarded sites. The launcher now explains automatic activation.

Native calling-convention tests, exact-byte checks, both Go test configurations,
the frontend build and eight browser tests passed. Independent review confirmed
the load/reload call paths, return/stack convention and ASLR-stable call sites.

The server/database release is live: matching world and eight zones, 22 source
and build files, the 18-column pet armor table, and the compact 22-service exotic
hub. Fresh migration/rollback rehearsal passed 26 controls before application;
the full database backup was decompressed and verified. Post-boot process hashes,
rules, schema and exact hub/merchant state passed; checked fresh logs had no
Error/Fatal lines. [Evidence and recovery](../releases/client-gameplay-live-20260919.md).

## Remaining work and limits

Final 1904 client installation/startup is waiting for game exit and the selected
authorized folder. The current original client is still running 1903, which the
owner installed manually. The original-directory restriction remains in force
unless explicitly overridden. Prior 1903 startup success is not 1904 evidence.

Manual gameplay acceptance remains open, including automatic UI rendering for
existing/new characters, pet item/stat behavior, model rendering and ground
placement, death effects and encounter balance. Main promotion is authorized for
this release before acceptance; it does not certify these tests. No hosted updater
or Windows code-signing release was added in this phase.

## Operational lessons

Deployment manifests must include CMake registrations as well as source files.
Pausing a supervisor prevents reaping, so zombie workers must not be mistaken for
zones still saving. Use the official launcher stop and verify its auto-start flags.
Docker-staged binaries need explicit container-root ownership/mode handling;
compare both staged and running hashes, and preserve rollback preimages.
