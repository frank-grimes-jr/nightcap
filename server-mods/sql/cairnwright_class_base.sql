-- Classic prototype uses the Shaman health, mana and endurance curve (chain/WIS).
-- Run the batch on one connection. Each data insert is a single InnoDB statement.
CREATE TEMPORARY TABLE crw_base_shape (ok INT NOT NULL CHECK (ok = 1));
INSERT INTO crw_base_shape
SELECT COUNT(*) = 50 AND MIN(level) = 1 AND MAX(level) = 50
FROM base_data WHERE class = 10 AND level BETWEEN 1 AND 50;

INSERT INTO crw_base_shape
SELECT COUNT(*) = 0 FROM base_data c
LEFT JOIN base_data s ON s.class = 10 AND s.level = c.level
WHERE c.class = 17 AND c.level BETWEEN 1 AND 50
AND NOT ((c.hp, c.mana, c.end, c.hp_regen, c.end_regen, c.hp_fac, c.mana_fac, c.end_fac)
     <=> (s.hp, s.mana, s.end, s.hp_regen, s.end_regen, s.hp_fac, s.mana_fac, s.end_fac));

INSERT INTO base_data (level, class, hp, mana, end, hp_regen, end_regen, hp_fac, mana_fac, end_fac)
SELECT s.level, 17, s.hp, s.mana, s.end, s.hp_regen, s.end_regen, s.hp_fac, s.mana_fac, s.end_fac
FROM base_data s LEFT JOIN base_data c ON c.class = 17 AND s.level = c.level
WHERE s.class = 10 AND s.level BETWEEN 1 AND 50 AND c.level IS NULL;
DROP TEMPORARY TABLE crw_base_shape;
