-- Additive schema, disabled until reviewed content and matching world/zone are installed.
-- Run once; an existing object is a collision, not permission to overwrite it.
CREATE TABLE nightcap_market_state (
  id TINYINT UNSIGNED PRIMARY KEY,
  enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
  epoch BIGINT UNSIGNED NOT NULL DEFAULT 0,
  expansion INT NOT NULL DEFAULT 0,
  loot_multiplier INT NOT NULL DEFAULT 4,
  buy_cost_mod DECIMAL(12,6) NOT NULL DEFAULT 2.5,
  rotated_at TIMESTAMP NULL
) ENGINE=InnoDB;
INSERT INTO nightcap_market_state(id) VALUES(1);

CREATE TABLE nightcap_market_catalog (
  item_id INT UNSIGNED PRIMARY KEY,
  pool ENUM('find','tunnel') NOT NULL,
  min_expansion INT NOT NULL,
  max_expansion INT NOT NULL DEFAULT -1,
  find_cp INT UNSIGNED NOT NULL,
  sell_cp INT UNSIGNED NOT NULL,
  buy_cp INT UNSIGNED NOT NULL,
  source_url VARCHAR(255) NOT NULL,
  captured_at DATE NOT NULL,
  CHECK(buy_cp < sell_cp AND buy_cp < find_cp)
) ENGINE=InnoDB;

CREATE TABLE nightcap_market_actors (
  npc_id INT UNSIGNED PRIMARY KEY,
  zone_id INT UNSIGNED NOT NULL,
  kind ENUM('find','sell','buy') NOT NULL
) ENGINE=InnoDB;

CREATE TABLE nightcap_market_offers (
  npc_id INT UNSIGNED PRIMARY KEY,
  epoch BIGINT UNSIGNED NOT NULL,
  zone_id INT UNSIGNED NOT NULL,
  kind ENUM('find','sell','buy') NOT NULL,
  item_id INT UNSIGNED NOT NULL,
  price_cp INT UNSIGNED NOT NULL,
  remaining TINYINT UNSIGNED NOT NULL DEFAULT 1,
  CHECK(remaining <= 1 AND price_cp > 0)
) ENGINE=InnoDB;

CREATE TABLE nightcap_market_trades (
  epoch BIGINT UNSIGNED NOT NULL,
  npc_id INT UNSIGNED NOT NULL,
  character_id INT UNSIGNED NOT NULL,
  kind ENUM('find','sell','buy') NOT NULL,
  item_id INT UNSIGNED NOT NULL,
  price_cp INT UNSIGNED NOT NULL,
  traded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(epoch,npc_id)
) ENGINE=InnoDB;

DELIMITER //
CREATE PROCEDURE nightcap_market_rotate(IN current_era INT, IN current_loot INT, IN current_buy DECIMAL(12,6))
rotation: BEGIN
  DECLARE finished INT DEFAULT 0;
  DECLARE actor_npc, actor_zone, chosen, cost, active, expected_loot INT;
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
          < IF(actor_kind='find',2,1)
        AND NOT EXISTS (SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid
          WHERE m.item=c.item_id AND n.id=actor_npc)
      ORDER BY RAND() LIMIT 1
    ) candidate;
    IF chosen IS NOT NULL THEN
      SELECT CASE actor_kind WHEN 'find' THEN find_cp WHEN 'sell' THEN sell_cp ELSE buy_cp END
        INTO cost FROM nightcap_market_catalog WHERE item_id=chosen;
      IF cost>0 THEN
        INSERT INTO nightcap_market_offers(npc_id,epoch,zone_id,kind,item_id,price_cp)
          VALUES(actor_npc,generation,actor_zone,actor_kind,chosen,cost);
      END IF;
    END IF;
  END LOOP;
  CLOSE actors;
  UPDATE nightcap_market_state SET epoch=generation,expansion=current_era,rotated_at=CURRENT_TIMESTAMP WHERE id=1;
  COMMIT;
END //
DELIMITER ;
