# Waypoint visual repair — October 11, 2026

Owner approved main promotion and server activation on October 11, 2026.
Deployment verification is pending. The owner reported two human males in Befallen.
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
is needed. Instance Keeper service and appearance remain intact. Positions,
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
idempotence. No production writes have occurred.

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
main promotion and server activation on October 11; rendered acceptance remains
an open live QA check.
