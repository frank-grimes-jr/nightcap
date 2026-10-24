# Exact gameplay QA — candidate only

Run after the candidate is installed in an authorized test environment. Record
the binary hash, zone/instance, NPC spawn IDs, coordinates and times. Keep public
Lower Guk and Keeper Raid/Grind runs distinct. Native fixture success is not
completed owner gameplay or balance acceptance.

1. **Original bedroom route:** enter Lower Guk (`gukbottom`, zone 66) on Palwar.
   Record whether entry is public or through a Keeper, plus the instance ID.
   Approach the bedroom camp; identify the gargoyle/skeleton/froglok train and
   record its origin, pull point, and Extended Targets. Pull deliberately, die,
   return, then repeat with a successful zone-out and a completed logout.
   Before approaching their current positions, old hate must not reappear.
   Approaching normal hostile aggro range can create a new fight and is not by
   itself a failure. Capture the NPC hate/target state if the group returns.
2. **Feign memory:** use the held Monk feign ability while NPCs remember Palwar.
   Test accepted death while memory remains and successful zone-out/logout.
   Re-enter; the old memory must not attach to Palwar or another client through
   an entity-ID reuse. Include a second player retaining a separate engagement:
   their hate, damage credit and remembered feign must remain. A resisted/vetoed
   death or failed zone request must not grant a free memory wipe.
3. **Stationary return home after natural unload:** in a disposable test zone
   or managed Raid instance with supported checkpoints, pull one stationary NPC far from its
   canonical spawn. Let the zone unload naturally while its saved position is
   displaced; do not terminate a production zone child. Reload and verify the
   saved NPC resumes at that position and eventually returns to its original
   home once idle. Its existing loot and resource state must not reroll/reset.
   Compare the canonical spawn and actual guard point to distinguish a pathing
   obstruction from a wrong home position. The guard must match a fresh spawn's
   ground-corrected home, including in multi-floor and water areas. Include
   roambox NPCs as an unchanged control.
4. **Preservation controls:** verify a roaming NPC resumes its saved waypoint,
   a player/NPC corpse stays at the death location, a killed NPC retains its
   respawn timer, and a quest-created actor retains its scripted behavior. Check
   ordinary feign/stand-up, memory blur/fading and normal new social aggro. For
   a Keeper dungeon, confirm recorded kills/journal/reward progress persist.
5. **Empty-zone timing:** allow the empty-zone 60-second idle pause, then return
   and observe resumed movement. This candidate does not extend idle processing
   or instantly send trains home. Record long or blocked return routes as a
   separate pathing/settling issue rather than claiming stale hate from proximity.

Acceptance remains open until the owner reports these results. Main promotion
and production deployment require current owner approval under AGENTS.md.
