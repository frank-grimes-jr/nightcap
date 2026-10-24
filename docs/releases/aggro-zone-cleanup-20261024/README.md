# Aggro departure and NPC return-home candidate — October 24, 2026

Status: source candidate; no production installation or owner acceptance.

Palwar reported that gargoyles, skeletons and frogs regrouped on returning to the
Lower Guk bedroom area in a **Raid** run after death, zoning and logout. They were not already in
Extended Targets at arrival. The owner confirmed **no Feign Death** was used,
so the separate feign-memory defect does not explain this encounter. The owner
subsequently identified **Thursday evening's run**, matching the older Raid
checkpoint described below, and said the return was **more than an hour later**.
That initially suggested checkpoint restoration. Later client-log evidence,
below, records fresh Raid entries rather than a return to the saved run.
This observation does not establish persistent hate:
fresh proximity/social aggro, displaced NPCs and remembered targets must be
distinguished. Two native defects are reproduced and corrected here; neither is
claimed as a completed in-game resolution or the cause of the logged fresh-Raid
trains. Both remain separately reproduced native defects.

## Evidence and corrected behavior

The source authority is main `ebeb6591`, with the retained Chapterhouse build
whose zone SHA-256 is
`2c9323e43c7287780acf6183b54bbd5800ed4a1e19c7655e1fd6f828de861eb6`.
The default workspace is older and contains unrelated changes. Work is isolated
in `E:/EQ_Local_Dev/_worktrees/aggro-zone-cleanup`.

1. **Feign memory survives departure.** Ordinary hate/rampage cleanup does not
   remove NPC feign memory, which stores bare zone entity IDs. The native AI can
   resolve a recycled ID to a new client and add hate. Accepted player death now
   calls memory-only `ClearFeignMemoryOnDeparture` before the corpse takes the ID; the client
   destructor does the same after existing group/raid bookkeeping and before
   final removal, covering zoning and logout.
   A vetoed death is unaffected. Other players' hate/feign entries and ordinary
   feign, memory blur and fading paths retain their existing semantics. Shared
   group/raid Extended Target counters are left to existing lifecycle cleanup.
2. **A restored pull position becomes home.** `Spawn2::Process` constructs a
   restored NPC at its saved position; `NPC::AI_Start` uses that as its guard
   point. Restored stationary NPCs now keep their canonical spawn home, normalized
   using the same ground/water rules as a fresh spawn before quest callbacks.
   Their pre-publication position, construction spawn point, HP, mana, loot and
   saved state remain unchanged. Grid and roambox roamers retain existing behavior; dynamic
   quest actors, corpses and respawn timers remain separate. The canonical-row
   lookup is value-initialized so a missing row safely uses the saved fallback.

The change adds no leash, aggro immunity, global hate wipe, encounter reset,
instant teleport home, rule, schema migration or client dependency. Normal new
proximity/social aggro remains possible when a player returns near hostile NPCs.

Read-only production observations on October 24 at approximately 11:27–11:31 UTC:

- Running game image `db570029805b` matches the dated Chapterhouse release.
- Lower Guk uses ruleset 1 and a one-hour unload delay. NPC return delay is
  5–30 seconds; empty-zone NPC processing pauses after 60 seconds. Logging out
  for longer does not necessarily let a long return path finish while idle.
- Public Lower Guk has 230 saved rows from October 23 UTC. All 23 captured
  displacements over 50 units were roaming-grid NPCs; no such stationary
  displacement was observed in that saved snapshot.
- At 11:15 UTC Palwar entered fresh Keeper instance 103. Its boot explicitly
  reported no saved state. A bind return occurred at 11:17 UTC; the instance
  became idle at 11:18 UTC. Retained logs also show an older instance 101.
  These logs do not contain a hate-list dump proving the reported cause.

A second read-only check at 12:08 UTC inspected the **managed Raid checkpoint**,
which is separate from `zone_state_spawns`. `LoadZoneState` consumes
`NightcapDungeon::LoadCheckpoint`; its managed-zone-variable bypass does not
bypass NPC restoration. The return-home defect therefore applies to Raid/Grind
checkpoint reloads too.

The October 22, 19:45 Eastern Raid retained 230 rows at its 20:50 unload. Two
stationary froglok shin knights (spawn IDs 9818/9819) shared exactly the same
saved position, 226/249 units from their canonical homes. Another stationary
shin ghoul knight (9964) was nearby, 54 units from home. Two additional large
3D differences were height-only and are not evidence of a pull. Thirty-six
roamers were displaced by over 50 units. This establishes a saved cluster,
in the owner-confirmed incident run, not that hate persisted or that a reload
preceded the particular re-entry. The owner's report of returning more than an
hour later is consistent with the logged one-hour unload. Today's
fresh Raid had no checkpoint at the time of capture. No return/reload sequence
for the reported encounter has been established.

