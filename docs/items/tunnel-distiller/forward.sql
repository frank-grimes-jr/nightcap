-- Add one permanent entry to Della's existing East Commonlands shop.
DELIMITER //
BEGIN NOT ATOMIC
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    START TRANSACTION;
    IF (SELECT COUNT(*) FROM npc_types WHERE merchant_id = 999609) <> 1
       OR NOT EXISTS (
           SELECT 1 FROM npc_types n
           JOIN spawnentry e ON e.npcID = n.id
           JOIN spawn2 s ON s.spawngroupID = e.spawngroupID
           WHERE n.id = 999609 AND n.merchant_id = 999609 AND BINARY n.name = 'Della'
             AND n.class = 41 AND n.alt_currency_id = 0 AND s.zone = 'ecommons' AND s.version = 0
       ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Expected the dedicated tunnel jeweler page';
    END IF;

    -- Raw price is zero. Nightcap FreeTrade gives this originally NO DROP item
    -- the same one-platinum minimum for buying that it uses for fixed resale.
    IF NOT EXISTS (
        SELECT 1 FROM items WHERE id = 52023 AND BINARY Name = 'Perfected Augmentation Distiller'
          AND itemtype = 64 AND stackable = 1 AND minstatus = 0
          AND nodrop = 0 AND price = 0 AND sellrate = 1
    ) OR NOT EXISTS (
        SELECT 1 FROM zone z JOIN rule_values r ON r.ruleset_id = z.ruleset
        WHERE z.short_name = 'ecommons' AND z.version = 0
          AND r.rule_name = 'Items:FreeTrade' AND LOWER(r.rule_value) IN ('true', '1')
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Expected the priced Nightcap perfected distiller';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM merchantlist WHERE merchantid = 999609 AND (slot = 105 OR item = 52023)) THEN
        INSERT INTO merchantlist (merchantid, slot, item, min_expansion) VALUES (999609, 105, 52023, 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM merchantlist WHERE merchantid = 999609 AND slot = 105 AND item = 52023
          AND faction_required = -100 AND level_required = 0 AND min_status = 0 AND max_status = 255
          AND alt_currency_cost = 0 AND classes_required = 65535 AND probability = 100
          AND bucket_name = '' AND bucket_value = '' AND bucket_comparison = 0
          AND min_expansion = 0 AND max_expansion = -1
          AND content_flags IS NULL AND content_flags_disabled IS NULL
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Della distiller stock conflicts with the expected row';
    END IF;
    COMMIT;
END//
DELIMITER ;
