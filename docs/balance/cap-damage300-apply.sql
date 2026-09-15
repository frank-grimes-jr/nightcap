DELIMITER //
CREATE PROCEDURE `cap_apply_6a634d4ea67f`()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 IF DATABASE() <> 'nightcap_balance_20260912' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Wrong database'; END IF;
 IF EXISTS(SELECT 1 FROM account) OR EXISTS(SELECT 1 FROM character_data) OR EXISTS(SELECT 1 FROM character_alternate_abilities) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Nonempty character fixture'; END IF;
 IF (SELECT COUNT(*) FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap')) <> 2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected cap rule rows'; END IF;
 IF (SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:ItemSpellDmgCap' AND rule_value='250') <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cap precondition changed'; END IF;
 UPDATE rule_values SET rule_value='300' WHERE ruleset_id=1 AND rule_name='Character:ItemSpellDmgCap' AND rule_value='250';
 IF (SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:ItemHealAmtCap' AND rule_value='250') <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cap precondition changed'; END IF;
 COMMIT;
END//
CALL `cap_apply_6a634d4ea67f`()//
DROP PROCEDURE `cap_apply_6a634d4ea67f`//
DELIMITER ;
