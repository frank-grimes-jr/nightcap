-- Candidate only. No --force. Backup, locks and global reload: README.md.
-- A failed CALL leaves this named helper for receipt-aware cleanup.
DELIMITER //
CREATE PROCEDURE nightcap_aa_cost_20261021_rollback()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  SELECT ruleset_id,rule_name,rule_value FROM rule_values
    WHERE rule_name IN ('AA:ExpPerPoint','AA:PassiveExpPercent',
      'AA:NormalizedAAEnabled','AA:ModernAAScalingEnabled') FOR UPDATE;
  IF (SELECT COUNT(*) FROM rule_sets WHERE ruleset_id=1 AND name='default') <> 1
    OR COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default') <> 'default'
    OR (SELECT COUNT(*) FROM rule_values WHERE rule_name IN
      ('AA:ExpPerPoint','AA:PassiveExpPercent','AA:NormalizedAAEnabled','AA:ModernAAScalingEnabled')) <> 4
    OR (SELECT COUNT(*) FROM rule_values WHERE ruleset_id=1 AND
      ((rule_name='AA:ExpPerPoint' AND BINARY rule_value='40000')
      OR (rule_name='AA:PassiveExpPercent' AND BINARY rule_value='10')
      OR (rule_name='AA:NormalizedAAEnabled' AND BINARY rule_value='false')
      OR (rule_name='AA:ModernAAScalingEnabled' AND BINARY rule_value='false'))) <> 4
  THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='AA pacing baseline drift; no rule changed';
  END IF;
  UPDATE rule_values SET rule_value='4000'
    WHERE ruleset_id=1 AND rule_name='AA:ExpPerPoint' AND BINARY rule_value='40000';
  IF ROW_COUNT() <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Expected exactly one AA pacing rule change';
  END IF;
  COMMIT;
END//
DELIMITER ;
CALL nightcap_aa_cost_20261021_rollback();
DROP PROCEDURE nightcap_aa_cost_20261021_rollback;
