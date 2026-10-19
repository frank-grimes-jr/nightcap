DELIMITER //
CREATE PROCEDURE nightcap_allclass_aa_20261019()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='aa_ability' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='aa_ability') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected WPM content storage'; END IF;
 IF NOT ((SELECT COUNT(*) FROM aa_ability WHERE `id` <=> 389)=1 AND NOT EXISTS (SELECT 1 FROM aa_ability WHERE `id` <=> 389 AND NOT ((`auto_grant_enabled` <=> 1 AND `category` <=> -1 AND `charges` <=> 0 AND `classes` <=> 550 AND `deities` <=> 131071 AND `drakkin_heritage` <=> 127 AND `enabled` <=> 1 AND `first_rank_id` <=> 1186 AND `grant_only` <=> 0 AND `id` <=> 389 AND BINARY `name` <=> BINARY CONVERT(X'4865616c696e6720426f6f6e' USING utf8mb4) AND `races` <=> 65535 AND `reset_on_death` <=> 0 AND `status` <=> 0 AND `type` <=> 2)))) THEN
  IF NOT ((SELECT COUNT(*) FROM aa_ability WHERE `id` <=> 389)=1 AND NOT EXISTS (SELECT 1 FROM aa_ability WHERE `id` <=> 389 AND NOT ((`auto_grant_enabled` <=> 1 AND `category` <=> -1 AND `charges` <=> 0 AND `classes` <=> 518 AND `deities` <=> 131071 AND `drakkin_heritage` <=> 127 AND `enabled` <=> 1 AND `first_rank_id` <=> 1186 AND `grant_only` <=> 0 AND `id` <=> 389 AND BINARY `name` <=> BINARY CONVERT(X'4865616c696e6720426f6f6e' USING utf8mb4) AND `races` <=> 65535 AND `reset_on_death` <=> 0 AND `status` <=> 0 AND `type` <=> 2)))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM aa_ability preimage drift'; END IF;
  UPDATE aa_ability SET `classes`=550 WHERE `id` <=> 389;
  IF NOT ((SELECT COUNT(*) FROM aa_ability WHERE `id` <=> 389)=1 AND NOT EXISTS (SELECT 1 FROM aa_ability WHERE `id` <=> 389 AND NOT ((`auto_grant_enabled` <=> 1 AND `category` <=> -1 AND `charges` <=> 0 AND `classes` <=> 550 AND `deities` <=> 131071 AND `drakkin_heritage` <=> 127 AND `enabled` <=> 1 AND `first_rank_id` <=> 1186 AND `grant_only` <=> 0 AND `id` <=> 389 AND BINARY `name` <=> BINARY CONVERT(X'4865616c696e6720426f6f6e' USING utf8mb4) AND `races` <=> 65535 AND `reset_on_death` <=> 0 AND `status` <=> 0 AND `type` <=> 2)))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM aa_ability afterimage mismatch'; END IF;
 END IF;
 COMMIT;
END//
DELIMITER ;
CALL nightcap_allclass_aa_20261019();
DROP PROCEDURE nightcap_allclass_aa_20261019;
