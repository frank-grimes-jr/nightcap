-- Dwarf/Brell, Classic Kaladim choice, with the Nightcap East Commonlands
-- start and bind. Use the reviewed Dwarf wisdom-hybrid allocation.
-- Run as one batch with stop-on-error on a dedicated connection.
CREATE TEMPORARY TABLE crw_creation_check (ok INT NOT NULL CHECK (ok = 1));
START TRANSACTION;
INSERT INTO crw_creation_check
SELECT COUNT(*) = 1 FROM char_create_point_allocations
WHERE id = 14 AND (base_str, base_sta, base_dex, base_agi, base_int, base_wis, base_cha,
                   alloc_str, alloc_sta, alloc_dex, alloc_agi, alloc_int, alloc_wis, alloc_cha)
                 = (100,95,90,70,60,88,55, 0,20,0,0,0,0,0);
INSERT INTO crw_creation_check
SELECT COUNT(*) = 1 FROM char_create_combinations
WHERE race = 8 AND class = 3 AND deity = 202 AND start_zone = 67
AND allocation_id = 14 AND expansions_req = 0;

CREATE TEMPORARY TABLE crw_start LIKE start_zones;
INSERT INTO crw_start SELECT * FROM start_zones
WHERE player_race = 8 AND player_class = 3 AND player_deity = 202
AND zone_id = 22 AND start_zone = 22 AND bind_id = 22;
INSERT INTO crw_creation_check SELECT COUNT(*) = 1 FROM crw_start;
UPDATE crw_start SET player_class = 17;

-- Accept an exact replay. Detect a different class-17 allocation or home.
INSERT INTO crw_creation_check
SELECT COUNT(*) = 0 FROM char_create_combinations WHERE class = 17
AND (race, deity, start_zone, allocation_id, expansions_req) <> (8,202,67,14,0);
INSERT INTO crw_creation_check
SELECT COUNT(*) = 0 FROM
(SELECT * FROM start_zones WHERE player_class = 17 EXCEPT SELECT * FROM crw_start) changed;

INSERT INTO char_create_combinations (allocation_id, race, class, deity, start_zone, expansions_req)
SELECT 14,8,17,202,67,0 WHERE NOT EXISTS
(SELECT 1 FROM char_create_combinations WHERE class = 17);
INSERT INTO start_zones SELECT * FROM crw_start WHERE NOT EXISTS
(SELECT 1 FROM start_zones WHERE player_class = 17);
COMMIT;
DROP TEMPORARY TABLE crw_creation_check, crw_start;
