-- Candidate data paired with rebuilt world/zone. Existing earned Hunt headroom
-- remains additive. Capture fresh target preimages before stopped deployment.
DELIMITER //
CREATE PROCEDURE nightcap_output_caps_20261018()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()
     AND TABLE_NAME='rule_values' AND ENGINE='InnoDB') <> 1
    OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()
     AND EVENT_OBJECT_TABLE='rule_values') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected output rule storage';
 END IF;
 IF (SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1
     AND rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap')
     AND rule_value IN ('250','750') FOR UPDATE) <> 2 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Shared output cap preimage drift';
 END IF;
 UPDATE rule_values SET rule_value='750' WHERE ruleset_id=1
  AND rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap') AND rule_value='250';
 COMMIT;
END//
DELIMITER ;
CALL nightcap_output_caps_20261018();
DROP PROCEDURE nightcap_output_caps_20261018;
