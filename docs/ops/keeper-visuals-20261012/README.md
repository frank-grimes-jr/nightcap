# Instance Keeper appearance follow-up — October 12, 2026

The owner tested Permafrost and confirmed the waypoint portal is visible and
functional, but the human **Instance Keeper** remains. The October 11 repair
deliberately preserved this second NPC's appearance and therefore did not fully
satisfy the desired presentation. This follow-up covers all seven custom dungeon
Keepers, NPC types 999227–999233, through their shared global-name quest.

The Keeper becomes a small floating Eye of Zomm: race 108, gender 2, texture and
helmtexture 0, size 3. `EYE_ACTORDEF` is present in the globally loaded client
`global_chr.s3d`; no client update is needed. Its name, targetability, destination
lastname, location, instances and all dialogue/confirmation code are retained.
This is an appearance illusion, not a summoned pet or spell cast. The waypoint
portal quest and player discoveries are unchanged.

## Evidence and checks

Production inspection found exactly seven human Keepers, one each in Befallen,
Unrest, High Keep, Najena, Cazic-Thule, Permafrost and Nagafen's Lair. No zone or
NPC-ID quest overrides were found for those types. The deployed original quest
SHA-256 is `2d5f6af9dcc015dc222a23b50ea338d594e0420c2570353e6f0e572ff4b86969`.
Read-only inspection and captures: `artifacts/keeper-visuals-20261012/` locally.

`perl tools/tests/instance_keeper_visuals.t` originally failed on absent spawn
and live-refresh appearance handlers. All 13 checks now pass, including human
replacement, live refresh, repeated/unrelated signals, correct dungeon/version,
hail/status/join and reset confirmation. The 16 existing waypoint checks pass.
The `EVENT_SAY` through end-of-file region exactly matches the captured live
quest, preserving every interaction branch. Perl syntax and diff checks pass.

## Activation and recovery

This is a correction to the previously approved main/server waypoint repair.
`python docs/ops/keeper-visuals-20261012/run.py check` runs local validation.
After merge, `apply` requires committed operation files on `origin/main`, takes
the existing deployment lock, checks the exact original quest hash, backs it up,
atomically installs the candidate, reloads quests without resetting timers and
signals the seven Keeper NPC types with 20261014. Future spawns use EVENT_SPAWN.
No DB writes, native restart, instance reset or waypoint relocation occur.

`rollback` installs a temporary recovery handler, signals 20261015 to restore
race 1/gender 0/texture 0/helm 0/size 6, then restores the original quest bytes
and reloads. Backups: `/opt/nightcap/backups/keeper-visuals-20261012/` on OVH.
Inspect existing evidence before retrying an interrupted apply. File and reload
checks are deployment evidence, not client rendering acceptance.

## Exact live QA

1. In Permafrost at `/loc -121, 61, 2`, expect the portal plus a small floating
   eye named Instance Keeper, with no human service model. Check visibility,
   size, grounding and that both nameplates are readable.
2. Target/hail the Keeper. Confirm it offers **Permafrost**; status and join
   behave as before. Verify an existing instance remains available. Do not
   confirm reset on a valuable instance merely to test a cosmetic change.
3. Zone away and back, and test an already-running zone. Both appearances
   should remain correct for late arrivals and after a fresh zone boot.
4. Check Befallen `/loc -82, 35, 3` and one other Keeper. Discovery and recall
   should remain unchanged. Native unrelated NPCs are not part of this change.

## Deployment result

PR #181 merged to main and was activated on OVH October 12 at approximately
2:32 p.m. Eastern. Deployed commit `63c8335ec9ba378a80bacebc460bce642b1abfe2`;
the host and in-container quest SHA-256 both match
`8ae628f60cc5913f55811cd4c3f0287873c792d904240f580624560418026d0f`.
All 12 zone workers logged completed quest reloads; no quest/Perl errors were
found in the bounded deployment window. World/zone PIDs and start ticks were
unchanged. All five services stayed running and game/database remained healthy.
The waypoint quest hash is unchanged. Refresh signals were sent to all seven
Keeper types. [Sanitized evidence](deployment-evidence.json) records these checks.

The earlier main/server authorization covers this corrective follow-up.

## Owner acceptance — October 13, 2026

After the Permafrost report identified the remaining human as Instance Keeper
and the floating-eye correction was deployed, the owner replied **"resolved"**.
This closes the reported waypoint/keeper visual issue and its rendering
acceptance gate. No further runtime change was needed. The confirmation does
not separately attest every zone, client setting or checklist step above.
The dated deployment JSON retains its original pre-acceptance scope.
