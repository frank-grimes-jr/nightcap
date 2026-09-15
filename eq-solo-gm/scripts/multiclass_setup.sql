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

-- Chronicler model: race 21 = King Xorbb (Beholder / floating-eye model). Chosen
-- because it renders on old/classic graphics (the Sphinx, race 86, is invisible
-- without Luclin models). Vendors are split by the four EQ archetypes
-- (Caster/Priest/Melee/Tank); 999225 is a standalone bag vendor.
INSERT INTO npc_types
    (id, name, level, race, `class`, bodytype, hp, mana, gender,
     texture, helmtexture, size, loottable_id, merchant_id,
     npc_spells_id, npc_faction_id, mindmg, maxdmg, npcspecialattks,
     special_abilities, d_melee_texture1, d_melee_texture2,
     prim_melee_type, sec_melee_type, runspeed, lastname)
VALUES
-- The Ancient Chronicler (multiclass quest hub - no merchant) - King Xorbb model
(999220, 'The_Ancient_Chronicler', 65, 21, 12, 1,
 100000, 100000, 2, 0, 0, 8.0, 0, 0,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Ancient Chronicler'),

-- Arcane Loremaster (Casters: Nec/Wiz/Mag/Enc) - classBits 15360
-- class MUST be 41 (Merchant) or the NPC can't be right-clicked to shop.
(999221, 'Arcane_Loremaster', 65, 3, 41, 1,
 100000, 100000, 2, 2, 0, 6.0, 0, 99221,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Caster Spells'),

-- Divine Loremaster (Priests: Clr/Dru/Shm) - classBits 546
(999222, 'Divine_Loremaster', 65, 5, 41, 1,
 100000, 100000, 1, 2, 0, 6.0, 0, 99222,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Priest Spells'),

-- Martial Loremaster (Melee: Mnk/Rog/Ber/Brd/Rng/Bst) - classBits 49608
(999223, 'Martial_Loremaster', 65, 1, 41, 1,
 100000, 50000, 0, 2, 0, 6.0, 0, 99223,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Melee Tomes'),

-- Stalwart Loremaster (Tanks: War/Pal/SK) - classBits 21
(999224, 'Stalwart_Loremaster', 65, 2, 41, 1,
 100000, 50000, 0, 2, 0, 6.0, 0, 99224,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Tank Spells'),

-- Bag vendor (sells one container of each slot size 8..40)
(999225, 'Bartholomew_Packwell', 60, 1, 41, 1,
 50000, 0, 0, 2, 0, 6.0, 0, 99225,
 0, 0, 0, 0, '', '', 0, 0, 28, 28, 1.25, 'Bags & Containers')

ON DUPLICATE KEY UPDATE
    name         = VALUES(name),
    race         = VALUES(race),
    `class`      = VALUES(`class`),
    gender       = VALUES(gender),
    merchant_id  = VALUES(merchant_id),
    lastname     = VALUES(lastname);

-- =============================================================================
-- 3. Spawn Groups
-- =============================================================================

INSERT IGNORE INTO spawngroup
    (id, name, spawn_limit, dist, max_x, min_x, max_y, min_y, delay, mindelay, despawn, despawn_timer)
VALUES
    (999220, 'PoK_AncientChronicler',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999221, 'PoK_ArcaneLoremaster',      1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999222, 'PoK_DivineLoremaster',      1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999223, 'PoK_MartialLoremaster',     1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999224, 'PoK_StalwartLoremaster',    1, 0, 0, 0, 0, 0, 0, 15000, 0, 100),
    (999225, 'PoK_BagVendor',             1, 0, 0, 0, 0, 0, 0, 15000, 0, 100);

-- =============================================================================
-- 4. Spawn Group Entries
-- =============================================================================

INSERT IGNORE INTO spawnentry (spawngroupID, npcID, chance)
VALUES
    (999220, 999220, 100),
    (999221, 999221, 100),
    (999222, 999222, 100),
    (999223, 999223, 100),
    (999224, 999224, 100),
    (999225, 999225, 100);

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

-- Clustered just forward (south) of Mister Magelo (npc 202388, at 334,287,-125),
-- clear of the tree. Floor z = -125.
INSERT INTO spawn2
    (spawngroupID, zone, version, x, y, z, heading, respawntime, variance, pathgrid, animation)
VALUES
    (999220, 'poknowledge', 0, 340, 262, -125, 128, 86400, 0, 0, 0),
    (999221, 'poknowledge', 0, 325, 264, -125, 128, 86400, 0, 0, 0),
    (999222, 'poknowledge', 0, 332, 256, -125, 128, 86400, 0, 0, 0),
    (999223, 'poknowledge', 0, 348, 256, -125, 128, 86400, 0, 0, 0),
    (999224, 'poknowledge', 0, 355, 264, -125, 128, 86400, 0, 0, 0),
    (999225, 'poknowledge', 0, 340, 248, -125, 128, 86400, 0, 0, 0)
ON DUPLICATE KEY UPDATE x=VALUES(x), y=VALUES(y), z=VALUES(z), heading=VALUES(heading);

-- =============================================================================
-- 6. Spell/Tome Vendor Stock — 4 archetypes, scribe level <= 60 (expansion 1)
--
-- IMPORTANT: the spell id for a scribable scroll is in items.scrolleffect, NOT
-- items.spellid (which does not exist in this DB). There is also no items.expansion
-- column — gate by the spell's scribe level in spells_new.classesN instead.
-- (The GM tool's /api/vendors/refresh used i.spellid/i.expansion and silently
-- failed against this schema, which is why these vendors were empty.)
--
-- spells_new.classesN = min level a class can scribe (255 = never). classBits is
-- the items.classes bitmask: bit = 2^(classId-1).
--   Caster (99221): Nec/Wiz/Mag/Enc      cols 11,12,13,14   bits 15360
--   Priest (99222): Clr/Dru/Shm          cols 2,6,10        bits 546
--   Melee  (99223): Mnk/Rog/Ber/Brd/Rng/Bst cols 4,7,8,9,15,16 bits 49608
--   Tank   (99224): War/Pal/SK           cols 1,3,5         bits 21
-- Pure-melee classes (War/Mnk/Rog/Ber) have no scribable spells at exp 1, so the
-- Melee/Tank vendors stock the hybrid casters (Brd/Rng/Bst / Pal/SK).
-- =============================================================================

DELETE FROM merchantlist WHERE merchantid IN (99221, 99222, 99223, 99224);

SET @s := 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99221, (@s := @s + 1), i.id, -100, 0, 0, 65535, 100
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.scrolleffect > 0 AND (i.classes & 15360) > 0
  AND (sn.classes11 BETWEEN 1 AND 60 OR sn.classes12 BETWEEN 1 AND 60 OR sn.classes13 BETWEEN 1 AND 60 OR sn.classes14 BETWEEN 1 AND 60)
ORDER BY i.name;

SET @s := 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99222, (@s := @s + 1), i.id, -100, 0, 0, 65535, 100
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.scrolleffect > 0 AND (i.classes & 546) > 0
  AND (sn.classes2 BETWEEN 1 AND 60 OR sn.classes6 BETWEEN 1 AND 60 OR sn.classes10 BETWEEN 1 AND 60)
ORDER BY i.name;

SET @s := 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99223, (@s := @s + 1), i.id, -100, 0, 0, 65535, 100
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.scrolleffect > 0 AND (i.classes & 49608) > 0
  AND (sn.classes4 BETWEEN 1 AND 60 OR sn.classes7 BETWEEN 1 AND 60 OR sn.classes8 BETWEEN 1 AND 60 OR sn.classes9 BETWEEN 1 AND 60 OR sn.classes15 BETWEEN 1 AND 60 OR sn.classes16 BETWEEN 1 AND 60)
ORDER BY i.name;

SET @s := 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99224, (@s := @s + 1), i.id, -100, 0, 0, 65535, 100
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.scrolleffect > 0 AND (i.classes & 21) > 0
  AND (sn.classes1 BETWEEN 1 AND 60 OR sn.classes3 BETWEEN 1 AND 60 OR sn.classes5 BETWEEN 1 AND 60)
ORDER BY i.name;

-- =============================================================================
-- 7. Bag vendor (99225) — one container of each distinct slot size, 8..40.
-- bagslots = slot count; pick the best per size (Giant bagsize=4 then highest
-- weight-reduction). nodrop=0 means NO TRADE: the merchant can sell these,
-- but the server rejects selling them back. Do not flip this flag for pricing.
-- =============================================================================

DELETE FROM merchantlist WHERE merchantid = 99225;

SET @bs := 0;
INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability)
SELECT 99225, (@bs := @bs + 1), id, -100, 0, 0, 65535, 100
FROM (
    SELECT id, bagslots,
           ROW_NUMBER() OVER (PARTITION BY bagslots ORDER BY bagsize DESC, bagwr DESC, id ASC) AS rn
    FROM items
    WHERE bagslots BETWEEN 8 AND 40 AND nodrop = 0
) x
WHERE x.rn = 1
ORDER BY x.bagslots;

-- =============================================================================
-- Done. After running this: #repop in PoK (or restart the zone) to spawn/move NPCs.
-- =============================================================================
