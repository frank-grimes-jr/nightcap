-- =============================================================================
-- Instance Keeper NPCs
--
-- Places an "Instance_Keeper" NPC at the entrance of each instancable dungeon.
-- The NPC's lastname stores the short name of the zone it creates instances for.
-- Quest script: akk-stack/server/quests/global/Instance_Keeper.pl
--
-- To add more zones:
--   1. Pick an NPC ID in the 998xxx range (unused)
--   2. Add npc_types, spawngroup, spawnentry, and spawn2 rows
--   3. Set lastname = zone short name
--   4. Use /loc in-game to get accurate coordinates, then UPDATE spawn2
--
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < instance_keeper_setup.sql
-- =============================================================================

-- NPC type template — all Instance Keepers share appearance (Human male, level 50)
-- lastname is the target instance zone short name
INSERT INTO npc_types
    (id, name, lastname, level, race, `class`, bodytype, hp, mana, gender,
     texture, helmtexture, size, loottable_id, merchant_id,
     npc_spells_id, npc_faction_id, mindmg, maxdmg, npcspecialattks,
     special_abilities, runspeed)
VALUES
    (998001, 'Instance_Keeper', 'befallen',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998002, 'Instance_Keeper', 'unrest',      50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998003, 'Instance_Keeper', 'highkeep',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998004, 'Instance_Keeper', 'najena',      50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998005, 'Instance_Keeper', 'cazicthule',  50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998006, 'Instance_Keeper', 'permafrost',  50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (998007, 'Instance_Keeper', 'soldungb',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25)
ON DUPLICATE KEY UPDATE lastname = VALUES(lastname);

-- Spawn groups
INSERT IGNORE INTO spawngroup
    (id, name, spawn_limit, dist, max_x, min_x, max_y, min_y, delay, mindelay, despawn, despawn_timer)
VALUES
    (998001, 'InstanceKeeper_befallen',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998002, 'InstanceKeeper_unrest',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998003, 'InstanceKeeper_highkeep',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998004, 'InstanceKeeper_najena',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998005, 'InstanceKeeper_cazic',      1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998006, 'InstanceKeeper_permafrost', 1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (998007, 'InstanceKeeper_soldungb',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100);

-- Spawn entries
INSERT IGNORE INTO spawnentry (spawngroupID, npcID, chance) VALUES
    (998001, 998001, 100),
    (998002, 998002, 100),
    (998003, 998003, 100),
    (998004, 998004, 100),
    (998005, 998005, 100),
    (998006, 998006, 100),
    (998007, 998007, 100);

-- Spawn2 — placed at each dungeon's zone entrance (adjust with /loc in-game)
-- !! PLACEHOLDER COORDINATES — stand at entrance, use /loc, then UPDATE spawn2 !!
INSERT IGNORE INTO spawn2
    (spawngroupID, zone, version, x, y, z, heading, respawntime, variance, pathgrid, animation)
VALUES
    -- Befallen entrance (West Karana zone line area)
    (998001, 'befallen',   0,   35,  -82,   3, 0, 86400, 0, 0, 0),
    -- Estate of Unrest entrance
    (998002, 'unrest',     0,   52,  -38,   3, 0, 86400, 0, 0, 0),
    -- High Keep entrance
    (998003, 'highkeep',   0,   88,  -16,   4, 0, 86400, 0, 0, 0),
    -- Najena entrance
    (998004, 'najena',     0,  858,  -76,   4, 0, 86400, 0, 0, 0),
    -- Temple of Cazic-Thule entrance
    (998005, 'cazicthule', 0,  -74,   71,   4, 0, 86400, 0, 0, 0),
    -- Permafrost entrance
    (998006, 'permafrost', 0,   61, -121,   2, 0, 86400, 0, 0, 0),
    -- Nagafen's Lair entrance
    (998007, 'soldungb',   0, -263, -424, -108, 0, 86400, 0, 0, 0);

-- =============================================================================
-- To add more zones, copy the pattern above with a new ID in the 998xxx range.
-- Coordinates are pulled from the zone table's safe_x/safe_y/safe_z as a
-- starting point — adjust with /loc after testing in-game.
-- =============================================================================
