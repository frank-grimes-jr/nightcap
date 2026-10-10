-- Run inside the deployment runner's guarded transaction, after Crushbone unloads.
-- Move the marker and recall destination together; preserve all discoveries.
UPDATE nightcap_waypoints
SET x=158, y=-644, z=4, heading=0, is_dungeon=1
WHERE zone='crushbone' AND zone_id=58
  AND x=610 AND y=292 AND z=2 AND heading=0 AND is_dungeon=0;

UPDATE spawn2
SET x=158, y=-644, z=4, heading=0
WHERE id=3266061 AND spawngroupID=999240 AND zone='crushbone' AND version=0
  AND x=610 AND y=292 AND z=2 AND heading=0;

-- Keep saved-state identity, HP, loot, buffs and all unrelated NPC/corpse states.
UPDATE zone_state_spawns
SET x=158, y=-644, z=4, heading=0
WHERE zone_id=58 AND instance_id=0 AND is_corpse=0 AND is_zone=0
  AND npc_id IN (0,999240) AND spawn2_id=3266061 AND spawngroup_id=999240;
