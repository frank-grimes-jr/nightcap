-- =============================================================================
-- Waypoints (#32) — one discoverable waypoint per Classic zone.
--
--   * Dungeons (castoutdoor = 0): waypoint at the zone safe point (zone-in).
--   * Outdoor/city zones: waypoint at the spawn2 point farthest from the safe
--     point — deterministic "randomly placed", and spawn points are guaranteed
--     valid ground. ponytail: hand-tune individual rows in nightcap_waypoints
--     later if a spot turns out ugly; discovery reads the table, not this file.
--   * Visible marker: NPC "a waypoint" (999240, human — the only model loaded
--     in every zone) spawned at each waypoint via ONE shared spawngroup.
--   * Discovery: global_player.pl proximity timer writes
--     nightcap_character_waypoints; all waypoints => title "the Explorer"
--     (title_set 100).
--   * Return travel: Waypoint_Master (999239) in PoK at (370,290).
--
-- IDs: NPCs 999239-999240, spawngroups 999239-999240, title_set 100
-- (verified free 2026-07-16). Non-era stragglers tagged expansion 0 in PEQ
-- (tutorial, cshome, arena, etc.) are excluded so the title stays earnable.
--
-- Apply: docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < waypoints_setup.sql
--        then restart zones (new spawns need #repop; npc_types need restart).
-- =============================================================================

CREATE TABLE IF NOT EXISTS nightcap_waypoints (
  zone     VARCHAR(32) NOT NULL PRIMARY KEY,
  zone_id  INT NOT NULL,
  x        FLOAT NOT NULL,
  y        FLOAT NOT NULL,
  z        FLOAT NOT NULL,
  heading  FLOAT NOT NULL DEFAULT 0,
  is_dungeon TINYINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS nightcap_character_waypoints (
  character_id INT NOT NULL,
  zone         VARCHAR(32) NOT NULL,
  discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (character_id, zone)
);

-- ---- populate waypoints (re-runnable; discoveries keyed by zone survive) ----
DELETE FROM nightcap_waypoints;

-- dungeons: safe point
INSERT INTO nightcap_waypoints (zone, zone_id, x, y, z, heading, is_dungeon)
SELECT z.short_name, z.zoneidnumber, z.safe_x, z.safe_y, z.safe_z, z.safe_heading, 1
FROM zone z
WHERE z.version = 0 AND z.expansion = 0 AND z.castoutdoor = 0
  AND z.short_name NOT IN ('cshome','arena','tutoriala','tutorialb','shadowrest','nedaria','jaggedpine','hateplaneb');

-- outdoor/city: farthest spawn point from the safe point (fallback: safe point)
INSERT INTO nightcap_waypoints (zone, zone_id, x, y, z, heading, is_dungeon)
SELECT z.short_name, z.zoneidnumber,
  COALESCE((SELECT s.x FROM spawn2 s WHERE s.zone = z.short_name AND s.version = 0
            ORDER BY POW(s.x - z.safe_x, 2) + POW(s.y - z.safe_y, 2) DESC LIMIT 1), z.safe_x),
  COALESCE((SELECT s.y FROM spawn2 s WHERE s.zone = z.short_name AND s.version = 0
            ORDER BY POW(s.x - z.safe_x, 2) + POW(s.y - z.safe_y, 2) DESC LIMIT 1), z.safe_y),
  COALESCE((SELECT s.z FROM spawn2 s WHERE s.zone = z.short_name AND s.version = 0
            ORDER BY POW(s.x - z.safe_x, 2) + POW(s.y - z.safe_y, 2) DESC LIMIT 1), z.safe_z),
  0, 0
FROM zone z
WHERE z.version = 0 AND z.expansion = 0 AND z.castoutdoor = 1
  AND z.short_name NOT IN ('cshome','arena','tutoriala','tutorialb','shadowrest','nedaria','jaggedpine','hateplaneb');

-- ---- marker NPC + Waypoint Master ----
DELETE FROM npc_types WHERE id IN (999239, 999240);
INSERT INTO npc_types (id, name, lastname, level, race, class, bodytype, hp, gender, texture, helmtexture, size, runspeed, loottable_id, merchant_id, npc_faction_id)
VALUES
  (999240, 'a_waypoint', 'Stand Here to Attune', 60, 1, 1, 1, 60000, 0, 0, 0, 8, 0, 0, 0, 0);

-- Waypoint Master: clone a QA-proven PoK appearance (Chronicler, race 82)
DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999220;
UPDATE t_npc SET id=999239, name='Waypoint_Master', lastname='Waypoint Travel', class=1, merchant_id=0;
INSERT INTO npc_types SELECT * FROM t_npc;
DROP TEMPORARY TABLE IF EXISTS t_npc;

-- ---- spawns: one spawngroup for all markers, one for the master ----
DELETE FROM spawn2 WHERE spawngroupID IN (999239, 999240);
DELETE FROM spawnentry WHERE spawngroupID IN (999239, 999240);
DELETE FROM spawngroup WHERE id IN (999239, 999240);

INSERT INTO spawngroup (id,name,spawn_limit,dist,max_x,min_x,max_y,min_y,delay,mindelay,despawn,despawn_timer) VALUES
  (999239,'PoK_WaypointMaster',1,0,0,0,0,0,0,15000,0,100),
  (999240,'Nightcap_WaypointMarkers',0,0,0,0,0,0,0,15000,0,100);

INSERT INTO spawnentry (spawngroupID,npcID,chance) VALUES
  (999239,999239,100),(999240,999240,100);

INSERT INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime,variance,pathgrid,animation)
VALUES (999239,'poknowledge',0,370,290,-125,128,86400,0,0,0);

INSERT INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime,variance,pathgrid,animation)
SELECT 999240, w.zone, 0, w.x, w.y, w.z, w.heading, 60, 0, 0, 0
FROM nightcap_waypoints w;

-- ---- title ----
DELETE FROM titles WHERE title_set = 100;
INSERT INTO titles (skill_id,min_skill_value,max_skill_value,min_aa_points,max_aa_points,class,gender,char_id,status,item_id,prefix,suffix,title_set)
VALUES (-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,'','the Explorer',100);

SELECT COUNT(*) AS waypoints, SUM(is_dungeon) AS dungeons FROM nightcap_waypoints;
