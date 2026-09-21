-- Stop world/zones and back up first. DDL is not transactional; this schema
-- step accepts old or upgraded primary keys so interrupted upgrades can resume.
-- Existing trade audit and current offers are retained; world startup rotates.
DELIMITER //
BEGIN NOT ATOMIC
DECLARE key_columns TEXT;
DECLARE n INT;
SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) INTO key_columns
 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='nightcap_market_offers' AND INDEX_NAME='PRIMARY';
IF key_columns IS NULL OR key_columns NOT IN ('npc_id','npc_id,item_id') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected market primary key';
END IF;
IF key_columns='npc_id' THEN
 ALTER TABLE nightcap_market_offers DROP PRIMARY KEY, ADD PRIMARY KEY(npc_id,item_id);
END IF;
SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) INTO key_columns
 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='nightcap_market_trades' AND INDEX_NAME='PRIMARY';
IF key_columns IS NULL OR key_columns NOT IN ('epoch,npc_id','epoch,npc_id,item_id') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected market primary key';
END IF;
IF key_columns='epoch,npc_id' THEN
 ALTER TABLE nightcap_market_trades DROP PRIMARY KEY, ADD PRIMARY KEY(epoch,npc_id,item_id);
END IF;
END //
DELIMITER ;

DELIMITER //
DROP PROCEDURE IF EXISTS nightcap_market_rotate //
CREATE PROCEDURE nightcap_market_rotate(IN current_era INT, IN current_loot INT, IN current_buy DECIMAL(12,6))
rotation: BEGIN
  DECLARE finished INT DEFAULT 0;
  DECLARE actor_npc, actor_zone, chosen, cost, active, expected_loot INT;
  DECLARE offer_number, offer_count INT;
  DECLARE expected_buy DECIMAL(12,6);
  DECLARE actor_kind VARCHAR(8);
  DECLARE generation BIGINT UNSIGNED;
  DECLARE actors CURSOR FOR SELECT npc_id,zone_id,kind FROM nightcap_market_actors ORDER BY RAND();
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished=1;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
  START TRANSACTION;
  SELECT enabled,epoch+1,loot_multiplier,buy_cost_mod INTO active,generation,expected_loot,expected_buy
    FROM nightcap_market_state WHERE id=1 FOR UPDATE;
  IF active<>1 OR current_era<0 OR current_era>30 OR finished=1 THEN
    ROLLBACK;
    LEAVE rotation;
  END IF;
  IF current_loot<>expected_loot OR current_buy<>expected_buy THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reprice market for changed earning rules before startup';
  END IF;
  DELETE FROM nightcap_market_offers;
  OPEN actors;
  actor_loop: LOOP
    FETCH actors INTO actor_npc,actor_zone,actor_kind;
    IF finished=1 THEN LEAVE actor_loop; END IF;
    SET offer_number=0;
    SET offer_count=IF(actor_kind='find',1,2);
    WHILE offer_number<offer_count DO
    SET offer_number=offer_number+1;
    SET chosen=NULL;
    -- Aggregate avoids triggering the cursor's NOT FOUND handler for an empty pool.
    SELECT MAX(candidate.item_id) INTO chosen FROM (
      SELECT c.item_id FROM nightcap_market_catalog c JOIN items i ON i.id=c.item_id
      WHERE c.min_expansion<=current_era AND (c.max_expansion<0 OR c.max_expansion>=current_era)
        AND c.pool=IF(actor_kind='find','find','tunnel')
        AND i.nodrop<>0 AND i.norent<>0 AND i.stackable=0 AND i.maxcharges=0
        AND i.itemclass=0 AND i.questitemflag=0 AND i.attuneable=0
        AND c.buy_cp<c.sell_cp AND c.buy_cp<c.find_cp
        AND (SELECT COUNT(*) FROM nightcap_market_offers o WHERE o.item_id=c.item_id AND o.kind=actor_kind)
          < IF(actor_kind='sell',3,2)
        AND NOT EXISTS (SELECT 1 FROM nightcap_market_offers own WHERE own.npc_id=actor_npc AND own.item_id=c.item_id)
        AND NOT EXISTS (SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid
          WHERE m.item=c.item_id AND n.id=actor_npc)
      ORDER BY (SELECT COUNT(*) FROM nightcap_market_offers used WHERE used.item_id=c.item_id AND used.kind=actor_kind), RAND() LIMIT 1
    ) candidate;
    IF chosen IS NOT NULL THEN
      SELECT CASE actor_kind WHEN 'find' THEN find_cp WHEN 'sell' THEN sell_cp ELSE buy_cp END
        INTO cost FROM nightcap_market_catalog WHERE item_id=chosen;
      IF cost>0 THEN
        INSERT INTO nightcap_market_offers(npc_id,epoch,zone_id,kind,item_id,price_cp)
          VALUES(actor_npc,generation,actor_zone,actor_kind,chosen,cost);
      END IF;
    END IF;
    END WHILE;
  END LOOP;
  CLOSE actors;
  UPDATE nightcap_market_state SET epoch=generation,expansion=current_era,rotated_at=CURRENT_TIMESTAMP WHERE id=1;
  COMMIT;
END //
DELIMITER ;
