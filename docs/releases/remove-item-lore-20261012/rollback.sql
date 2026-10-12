-- Stop gateway/game and take a verified backup first. Run without --force.
-- Existing shared_memory binary applies this rule; startup rebuilds the cache.
-- IMMEDIATE CLOSED-GATE RECOVERY ONLY. After players collect duplicates, restoring
-- LORE can destroy duplicate cursor items. Reconcile owned duplicates first.
DELIMITER //
CREATE PROCEDURE nightcap_restore_lore_20261012()
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
  START TRANSACTION;
  IF (SELECT COUNT(*) FROM rule_sets WHERE ruleset_id=1 AND BINARY name=BINARY 'default') <> 1
     OR EXISTS (SELECT 1 FROM variables WHERE varname IN ('RuleSet','disablelore'))
     OR (SELECT COUNT(*) FROM rule_values WHERE rule_name='Items:DisableLore') <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='LORE policy baseline changed; recapture before activation or recovery';
  END IF;
  UPDATE rule_values SET rule_value='false'
    WHERE ruleset_id=1 AND rule_name='Items:DisableLore' AND BINARY rule_value=BINARY 'true';
  IF ROW_COUNT() <> 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Expected exactly one true DisableLore rule';
  END IF;
  COMMIT;
END//
DELIMITER ;
CALL nightcap_restore_lore_20261012();
DROP PROCEDURE nightcap_restore_lore_20261012;
