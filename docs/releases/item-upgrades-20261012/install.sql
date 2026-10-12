-- Apply offline after a fresh target backup. Install the matching native zone
-- and quests/ecommons/999820.pl before activation. Adds one reusable box item;
-- existing tier item definitions are unchanged. Regenerate shared item memory.
CREATE TABLE IF NOT EXISTS nightcap_item_upgrade_state (
 id TINYINT PRIMARY KEY, revision BIGINT NOT NULL, enabled TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nightcap_item_upgrades (
 request_id CHAR(36) PRIMARY KEY, character_id INT NOT NULL,
 input_id INT NOT NULL, output_id INT NOT NULL,
 inventory_before TEXT NOT NULL, inventory_after TEXT NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

DELIMITER //
CREATE PROCEDURE nightcap_item_upgrade_install_20261012()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()
     AND TABLE_NAME IN ('items','npc_types','spawngroup','spawnentry','spawn2','inventory',
                        'nightcap_item_upgrade_state','nightcap_item_upgrades')
     AND ENGINE='InnoDB')<>8
    OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()
               AND EVENT_OBJECT_TABLE IN ('items','npc_types','spawngroup','spawnentry','spawn2',
                   'inventory','nightcap_item_upgrade_state','nightcap_item_upgrades')) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Upgrade tables must be untriggered InnoDB';
 END IF;
 IF EXISTS (SELECT 1 FROM nightcap_item_upgrade_state)
    OR EXISTS (SELECT 1 FROM nightcap_item_upgrades)
    OR EXISTS (SELECT 1 FROM items WHERE id=900620 OR Name='Reforging Box')
    OR EXISTS (SELECT 1 FROM tradeskill_recipe_entries WHERE item_id=900620)
    OR EXISTS (SELECT 1 FROM npc_types WHERE id=999820 OR name='Artisan_Veyra')
    OR EXISTS (SELECT 1 FROM spawngroup WHERE id=999820 OR name='NightcapItemUpgrades')
    OR EXISTS (SELECT 1 FROM spawnentry WHERE spawngroupID=999820 OR npcID=999820)
    OR EXISTS (SELECT 1 FROM spawn2 WHERE id=999820 OR spawngroupID=999820)
    OR EXISTS (SELECT 1 FROM zone_state_spawns WHERE npc_id=999820 OR spawngroup_id=999820 OR spawn2_id=999820) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Upgrade identity or feature ownership collision';
 END IF;
 IF (SELECT COUNT(*) FROM items WHERE id=17339 AND itemclass=1 AND bagtype=13 AND bagslots=4)<>1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Native four-slot combine-box template changed';
 END IF;

 CREATE TEMPORARY TABLE nightcap_upgrade_box LIKE items;
 INSERT INTO nightcap_upgrade_box SELECT * FROM items WHERE id=17339;
 UPDATE nightcap_upgrade_box SET id=900620,Name='Reforging Box',lore='Reforging Box',
  itemclass=1,bagtype=13,bagslots=4,bagsize=10,bagwr=0,weight=10,size=2,
  price=0,sellrate=0,norent=1,nodrop=1,attuneable=0,loregroup=-1,
  stackable=0,stacksize=1,maxcharges=0,reqlevel=0,reclevel=0,
  slots=0,classes=65535,races=65535,deity=0,
  clickeffect=-1,proceffect=-1,worneffect=-1,focuseffect=-1,scrolleffect=-1,bardeffect=-1,
  charmfile='',charmfileid=0,scriptfileid=0;
 INSERT INTO items SELECT * FROM nightcap_upgrade_box;
 DROP TEMPORARY TABLE nightcap_upgrade_box;
 IF (SELECT COUNT(*) FROM npc_types WHERE id=22033 AND race=1 AND gender=0
     AND texture=2 AND helmtexture=0)<>1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Native East Commonlands appearance template changed';
 END IF;

 -- Copy a native appearance; explicitly remove template combat/service behavior.
 CREATE TEMPORARY TABLE nightcap_upgrade_npc LIKE npc_types;
 INSERT INTO nightcap_upgrade_npc SELECT * FROM npc_types WHERE id=22033;
 UPDATE nightcap_upgrade_npc SET id=999820,name='Artisan_Veyra',lastname='Reforging Boxes',
  level=50,maxlevel=50,class=1,hp=100000,mana=0,loottable_id=0,merchant_id=0,
  alt_currency_id=0,npc_spells_id=0,npc_spells_effects_id=0,npc_faction_id=0,
  adventure_template_id=0,trap_template=0,
  special_abilities='19,1^20,1^24,1^35,1',npcspecialattks='',aggroradius=0,assistradius=0,
  npc_aggro=0,always_aggro=0,raid_target=0,spawn_limit=1,findable=1,emoteid=0,isquest=1,
  skip_global_loot=1,keeps_sold_items=0,is_parcel_merchant=0,multiquest_enabled=0,
  qglobal=0,unique_spawn_by_name=1,armortint_id=0,npc_tint_id=0,herosforgemodel=0;
 INSERT INTO npc_types SELECT * FROM nightcap_upgrade_npc;
 DROP TEMPORARY TABLE nightcap_upgrade_npc;
 INSERT INTO spawngroup (id,name) VALUES (999820,'NightcapItemUpgrades');
 INSERT INTO spawnentry (spawngroupID,npcID,chance,min_expansion,max_expansion)
 VALUES (999820,999820,100,0,-1);
 -- Workshop, beside the compact layout's Epic Forgemaster. Existing spawns stay put.
 INSERT INTO spawn2 (id,spawngroupID,zone,version,x,y,z,heading,respawntime,variance,
                     pathgrid,min_expansion,max_expansion)
 VALUES (999820,999820,'ecommons',0,-385,-1818,3.75,0,60,0,0,0,-1);
 INSERT INTO nightcap_item_upgrade_state (id,revision,enabled) VALUES (1,2026101201,0);
 COMMIT;
END//
DELIMITER ;
CALL nightcap_item_upgrade_install_20261012();
DROP PROCEDURE nightcap_item_upgrade_install_20261012;
