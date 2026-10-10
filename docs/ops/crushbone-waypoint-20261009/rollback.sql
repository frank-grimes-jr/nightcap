-- Use the saved preimage to restore any existing marker state exactly.
-- This inverse restores the two durable placement rows only.
UPDATE nightcap_waypoints
SET x=610, y=292, z=2, heading=0, is_dungeon=0
WHERE zone='crushbone' AND zone_id=58
  AND x=158 AND y=-644 AND z=4 AND heading=0 AND is_dungeon=1;

UPDATE spawn2
SET x=610, y=292, z=2, heading=0
WHERE id=3266061 AND spawngroupID=999240 AND zone='crushbone' AND version=0
  AND x=158 AND y=-644 AND z=4 AND heading=0;
