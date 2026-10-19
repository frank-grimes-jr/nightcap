DELIMITER //
CREATE PROCEDURE nightcap_wpm_items_20261018()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='loottable_entries' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='loottable_entries') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected WPM content storage'; END IF;
 IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988620)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988620 AND NOT (FALSE))) THEN
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988620)=1 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988620 AND NOT ((`loottable_id` <=> 13335 AND `lootdrop_id` <=> 988620 AND `multiplier` <=> 1 AND `droplimit` <=> 1 AND `mindrop` <=> 1 AND `probability` <=> 100)))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries preimage drift'; END IF;
  DELETE FROM loottable_entries WHERE `lootdrop_id` <=> 988620;
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988620)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988620 AND NOT (FALSE))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries afterimage mismatch'; END IF;
 END IF;
 IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988621)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988621 AND NOT (FALSE))) THEN
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988621)=1 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988621 AND NOT ((`loottable_id` <=> 104959 AND `lootdrop_id` <=> 988621 AND `multiplier` <=> 1 AND `droplimit` <=> 1 AND `mindrop` <=> 1 AND `probability` <=> 100)))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries preimage drift'; END IF;
  DELETE FROM loottable_entries WHERE `lootdrop_id` <=> 988621;
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988621)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988621 AND NOT (FALSE))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries afterimage mismatch'; END IF;
 END IF;
 IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988622)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988622 AND NOT (FALSE))) THEN
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988622)=1 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988622 AND NOT ((`loottable_id` <=> 13516 AND `lootdrop_id` <=> 988622 AND `multiplier` <=> 1 AND `droplimit` <=> 1 AND `mindrop` <=> 1 AND `probability` <=> 100)))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries preimage drift'; END IF;
  DELETE FROM loottable_entries WHERE `lootdrop_id` <=> 988622;
  IF NOT ((SELECT COUNT(*) FROM loottable_entries WHERE `lootdrop_id` <=> 988622)=0 AND NOT EXISTS (SELECT 1 FROM loottable_entries WHERE `lootdrop_id` <=> 988622 AND NOT (FALSE))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM loottable_entries afterimage mismatch'; END IF;
 END IF;
 COMMIT;
END//
DELIMITER ;
CALL nightcap_wpm_items_20261018();
DROP PROCEDURE nightcap_wpm_items_20261018;
