-- Withdraw only the complete owned afterimage. Retain purchased items.
DELIMITER //
BEGIN NOT ATOMIC
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    START TRANSACTION;
    DELETE FROM merchantlist WHERE merchantid = 999609 AND slot = 105 AND item = 52023
      AND faction_required = -100 AND level_required = 0 AND min_status = 0 AND max_status = 255
      AND alt_currency_cost = 0 AND classes_required = 65535 AND probability = 100
      AND bucket_name = '' AND bucket_value = '' AND bucket_comparison = 0
      AND min_expansion = 0 AND max_expansion = -1
      AND content_flags IS NULL AND content_flags_disabled IS NULL;
    IF EXISTS (SELECT 1 FROM merchantlist WHERE merchantid = 999609 AND (slot = 105 OR item = 52023)) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Review changed Della distiller stock before rollback';
    END IF;
    COMMIT;
END//
DELIMITER ;
