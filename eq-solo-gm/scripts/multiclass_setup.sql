-- =============================================================================
-- Multiclass System Setup
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < multiclass_setup.sql
-- =============================================================================

-- 1. Character multiclass tracking
-- id auto_increment is required: the compiled zone binary (SetMulticlassSlot in aa.cpp)
-- does SELECT id to check row existence before deciding INSERT vs UPDATE.
CREATE TABLE IF NOT EXISTS character_multiclass (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    character_id    INT UNSIGNED NOT NULL,
    class2          TINYINT UNSIGNED NULL DEFAULT NULL,
    class3          TINYINT UNSIGNED NULL DEFAULT NULL,
    applied_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_character_id (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 2. NPC Types
-- Race reference: 1=Human, 3=Erudite, 10=Halfling, 15=High Elf
-- Class reference: 1=Warrior, 2=Cleric, 12=Wizard
-- Gender: 0=Male, 1=Female, 2=Neutral
-- merchant_id: links to merchantlist.merchantid (0 = no merchant)
-- =============================================================================

INSERT INTO npc_types
    (id, name, level, race, `class`, bodytype, hp, mana, gender,
     texture, helmtexture, size, loottable_id, merchant_id,
     npc_spells_id, npc_faction_id, mindmg, maxdmg, npcspecialattks,
     special_abilities, d_melee_texture1, d_melee_texture2,
     prim_melee_type, sec_melee_type, runspeed, lastname)
VALUES
-- The Ancient Chronicler (quest hub - no merchant)
(999220, 'The_Ancient_Chronicler', 65, 3, 12, 1,
 100000, 100000, 0, 2, 0, 6.0, 0, 0,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Ancient Chronicler'),

-- Keeper of Arcane Tomes (Pure Caster spells: Nec/Wiz/Mag/Enc)
(999221, 'Keeper_of_Arcane_Tomes', 65, 3, 12, 1,
 100000, 100000, 2, 2, 0, 6.0, 0, 99221,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Pure Arcana'),

-- Keeper of Sacred Rites (Priest spells: Clr/Dru/Shm)
(999222, 'Keeper_of_Sacred_Rites', 65, 15, 2, 1,
 100000, 100000, 1, 2, 0, 6.0, 0, 99222,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Sacred Rites'),

-- Keeper of Martial Disciplines (Hybrid spells: Pal/Rng/SK/Brd/Bst)
(999223, 'Keeper_of_Martial_Disciplines', 65, 1, 3, 1,
 100000, 50000, 0, 2, 0, 6.0, 0, 99223,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Martial Arts'),

-- Provisions Keeper (food/drink - static stock)
(999224, 'Provisions_Keeper', 40, 10, 1, 1,
 50000, 0, 1, 0, 0, 5.5, 0, 99224,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Provisions')

ON DUPLICATE KEY UPDATE
    name         = VALUES(name),
    merchant_id  = VALUES(merchant_id),
    lastname     = VALUES(lastname);

-- =============================================================================
-- 3. Spawn Groups
-- =============================================================================

INSERT IGNORE INTO spawngroup
    (id, name, spawn_limit, dist, max_x, min_x, max_y, min_y, delay, mindelay, despawn, despawn_timer)
VALUES
    (999220, 'PoK_AncientChronicler',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999221, 'PoK_KeeperArcaneTomes',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999222, 'PoK_KeeperSacredRites',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999223, 'PoK_KeeperMartialDisc',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999224, 'PoK_ProvisionsKeeper',      1, 0, 0, 0, 0, 0, 0, 15000, 0, 100);

-- =============================================================================
-- 4. Spawn Group Entries
-- =============================================================================

INSERT IGNORE INTO spawnentry (spawngroupID, npcID, chance)
VALUES
    (999220, 999220, 100),
    (999221, 999221, 100),
    (999222, 999222, 100),
    (999223, 999223, 100),
    (999224, 999224, 100);

-- =============================================================================
-- 5. Spawn2 — Zone Placement
--
-- !! PLACEHOLDER COORDINATES — must be adjusted in-game !!
-- Stand where you want each NPC and use /loc to get coordinates, then run:
--   UPDATE spawn2 SET x=<X>, y=<Y>, z=<Z>, heading=<H>
--   WHERE spawngroupID IN (999220,999221,999222,999223,999224);
--
-- Intended layout (top-down view, near PoK library entrance):
--
--   [Arcane Tomes]  [The Ancient Chronicler]  [Sacred Rites]
--                   [Martial Disciplines]
--                   [Provisions Keeper]
--
-- Heading: 0-511 in EQEmu (256 = facing West approx)
-- =============================================================================

INSERT IGNORE INTO spawn2
    (spawngroupID, zone, version, x, y, z, heading, respawntime, variance, pathgrid, animation)
VALUES
    (999220, 'poknowledge', 0, -290, -135, -10, 0, 86400, 0, 0, 0),
    (999221, 'poknowledge', 0, -310, -135, -10, 0, 86400, 0, 0, 0),
    (999222, 'poknowledge', 0, -270, -135, -10, 0, 86400, 0, 0, 0),
    (999223, 'poknowledge', 0, -290, -155, -10, 0, 86400, 0, 0, 0),
    (999224, 'poknowledge', 0, -290, -115, -10, 0, 86400, 0, 0, 0);

-- =============================================================================
-- 6. Provisions Vendor Stock (static — common food/drink items)
-- Item type 14=Food, 15=Drink. Adjust if item IDs differ in your DB.
-- The GM tool's /api/vendors/refresh endpoint populates spell vendor stock.
-- =============================================================================

DELETE FROM merchantlist WHERE merchantid = 99224;

SET @pslot = 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99224, (@pslot := @pslot + 1), id, -100, 0, 0, 65535, 100
FROM items
WHERE itemtype IN (14, 15)
  AND nodrop = 0
  AND price BETWEEN 1 AND 10000
ORDER BY name
LIMIT 100;

-- =============================================================================
-- Done. Next steps:
--   1. Run /api/vendors/refresh in the GM tool to populate spell vendor stock
--   2. In-game: stand at desired NPC locations, use /loc, then UPDATE spawn2
--   3. After adjusting spawn2: #repop in PoK or restart zone
-- =============================================================================
