-- =============================================================================
-- Archetype spell vendor restock (Loremasters 99221-99224) — era-aware, idempotent
--
-- Stocks each vendor with every scroll (itemtype 20, scrolleffect -> spells_new)
-- whose spell is scribable by the archetype's classes at or below the CURRENT
-- level cap (Character:MaxLevel rule — follows era.json via apply-era.ps1).
--
-- History: the GM tool's /api/vendors/refresh queried nonexistent columns
-- (items.spellid / items.expansion) AFTER deleting stock — it wiped vendor
-- 99221 during the 2026-07-13 era apply. This script is the durable restock.
--
-- Class columns: Caster 99221 (Nec11 Wiz12 Mag13 Enc14), Priest 99222
-- (Clr2 Dru6 Shm10), Melee 99223 (Rng4 Brd8 Bst15), Tank 99224 (Pal3 Shd5).
-- Pure-melee classes have no scrolls; groups match the June 2026 vendor design.
--
-- Apply: docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < vendor_restock.sql
-- Then restart the PoK zone (merchantlist is cached at zone boot).
-- =============================================================================

SET @cap = (SELECT CAST(rule_value AS UNSIGNED) FROM rule_values
            WHERE rule_name = 'Character:MaxLevel' AND ruleset_id = 1 LIMIT 1);

-- Caster: Necromancer, Wizard, Magician, Enchanter
DELETE FROM merchantlist WHERE merchantid = 99221;
INSERT INTO merchantlist (merchantid, slot, item)
SELECT 99221, ROW_NUMBER() OVER (ORDER BY i.Name, i.id), i.id
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.itemtype = 20 AND i.scrolleffect > 0
  -- one scroll per spell: PEQ ships several item copies of the same scroll
  -- (one per original class vendor); without this the vendor shows dupes (#9)
  AND i.id = (SELECT MIN(i2.id) FROM items i2
              WHERE i2.scrolleffect = i.scrolleffect AND i2.itemtype = 20)
  AND LEAST(
        IF(sn.classes11 BETWEEN 1 AND 254, sn.classes11, 255),
        IF(sn.classes12 BETWEEN 1 AND 254, sn.classes12, 255),
        IF(sn.classes13 BETWEEN 1 AND 254, sn.classes13, 255),
        IF(sn.classes14 BETWEEN 1 AND 254, sn.classes14, 255)) <= @cap;

-- Priest: Cleric, Druid, Shaman
DELETE FROM merchantlist WHERE merchantid = 99222;
INSERT INTO merchantlist (merchantid, slot, item)
SELECT 99222, ROW_NUMBER() OVER (ORDER BY i.Name, i.id), i.id
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.itemtype = 20 AND i.scrolleffect > 0
  -- one scroll per spell: PEQ ships several item copies of the same scroll
  -- (one per original class vendor); without this the vendor shows dupes (#9)
  AND i.id = (SELECT MIN(i2.id) FROM items i2
              WHERE i2.scrolleffect = i.scrolleffect AND i2.itemtype = 20)
  AND LEAST(
        IF(sn.classes2  BETWEEN 1 AND 254, sn.classes2,  255),
        IF(sn.classes6  BETWEEN 1 AND 254, sn.classes6,  255),
        IF(sn.classes10 BETWEEN 1 AND 254, sn.classes10, 255)) <= @cap;

-- Melee: Ranger, Bard, Beastlord
DELETE FROM merchantlist WHERE merchantid = 99223;
INSERT INTO merchantlist (merchantid, slot, item)
SELECT 99223, ROW_NUMBER() OVER (ORDER BY i.Name, i.id), i.id
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.itemtype = 20 AND i.scrolleffect > 0
  -- one scroll per spell: PEQ ships several item copies of the same scroll
  -- (one per original class vendor); without this the vendor shows dupes (#9)
  AND i.id = (SELECT MIN(i2.id) FROM items i2
              WHERE i2.scrolleffect = i.scrolleffect AND i2.itemtype = 20)
  AND LEAST(
        IF(sn.classes4  BETWEEN 1 AND 254, sn.classes4,  255),
        IF(sn.classes8  BETWEEN 1 AND 254, sn.classes8,  255),
        IF(sn.classes15 BETWEEN 1 AND 254, sn.classes15, 255)) <= @cap;

-- Tank: Paladin, Shadow Knight
DELETE FROM merchantlist WHERE merchantid = 99224;
INSERT INTO merchantlist (merchantid, slot, item)
SELECT 99224, ROW_NUMBER() OVER (ORDER BY i.Name, i.id), i.id
FROM items i JOIN spells_new sn ON sn.id = i.scrolleffect
WHERE i.itemtype = 20 AND i.scrolleffect > 0
  -- one scroll per spell: PEQ ships several item copies of the same scroll
  -- (one per original class vendor); without this the vendor shows dupes (#9)
  AND i.id = (SELECT MIN(i2.id) FROM items i2
              WHERE i2.scrolleffect = i.scrolleffect AND i2.itemtype = 20)
  AND LEAST(
        IF(sn.classes3 BETWEEN 1 AND 254, sn.classes3, 255),
        IF(sn.classes5 BETWEEN 1 AND 254, sn.classes5, 255)) <= @cap;

SELECT merchantid, COUNT(*) AS stocked FROM merchantlist
WHERE merchantid BETWEEN 99221 AND 99224 GROUP BY merchantid;
