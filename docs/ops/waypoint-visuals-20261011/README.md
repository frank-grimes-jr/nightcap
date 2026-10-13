# Waypoint visual repair — October 11, 2026

Owner-approved PR #163 was merged and deployed on October 11, 2026.
The owner confirmed the combined visual issue resolved October 13 after the
[Instance Keeper follow-up](../keeper-visuals-20261012/README.md).
Originally the owner reported two human males in Befallen.
Production inspection found marker NPC 999240 and Instance Keeper 999227 at
world X=35, Y=-82, Z=3. Both intentionally use race 1, gender 0. This is not
a duplicate waypoint or a missing-model fallback. All 72 marker spawn rows
are unique by zone, and the ten saved marker states contain no duplicates.
Najena, Permafrost and Soldungb also overlap an Instance Keeper. Many outdoor
markers overlap native NPCs because the original setup copied their positions.

## Repair and constraints

The global NPC-ID quest gives the existing marker the globally loaded invisible
actor (race 127, gender 0, texture/helm 0, size 6) and persistent `WizardPortal`
effect 178. The same entity retains its nameplate and 25/30-unit discovery box.
The native nimbus mechanism sends the effect to players entering later; repeated
refreshes do not stack it. Signal 20261011 refreshes an already spawned marker.
No timer, new NPC, spell cast, client patch, database migration or binary build
is needed. This initial repair retained the Instance Keeper appearance; the
October 12 follow-up replaced its human model with a floating eye. Positions,
recall destinations, discoveries, Explorer rewards and combat data are unchanged.
This fixes the two-human presentation without deleting either service.

Read-only client evidence: `E:/Nightcap/global_chr.s3d` contains `IVM_ACTORDEF`;
`Resources/GlobalLoad.txt` loads that archive. Record 178 (268-byte records) in
`spellsnew.eff` is named `WizardPortal`. Wisp models were rejected as a universal
replacement because they are not in this client's global archive. Model-loading
background: [EQEmu client race inventory](https://docs.eqemu.dev/server/npc/client-race-inventory/).
Asset availability and native packet routing do not prove rendered acceptance.

## Verification and rollout

Run `perl tools/tests/waypoint_visuals.t` and
`perl -c server-mods/quests/global/999240.pl` from the repository checkout.
The regression initially failed for missing mesh replacement, missing effect
and missing live refresh. All 16 assertions now pass, including unchanged
discovery bounds, duplicate discovery silence, Explorer completion and refresh
idempotence. Eight adjacent Crushbone placement regressions also passed.

## Production verification

Activated main commit `fd7307ea1334ff923700c29b2bd5347865edafd0` at approximately
7:40 p.m. Eastern on October 11. The host file and in-container quest both have
SHA-256 `f8fe9a8783e28b6685104a73769cf083c17ef5c411c9bc616e9fc3a420684e65`.
All 12 zone workers logged completed quest reloads. No quest/Perl errors appeared
in the bounded deployment log window. World and all 12 zones retained the exact
same PIDs and process start ticks. All five services remained running, with game
and database healthy. The scoped refresh signal was sent to NPC type 999240;
this is delivery evidence, not a rendered-client acknowledgement.

The original quest and candidate are retained under
`/opt/nightcap/backups/waypoint-visuals-20261011/`. The original hash is
`78edf254f2b484c6d8855059b1ecddb062b5dae6f64f3c70f7a771fb9f0ec0b4`.
Sanitized [deployment evidence](deployment-evidence.json) records the hashes,
process continuity, service health and reload count. Raw before/after captures
and read-only audit helper are in `artifacts/waypoint-visuals-20261011/` locally.

## Activation and recovery commands

Use `python docs/ops/waypoint-visuals-20261011/run.py check` for the packaged
syntax/regression checks. After owner approval and promotion to main, `apply`
installs the exact quest using the existing OVH SSH identity. It takes the shared
deployment lock, requires the observed original quest SHA-256, retains the
original bytes, writes atomically, reloads quests without resetting timers,
waits for the staggered reload, then signals only NPC type 999240. No process
is killed or unloaded. The database remains unchanged.

`rollback` briefly installs the original quest with a scoped recovery signal,
removes effect 178 and restores the old human appearance on active markers,
then reinstalls the original bytes and reloads. New spawns use the original
quest. Inspect evidence under `/opt/nightcap/backups/waypoint-visuals-20261011/`
before retrying an interrupted operation. File/hash verification does not
constitute an in-game effect acknowledgement.

## Exact in-game acceptance

1. In Befallen at `/loc -82, 35, 3`, confirm one portal marker and one Instance
   Keeper, with no second human. Check visibility, portal scale and nameplate;
   verify the Keeper can still be targeted and hailed.
2. Enter the 25-unit horizontal / 30-unit vertical box on an unattuned character.
   Expect one attunement message and one progress update. Re-enter silently.
3. Recall from the Waypoint Master; arrive at the existing coordinates.
4. Zone away and return after another player has kept Befallen running. Confirm
   the portal appears for the late arrival and remains visible for 60 seconds.
5. Check fresh and saved-state zone boots, classic and modern model settings,
   and ordinary particle settings. Particle-off clients may hide the effect;
   check the nameplate remains usable. Reject the candidate if the portal is
   fleeting, missing, too large or obscures the Keeper.
6. Check Crushbone `/loc -644, 158, 4` and one outdoor waypoint. Verify no new
   human marker, duplicate effect, discovery change or relocation.

The candidate passed `feature → dev → test`. The owner explicitly approved
main promotion and server activation on October 11. Permafrost portal visibility
and function were owner-confirmed October 12. On October 13 the owner replied
**"resolved"** after the Keeper correction, closing the reported visual issue.
This does not separately attest every optional checklist step or every zone;
the deployment evidence retains its original dated scope.
