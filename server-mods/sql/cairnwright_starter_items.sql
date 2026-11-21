-- Creation-only robe and one-handed hammer. Follow the Nightcap initiate
-- stat budget. Use a separate connection with stop-on-error enabled.
CREATE TEMPORARY TABLE crw_kit LIKE items;
CREATE TEMPORARY TABLE crw_kit_check (ok INT NOT NULL CHECK (ok = 1));
INSERT INTO crw_kit SELECT * FROM items WHERE
    (id = 1060 AND name = 'Teir`Dal Robe Red' AND slots = 131072 AND itemtype = 10)
 -- Production's Rusty Warhammer has 2 damage. The local PEQ template has 4.
 OR (id = 6014 AND name = 'Rusty Warhammer' AND itemtype = 3 AND damage IN (2, 4) AND delay = 30);
INSERT INTO crw_kit_check SELECT COUNT(*) = 2 FROM crw_kit;
UPDATE crw_kit SET classes = 65536, races = 65535, deity = 0, nodrop = 0,
    price = 0, reqlevel = 0, reclevel = 0, weight = 10;
UPDATE crw_kit SET id = 998616, name = 'Initiate Cairnwright Robe', ac = 10, awis = 5 WHERE id = 1060;
UPDATE crw_kit SET id = 998636, name = 'Initiate Cairnwright Hammer', slots = 8192,
    damage = 6, delay = 30 WHERE id = 6014;
INSERT INTO crw_kit_check
SELECT COUNT(*) = 0 FROM items i JOIN crw_kit k ON k.name = i.name AND i.id <> k.id;
INSERT INTO crw_kit_check SELECT COUNT(*) = 0 FROM
(SELECT i.* FROM items i JOIN crw_kit k ON k.id = i.id EXCEPT SELECT * FROM crw_kit) changed;
INSERT INTO items SELECT k.* FROM crw_kit k LEFT JOIN items i ON i.id = k.id WHERE i.id IS NULL;
DROP TEMPORARY TABLE crw_kit_check, crw_kit;