### Later client-log correlation

Read-only inspection of `E:/Nightcap/Logs/eqlog_Palwar_Nightcap.txt` identifies:

- Thursday 19:25:34 local: public Lower Guk entry, followed by combat.
- Thursday 19:45:21: Raid101 entry; the journal says 719 minutes remain,
  confirming a fresh run. First recorded Raid attacker is a froglok shin knight
  at 19:49:25; gargoyles join at 19:50:02; a deadly black widow kills Palwar at
  19:50:29. This agrees with the retained server log.
- The next recorded Lower Guk entries are Saturday 07:15:14 public and
  07:15:38 fresh Raid103. Frogs begin attacking at 07:15:55, followed by gargoyles
  at 07:16:54; a tal ghoul wizard kills Palwar at 07:17:28.

There is no recorded post-unload return to Raid101 in this client log. This
limits the earlier checkpoint inference despite the owner's recollection of a
later return: the logged fights cannot be attributed to restored Raid101 hate
or home positions. Normal fresh proximity/assist chains and pathing still need
observation if those fights are the reported symptom. Do not claim this candidate
resolves them. The full client log remains private and outside the repository.

Raw character/location/network logs are retained only in ignored local
`artifacts/aggro-zone-cleanup/`. No database rows, running services or client
files were changed by investigation.

## Verification

Both new behavioral regressions failed against the original implementation:
stationary home was the saved pull point, and departure/death replayed stale
feign hate onto a replacement client. They pass with the changes. The focused
Windows suite passed 9 tests, including existing dungeon lifecycle, private
spawn and policy controls. Native fixtures execute extracted production methods
with explicit dependency fakes; they do not simulate the complete network or
movement lifecycle. Retained upstream helper excerpts have authenticated source
hashes. See `verification.json` for completed checks and their limits.

The isolated native builder `tools/build_aggro_cleanup_candidate.py` verifies
every retained source fingerprint before applying exactly five changed files.
It builds only the zone target and never installs or restarts anything.
`native-build-manifest.json`, when present, records the completed build and
changed-source inventory. [QA.md](QA.md) defines the remaining gameplay gate.

## Rollout and recovery boundary

This requires a rebuilt zone executable. Quest/rule reload cannot apply it.
There are no new world rules, cache ABI, SQL or client changes. Production's
supervisor restarts the whole runtime when a native child exits: do not kill
one zone to deploy or test this candidate.

After owner authorization, use a release-specific guarded maintenance procedure:
verify the current live baseline again, retain a fresh stopped backup, preserve
player/custom/content/cache/client state, install the candidate zone into an
immutable successor image, and verify every worker plus health before reopening.
Keep the prior image for binary-only recovery. Do not delete zone state, repop
the dungeon, restore player snapshots or clear other players' hate to prove a fix.
Existing displaced NPCs in a running process need a supported natural unload
and reload for the corrected restoration path to take effect.

## Whole-wiki review

The current maintained wiki includes the concurrent October 24 Hole keyless
release, source `66c7b843` in `E:/EQ_Local_Dev/_worktrees/hole-keyless-wiki`.
The gameplay checkout's wiki is older. Run that checkout's
`wiki/check_refresh.py --repo E:/EQ_Local_Dev/_worktrees/aggro-zone-cleanup
--ref HEAD --include-worktree`. It correctly reports review required for this
candidate; the ledger must not be advanced without review.

Combat/death, Travel, Dungeon modes, Features, home, commands, Recent changes,
all other maintained guides and generated item/zone/reward pages were assessed.
Current public mechanics, command names, catalogs, reward values and live-testing
labels do not change while this candidate remains uninstalled. No public page
is being represented as updated or published. On authorized deployment, update
Combat/Travel/Dungeon guidance and Recent changes together, review Features/home
for release visibility, retain normal fresh-aggro expectations, and verify any
authorized publication separately. No private incident data belongs in public
articles or generated pages.

## Fresh-instance train follow-up

Independent review found no additional custom defect in `CheckWillAggro` or
`AIYellForHelp`. Raid changes HP/damage, not assistance range. Existing assistance
checks range and LOS from helper to calling NPC, rather than helper to player.
A moving attacker can therefore recruit NPCs distant from the player; periodic
checks and replenishing caller limits permit later joins. This is a mechanism,
not a claim that the available logs establish each recruitment.

Before another gameplay change, capture the first hate-add trigger, NPC spawn
IDs, caller/helper/player coordinates, faction/range values and native LOS at
recruitment in a controlled fresh Lower Guk Raid. Do not alter difficulty,
assistance, leashing or idle timing merely to make the observed train disappear.
