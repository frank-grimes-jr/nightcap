-- =============================================================================
-- Instance Keeper NPCs
--
-- Places an "Instance_Keeper" NPC at the entrance of each instancable dungeon.
-- The NPC's lastname stores the short name of the zone it creates instances for.
-- Quest script: akk-stack/server/quests/global/Instance_Keeper.pl
--
-- IDs 999227-999233 (npc_types AND spawngroup) — the Nightcap custom range.
-- !! Before reusing a range, PROVE it is free in BOTH tables:
--      SELECT id FROM npc_types  WHERE id BETWEEN <lo> AND <hi>;
--      SELECT id FROM spawngroup WHERE id BETWEEN <lo> AND <hi>;
--    The original version of this script used 998xxx, which collided with
--    existing NPCs (a_swooping_bat) — and its ON DUPLICATE KEY / INSERT IGNORE
--    clauses masked the collision instead of failing. Plain INSERTs below are
--    deliberate: a collision must ERROR, not silently corrupt.
--
-- To add more zones:
--   1. Verify a free ID in both tables (query above)
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
    (999227, 'Instance_Keeper', 'befallen',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999228, 'Instance_Keeper', 'unrest',      50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999229, 'Instance_Keeper', 'highkeep',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999230, 'Instance_Keeper', 'najena',      50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999231, 'Instance_Keeper', 'cazicthule',  50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999232, 'Instance_Keeper', 'permafrost',  50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25),
    (999233, 'Instance_Keeper', 'soldungb',    50, 1, 1, 1, 50000, 0, 0, 0, 0, 6.0, 0, 0, 0, 0, 0, 0, '', '', 1.25);

-- Spawn groups (same IDs as their NPC for sanity)
INSERT INTO spawngroup
    (id, name, spawn_limit, dist, max_x, min_x, max_y, min_y, delay, mindelay, despawn, despawn_timer)
VALUES
    (999227, 'InstanceKeeper_befallen',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999228, 'InstanceKeeper_unrest',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999229, 'InstanceKeeper_highkeep',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999230, 'InstanceKeeper_najena',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999231, 'InstanceKeeper_cazic',      1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999232, 'InstanceKeeper_permafrost', 1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999233, 'InstanceKeeper_soldungb',   1, 0, 0, 0, 0, 0, 0, 15000, 0, 100);

-- Spawn entries
INSERT INTO spawnentry (spawngroupID, npcID, chance) VALUES
    (999227, 999227, 100),
    (999228, 999228, 100),
    (999229, 999229, 100),
    (999230, 999230, 100),
    (999231, 999231, 100),
    (999232, 999232, 100),
    (999233, 999233, 100);

-- Spawn2 — placed at each dungeon's zone-in (safe point as starting coords)
-- !! PLACEHOLDER COORDINATES — stand at entrance, use /loc, then UPDATE spawn2 !!
INSERT INTO spawn2
    (spawngroupID, zone, version, x, y, z, heading, respawntime, variance, pathgrid, animation)
VALUES
    (999227, 'befallen',   0,   35,  -82,   3, 0, 86400, 0, 0, 0),
    (999228, 'unrest',     0,   52,  -38,   3, 0, 86400, 0, 0, 0),
    (999229, 'highkeep',   0,   88,  -16,   4, 0, 86400, 0, 0, 0),
    (999230, 'najena',     0,  858,  -76,   4, 0, 86400, 0, 0, 0),
    (999231, 'cazicthule', 0,  -74,   71,   4, 0, 86400, 0, 0, 0),
    (999232, 'permafrost', 0,   61, -121,   2, 0, 86400, 0, 0, 0),
    (999233, 'soldungb',   0, -263, -424, -108, 0, 86400, 0, 0, 0);
