-- Maintenance only: stop gateway/game, take a fresh backup, verify InnoDB.
-- Execute in one MariaDB connection WITHOUT --force; any error must disconnect
-- and roll back. Do not run individual statements or against running zones.
CREATE TEMPORARY TABLE unrest_waypoint_guard(ok INT NOT NULL CHECK(ok=1)) ENGINE=MEMORY;
START TRANSACTION;
SELECT zone FROM nightcap_waypoints WHERE zone='unrest' FOR UPDATE;
SELECT id FROM spawn2 WHERE id IN (3266123,3266037) FOR UPDATE;
SELECT id FROM zone_state_spawns WHERE zone_id=63 AND instance_id=0
  AND spawn2_id=3266123 AND spawngroup_id=999240 FOR UPDATE;
INSERT INTO unrest_waypoint_guard SELECT COUNT(*)=1 FROM nightcap_waypoints
  WHERE zone='unrest' AND zone_id=63 AND x=118 AND y=881 AND z=3.75 AND heading=0 AND is_dungeon=0;
INSERT INTO unrest_waypoint_guard SELECT COUNT(*)=1 FROM spawn2
  WHERE id=3266123 AND spawngroupID=999240 AND zone='unrest' AND version=0
    AND x=118 AND y=881 AND z=3.75 AND heading=0;
INSERT INTO unrest_waypoint_guard SELECT COUNT(*)=1 FROM spawn2
  WHERE id=3266037 AND spawngroupID=999228 AND zone='unrest' AND version=0
    AND x=52 AND y=-38 AND z=3 AND heading=0;

UPDATE nightcap_waypoints SET x=52,y=-38,z=3,heading=0 WHERE zone='unrest' AND zone_id=63;
UPDATE spawn2 SET x=52,y=-38,z=3,heading=0
  WHERE id=3266123 AND spawngroupID=999240 AND zone='unrest' AND version=0;
-- Preserve all state except pose, including dormant markers (npc_id=0).
UPDATE zone_state_spawns SET x=52,y=-38,z=3,heading=0
  WHERE zone_id=63 AND instance_id=0 AND is_corpse=0 AND is_zone=0
    AND npc_id IN (0,999240) AND spawn2_id=3266123 AND spawngroup_id=999240;
COMMIT;
DROP TEMPORARY TABLE unrest_waypoint_guard;
