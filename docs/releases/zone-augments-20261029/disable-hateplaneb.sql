-- Run offline with the paired augment-capable zone binary and a fresh backup.
-- Rollback disables Hate B acquisition; all earned items/receipts remain.
DELIMITER //
CREATE PROCEDURE nightcap_hate_augments_disable_20261029()
BEGIN
 DECLARE state_revision BIGINT DEFAULT 0;
 DECLARE zone_enabled INT DEFAULT -1;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT revision INTO state_revision FROM nightcap_zone_hunt_state WHERE id=1 AND enabled=1 FOR UPDATE;
 IF state_revision<>2026100901 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hunt state drift'; END IF;
 SELECT enabled INTO zone_enabled FROM nightcap_zone_hunt_zones
  WHERE zone_id=186 AND augment_base=940592 AND gear_base=940596 AND min_level=46 AND night_only=0 FOR UPDATE;
 IF zone_enabled<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hate B configuration drift or replay'; END IF;
 IF EXISTS(SELECT 1 FROM nightcap_zone_hunt_sources WHERE zone_id=186) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hate B equipment sources require separate review'; END IF;
 IF (SELECT COUNT(*) FROM items WHERE id BETWEEN 940592 AND 940599)<>8 OR
  (SELECT COUNT(*) FROM items WHERE id=940592 AND BINARY Name=BINARY 'Blackspire Prism' AND augtype=2097152)<>1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hate B item definitions drift'; END IF;
 UPDATE nightcap_zone_hunt_zones SET enabled=0 WHERE zone_id=186 AND enabled=1;
 IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hate B update conflict'; END IF;
 COMMIT;
END//
DELIMITER ;
CALL nightcap_hate_augments_disable_20261029();
DROP PROCEDURE nightcap_hate_augments_disable_20261029;
