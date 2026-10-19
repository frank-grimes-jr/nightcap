DELIMITER //
CREATE PROCEDURE nightcap_pet_content_20261018()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='loottable_entries' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='loottable_entries') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected content storage'; END IF;
 IF EXISTS (SELECT 1 FROM loottable_entries WHERE lootdrop_id=988610) THEN
  IF (SELECT COUNT(*) FROM loottable_entries WHERE `loottable_id` <=> 13516 AND `lootdrop_id` <=> 988610 AND `multiplier` <=> 1 AND `droplimit` <=> 1 AND `mindrop` <=> 1 AND `probability` <=> 100)<>1 OR (SELECT COUNT(*) FROM loottable_entries WHERE lootdrop_id=988610)<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Fragment acquisition drift'; END IF;
  DELETE FROM loottable_entries WHERE `loottable_id` <=> 13516 AND `lootdrop_id` <=> 988610 AND `multiplier` <=> 1 AND `droplimit` <=> 1 AND `mindrop` <=> 1 AND `probability` <=> 100;
 END IF;
 COMMIT;
END//
DELIMITER ;
CALL nightcap_pet_content_20261018();
DROP PROCEDURE nightcap_pet_content_20261018;
