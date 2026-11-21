CREATE TEMPORARY TABLE expected_ornaments LIKE items;
DELIMITER //
BEGIN NOT ATOMIC
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    START TRANSACTION;
    -- EXPORT_FINGERPRINT
    IF @actual_rows <> @expected_rows OR @actual_checksum <> @expected_checksum THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Target equipment changed. Export the target again and regenerate the plan.';
    END IF;
    INSERT INTO nightcap_ornament_design (visual)
        SELECT d.visual FROM designs d LEFT JOIN nightcap_ornament_design r USING (visual)
        WHERE r.id IS NULL ORDER BY d.visual;
    IF EXISTS (SELECT 1 FROM nightcap_ornament_design WHERE id NOT BETWEEN 1000000 AND 1048575)
        OR EXISTS (SELECT 1 FROM nightcap_ornament_design r JOIN items i ON i.id=r.id
            WHERE BINARY i.lore <> 'Nightcap appearance ornament' OR i.itemtype <> 54) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Ornament ID conflict or RoF2 link limit reached';
    END IF;

    -- Start with a fresh definition and copy only visual and compatibility fields.
    INSERT INTO expected_ornaments (id, Name, lore, itemclass, itemtype, slots, augtype, augrestrict,
        idfile, material, elitematerial, herosforgemodel, color, icon, classes, races,
        nodrop, norent, stacksize, stackable, price, sellrate, nopet, clickeffect,
        proceffect, worneffect, focuseffect, scrolleffect, bardeffect)
        SELECT r.id, d.label, 'Nightcap appearance ornament', 0, 54, d.slots,
            1 << (d.socket-1), d.restriction_id, IF(d.model,CONCAT('IT',d.model),''),
            d.mat, d.elite, d.hero, d.tint, d.icon, 65535, 65535, 1, 1, 1, 0,
            0, 0, 1, -1, -1, -1, -1, -1, -1
        FROM designs d JOIN nightcap_ornament_design r USING (visual);
    -- A reused definition must still be statless, including in columns added by
    -- later PEQ releases. Compare every gameplay field with a freshly generated row.
    SET @saved_concat_limit=@@session.group_concat_max_len;
    SET SESSION group_concat_max_len=65535;
    SELECT GROUP_CONCAT(CONCAT('(i.`',COLUMN_NAME,'` <=> e.`',COLUMN_NAME,'`)') SEPARATOR ' AND ')
        INTO @matches FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='items'
        AND column_name <> 'Name' AND data_type NOT IN ('date','datetime','timestamp');
    SET SESSION group_concat_max_len=@saved_concat_limit;
    SET @check_existing=CONCAT('SELECT COUNT(*) INTO @drift FROM expected_ornaments e JOIN items i USING(id) WHERE NOT (',@matches,')');
    PREPARE ornament_check FROM @check_existing;
    EXECUTE ornament_check;
    DEALLOCATE PREPARE ornament_check;
    IF @drift <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Existing ornament differs from its statless definition';
    END IF;
    INSERT INTO items SELECT e.* FROM expected_ornaments e LEFT JOIN items i USING(id) WHERE i.id IS NULL;
    UPDATE nightcap_ornament_design r LEFT JOIN designs d USING (visual) SET r.active=(d.visual IS NOT NULL);
    DELETE FROM nightcap_ornament_source;
    INSERT INTO nightcap_ornament_source SELECT d.donor,r.id FROM donors d JOIN nightcap_ornament_design r USING (visual);

    IF NOT EXISTS (SELECT 1 FROM npc_types WHERE id=998946) THEN
        INSERT INTO npc_types (id,name,lastname,level,race,class,bodytype,hp,gender,size,
            merchant_id,loottable_id,texture,npc_faction_id,special_abilities)
        VALUES (998946,'Ornament_Artisan','Appearance Exchange',50,1,1,1,5000,1,6,
            0,0,1,0,'19,1^20,1^24,1^35,1');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM npc_types WHERE id=998946 AND BINARY name='Ornament_Artisan'
        AND class=1 AND merchant_id=0 AND loottable_id=0) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Ornament artisan NPC conflict';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM spawngroup WHERE name='nightcap_ornament_artisan') THEN
        INSERT INTO spawngroup (name) VALUES ('nightcap_ornament_artisan');
    END IF;
    SET @artisan_group=(SELECT id FROM spawngroup WHERE name='nightcap_ornament_artisan');
    IF NOT EXISTS (SELECT 1 FROM spawnentry WHERE spawngroupID=@artisan_group) THEN
        INSERT INTO spawnentry (spawngroupID,npcID,chance) VALUES (@artisan_group,998946,100);
    END IF;
    IF (SELECT COUNT(*) FROM spawnentry WHERE spawngroupID=@artisan_group)<>1 OR
        NOT EXISTS (SELECT 1 FROM spawnentry WHERE spawngroupID=@artisan_group AND npcID=998946 AND chance=100) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Ornament artisan spawn group conflict';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM spawn2 WHERE spawngroupID=@artisan_group) THEN
        INSERT INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime)
            SELECT @artisan_group,s.zone,0,s.x+12,s.y,s.z,s.heading,60
            FROM spawn2 s JOIN spawnentry e ON s.spawngroupID=e.spawngroupID
            JOIN npc_types n ON n.id=e.npcID
            WHERE n.name='Epic_Forgemaster' AND s.zone='ecommons' AND s.version=0;
    END IF;
    IF (SELECT COUNT(*) FROM spawn2 WHERE spawngroupID=@artisan_group)<>1 OR
        NOT EXISTS (SELECT 1 FROM spawn2 WHERE spawngroupID=@artisan_group AND zone='ecommons' AND version=0) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Expected one East Commonlands forge anchor';
    END IF;
    COMMIT;
END//
DELIMITER ;
