-- #22 candidate: reviewed base prices for Bartholomew Packwell (99225).
-- Run in a fresh mysql batch session, without --force, AFTER a verified backup.
-- Default applies; SET @nightcap_bag_rollback=1 before sourcing for exact rollback.
-- Only price changes. Copper units: 1 platinum = 1000 copper.
-- Guarded against the exact 2026-09-15 stock/flags; drift requires a fresh review.
DROP TEMPORARY TABLE IF EXISTS nightcap_bag_price_plan;
DROP TEMPORARY TABLE IF EXISTS nightcap_bag_price_guard;
CREATE TEMPORARY TABLE nightcap_bag_price_plan (
    id INT PRIMARY KEY, old_price INT UNSIGNED, new_price INT UNSIGNED,
    bagslots INT, bagwr INT, bagsize INT, bagtype INT
) ENGINE=InnoDB;
INSERT INTO nightcap_bag_price_plan VALUES
    (53684,0,10000,8,100,4,1),
    (6504,0,20000,9,0,4,13),
    (17138,0,40000,10,100,4,1),
    (60440,0,60000,11,0,4,5),
    (17215,2500000,100000,12,100,4,1),
    (120539,0,125000,13,85,4,5),
    (124402,0,175000,14,100,4,5),
    (52080,0,200000,15,95,4,5),
    (52082,12500000,250000,16,100,4,5),
    (52298,0,375000,18,100,4,5),
    (52084,0,500000,20,100,4,5),
    (64183,0,750000,22,100,4,5),
    (54262,312500000,1000000,24,100,4,5),
    (60959,0,1250000,25,100,4,5),
    (67872,0,1500000,26,100,4,5),
    (54263,1000000000,2000000,28,100,4,5),
    (57226,0,2750000,30,100,4,5),
    (54264,0,3500000,32,100,4,5),
    (57521,0,4250000,34,100,4,5),
    (56030,0,5000000,36,100,4,5),
    (129789,0,6250000,38,100,4,3),
    (54726,0,7500000,40,100,4,58);
CREATE TEMPORARY TABLE nightcap_bag_price_guard (
    ready TINYINT NOT NULL, CONSTRAINT bag_price_preflight CHECK (ready=1)
) ENGINE=InnoDB;
SET @nightcap_bag_rollback=COALESCE(@nightcap_bag_rollback,0);
SET @nightcap_bag_ready=0;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
-- Lock the merchant range, identity and all intended items before validation.
SELECT item FROM merchantlist WHERE merchantid=99225 ORDER BY slot FOR UPDATE;
SELECT id FROM npc_types WHERE id=999225 FOR UPDATE;
SELECT i.id FROM items i JOIN nightcap_bag_price_plan p ON p.id=i.id ORDER BY i.id FOR UPDATE;
SET @nightcap_bag_ready=(
    @nightcap_bag_rollback IN (0,1)
    AND (SELECT COUNT(*) FROM npc_types WHERE id=999225
         AND name='Bartholomew_Packwell' AND class=41 AND merchant_id=99225)=1
    AND (SELECT COUNT(*) FROM merchantlist WHERE merchantid=99225)=22
    AND (SELECT COUNT(DISTINCT m.item) FROM merchantlist m
         JOIN nightcap_bag_price_plan p ON p.id=m.item WHERE m.merchantid=99225)=22
    AND (SELECT COUNT(*) FROM items i JOIN nightcap_bag_price_plan p ON p.id=i.id
         WHERE i.bagslots=p.bagslots AND i.bagwr=p.bagwr AND i.bagsize=p.bagsize
         AND i.bagtype=p.bagtype AND i.nodrop=0 AND i.sellrate=1)=22
    AND ((SELECT COUNT(*) FROM items i JOIN nightcap_bag_price_plan p ON p.id=i.id
          WHERE i.price=p.old_price)=22
         OR (SELECT COUNT(*) FROM items i JOIN nightcap_bag_price_plan p ON p.id=i.id
             WHERE i.price=p.new_price)=22)
);
INSERT INTO nightcap_bag_price_guard VALUES(COALESCE(@nightcap_bag_ready,0));
-- The condition also prevents writes if a caller mistakenly enables --force.
UPDATE items i JOIN nightcap_bag_price_plan p ON p.id=i.id
SET i.price=IF(@nightcap_bag_rollback=1,p.old_price,p.new_price)
WHERE @nightcap_bag_ready=1;
SELECT 'bag_vendor_prices', IF(@nightcap_bag_rollback=1,'rollback','apply'), ROW_COUNT();
COMMIT;
DROP TEMPORARY TABLE nightcap_bag_price_guard;
DROP TEMPORARY TABLE nightcap_bag_price_plan;
