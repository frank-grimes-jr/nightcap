-- =============================================================================
-- Tiered Loot System — item generation + supporting data
-- Run:  docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < tiered_loot_setup.sql
-- After running: regenerate shared memory (./bin/shared_memory) and restart zones.
--
-- Tiers (packed under the RoF2 link cap of 1,048,575 — see say_link.cpp %05X/0xFFFFF):
--   T1 base     = id < 200000 (unchanged)
--   T2 Polished = base + 200,000
--   T3 Exalted  = base + 400,000
--   T4 Ascended = base + 600,000
--   Ascended epics = base + 800,000 (quest-only; see Epic_Forgemaster.pl)
--   Custom items   = 900,000+
--
-- Scaling model (2026-07-16 rework — calibrated to THJ Legendary, issue #25):
-- Ascended (max tier) matches THJ's Legendary multipliers, measured off the
-- Necklace of Eternal Visions (item 9289) base vs its Legendary version.
-- Per stat FAMILY (Polished / Exalted / Ascended):
--   HP / Mana:                 x1.45 / x1.90 / x2.40   (THJ Legendary ~x2.4)
--   AC / base stats / resists / regens: x1.35 / x1.65 / x2.00
--   Endurance:                 x1.07 / x1.13 / x1.20   (THJ: 180 -> 220)
--   Offense (dmg/atk/acc/spelldmg/healamt/...): x1.10 / x1.20 / x1.35
--                              (kept conservative so solo kill-speed doesn't
--                               trivialize — offense comes from AA/disc/augs, per #24)
-- NOT scaled (THJ leaves them): shielding, spellshield, dotshielding, avoidance,
--   clairvoyance (capped advanced stats). HEROIC stats are also left untouched:
--   THJ *adds* heroic on Legendary; that layer is deferred to heroic-stats (#8).
--
-- Scope: equippable items (slots>0) with >=1 positive scalable stat, plus all
-- bags (bagslots>0). Class epic weapons are excluded (upgraded via quest).
-- Stats scaled only when > 0 (negatives left as-is). Effects/haste/delay/req levels
-- not scaled. Bags get +slots, +weight-reduction, +capacity per tier.
-- =============================================================================

DROP PROCEDURE IF EXISTS gen_loot_tier;
DELIMITER //
CREATE PROCEDURE gen_loot_tier(
    IN p_off     INT,
    IN p_hpmana  DECIMAL(4,2),  -- HP / Mana        (Ascended = THJ Legendary x2.4)
    IN p_core    DECIMAL(4,2),  -- AC / base stats / resists / regens  (x2.0)
    IN p_endur   DECIMAL(4,2),  -- Endurance        (x1.2)
    IN p_offn    DECIMAL(4,2),  -- offense: damage/attack/accuracy/spelldmg/healamt/... (conservative)
    IN p_heroic  DECIMAL(4,2),  -- heroic = this fraction of the scaled stat (Ascended 0.25; else 0)  #8
    IN p_tag     VARCHAR(20),
    IN p_bagslot INT,
    IN p_bagwr   INT,
    IN p_bagsize INT
)
BEGIN
    -- clear this tier's id band (idempotent re-run)
    DELETE FROM items WHERE id BETWEEN p_off + 1 AND p_off + 199999;

    DROP TEMPORARY TABLE IF EXISTS tg;
    CREATE TEMPORARY TABLE tg AS
        SELECT * FROM items
        WHERE id < 200000
          -- class epic 1.0 weapons (+ fabled dup ids) — excluded, quest-only Ascended
          AND id NOT IN (5532,10099,10650,10651,10652,10908,11057,11566,14341,14383,
                         20487,20488,20490,20542,20544,36223,36224,66175)
          AND (
            bagslots > 0
            OR (slots > 0 AND (
                 ac>0 OR hp>0 OR mana>0 OR endur>0 OR regen>0 OR manaregen>0 OR enduranceregen>0
              OR damage>0 OR astr>0 OR asta>0 OR aagi>0 OR adex>0 OR acha>0 OR aint>0 OR awis>0
              OR heroic_str>0 OR heroic_sta>0 OR heroic_agi>0 OR heroic_dex>0 OR heroic_cha>0
              OR heroic_int>0 OR heroic_wis>0
              OR fr>0 OR cr>0 OR mr>0 OR dr>0 OR pr>0 OR svcorruption>0
              OR attack>0 OR accuracy>0 OR avoidance>0 OR combateffects>0 OR spelldmg>0 OR healamt>0
              OR clairvoyance>0 OR backstabdmg>0 OR elemdmgamt>0 OR dotshielding>0 OR shielding>0
              OR spellshield>0 OR strikethrough>0 OR damageshield>0
            ))
          );

    -- HP / Mana (scale highest) + tag + id shift
    UPDATE tg SET
      id   = id + p_off,
      Name = CONCAT(Name, p_tag),
      hp   = IF(hp>0,   ROUND(hp   * p_hpmana), hp),
      mana = IF(mana>0, ROUND(mana * p_hpmana), mana);

    -- Core defense: AC, base stats, resists, regens (positive only)
    UPDATE tg SET
      ac=IF(ac>0,ROUND(ac*p_core),ac),
      regen=IF(regen>0,ROUND(regen*p_core),regen), manaregen=IF(manaregen>0,ROUND(manaregen*p_core),manaregen),
      enduranceregen=IF(enduranceregen>0,ROUND(enduranceregen*p_core),enduranceregen),
      astr=IF(astr>0,ROUND(astr*p_core),astr), asta=IF(asta>0,ROUND(asta*p_core),asta), aagi=IF(aagi>0,ROUND(aagi*p_core),aagi),
      adex=IF(adex>0,ROUND(adex*p_core),adex), acha=IF(acha>0,ROUND(acha*p_core),acha), aint=IF(aint>0,ROUND(aint*p_core),aint), awis=IF(awis>0,ROUND(awis*p_core),awis),
      fr=IF(fr>0,ROUND(fr*p_core),fr), cr=IF(cr>0,ROUND(cr*p_core),cr), mr=IF(mr>0,ROUND(mr*p_core),mr),
      dr=IF(dr>0,ROUND(dr*p_core),dr), pr=IF(pr>0,ROUND(pr*p_core),pr), svcorruption=IF(svcorruption>0,ROUND(svcorruption*p_core),svcorruption);

    -- Endurance (scales least, per THJ: 180 -> 220)
    UPDATE tg SET endur=IF(endur>0,ROUND(endur*p_endur),endur);

    -- Offense (conservative — keeps solo kill-speed from trivializing; positive only)
    UPDATE tg SET
      damage=IF(damage>0,ROUND(damage*p_offn),damage),
      attack=IF(attack>0,ROUND(attack*p_offn),attack), accuracy=IF(accuracy>0,ROUND(accuracy*p_offn),accuracy),
      spelldmg=IF(spelldmg>0,ROUND(spelldmg*p_offn),spelldmg), healamt=IF(healamt>0,ROUND(healamt*p_offn),healamt),
      backstabdmg=IF(backstabdmg>0,ROUND(backstabdmg*p_offn),backstabdmg), elemdmgamt=IF(elemdmgamt>0,ROUND(elemdmgamt*p_offn),elemdmgamt),
      combateffects=IF(combateffects>0,ROUND(combateffects*p_offn),combateffects),
      strikethrough=IF(strikethrough>0,ROUND(strikethrough*p_offn),strikethrough), damageshield=IF(damageshield>0,ROUND(damageshield*p_offn),damageshield);

    -- Heroic stats (THJ Legendary signature, #8): add p_heroic of the SCALED base
    -- stat/resist as heroic (Ascended p_heroic=0.25 -> STA 40 gets +10 heroic, matching
    -- the reference necklace). Lower tiers pass 0. The heroic engine is live at x1.0
    -- multipliers (Character:Heroic*Multiplier); heroic also raises the stat softcap.
    -- Still NOT scaled: shielding/spellshield/dotshielding/avoidance/clairvoyance (capped).
    UPDATE tg SET
      heroic_str = heroic_str + IF(astr>0, ROUND(astr*p_heroic), 0),
      heroic_sta = heroic_sta + IF(asta>0, ROUND(asta*p_heroic), 0),
      heroic_agi = heroic_agi + IF(aagi>0, ROUND(aagi*p_heroic), 0),
      heroic_dex = heroic_dex + IF(adex>0, ROUND(adex*p_heroic), 0),
      heroic_int = heroic_int + IF(aint>0, ROUND(aint*p_heroic), 0),
      heroic_wis = heroic_wis + IF(awis>0, ROUND(awis*p_heroic), 0),
      heroic_cha = heroic_cha + IF(acha>0, ROUND(acha*p_heroic), 0),
      heroic_mr  = heroic_mr  + IF(mr>0, ROUND(mr*p_heroic), 0),
      heroic_fr  = heroic_fr  + IF(fr>0, ROUND(fr*p_heroic), 0),
      heroic_cr  = heroic_cr  + IF(cr>0, ROUND(cr*p_heroic), 0),
      heroic_dr  = heroic_dr  + IF(dr>0, ROUND(dr*p_heroic), 0),
      heroic_pr  = heroic_pr  + IF(pr>0, ROUND(pr*p_heroic), 0)
      WHERE p_heroic > 0;

    -- bag scaling: more slots, weight reduction, capacity
    UPDATE tg SET
      bagslots = LEAST(bagslots + p_bagslot, 40),
      bagwr    = LEAST(bagwr + p_bagwr, 100),
      bagsize  = GREATEST(bagsize, p_bagsize)
      WHERE bagslots > 0;

    INSERT INTO items SELECT * FROM tg;
    DROP TEMPORARY TABLE IF EXISTS tg;
END //
DELIMITER ;

--                       hpmana core  endur offn  heroic tag             bag: slot wr size
CALL gen_loot_tier(200000, 1.45, 1.35, 1.07, 1.10, 0.00, ' (Polished)', 2,  25, 3);
CALL gen_loot_tier(400000, 1.90, 1.65, 1.13, 1.20, 0.00, ' (Exalted)',  4,  50, 4);
CALL gen_loot_tier(600000, 2.40, 2.00, 1.20, 1.35, 0.25, ' (Ascended)', 6, 100, 4);  -- = THJ Legendary (+25% heroic)

DROP PROCEDURE IF EXISTS gen_loot_tier;

-- =============================================================================
-- Part 2 — Ascended epics, Essence item, Forgemaster NPC, global Essence drop
-- =============================================================================

-- Ascended epics: each class 1.0 epic -> base+800,000 (quest-only reward).
-- Same per-family scaling as T4 Ascended (= THJ Legendary): HP/Mana x2.4,
-- AC/stats/resists/regens x2.0, Endurance x1.2, offense x1.35. Capped advanced
-- stats + heroics left untouched (heroics deferred to #8).
DELETE FROM items WHERE id BETWEEN 800001 AND 899999;
DROP TEMPORARY TABLE IF EXISTS tge;
CREATE TEMPORARY TABLE tge AS SELECT * FROM items
  WHERE id IN (5532,10099,10650,10651,10652,10908,11057,11566,14341,14383,20487,20488,20490,20542,20544);
UPDATE tge SET
  id=id+800000, Name=CONCAT(Name,' (Ascended)'),
  hp=IF(hp>0,ROUND(hp*2.40),hp), mana=IF(mana>0,ROUND(mana*2.40),mana),
  ac=IF(ac>0,ROUND(ac*2.00),ac),
  regen=IF(regen>0,ROUND(regen*2.00),regen), manaregen=IF(manaregen>0,ROUND(manaregen*2.00),manaregen),
  enduranceregen=IF(enduranceregen>0,ROUND(enduranceregen*2.00),enduranceregen),
  astr=IF(astr>0,ROUND(astr*2.00),astr), asta=IF(asta>0,ROUND(asta*2.00),asta), aagi=IF(aagi>0,ROUND(aagi*2.00),aagi),
  adex=IF(adex>0,ROUND(adex*2.00),adex), acha=IF(acha>0,ROUND(acha*2.00),acha), aint=IF(aint>0,ROUND(aint*2.00),aint), awis=IF(awis>0,ROUND(awis*2.00),awis),
  fr=IF(fr>0,ROUND(fr*2.00),fr), cr=IF(cr>0,ROUND(cr*2.00),cr), mr=IF(mr>0,ROUND(mr*2.00),mr),
  dr=IF(dr>0,ROUND(dr*2.00),dr), pr=IF(pr>0,ROUND(pr*2.00),pr), svcorruption=IF(svcorruption>0,ROUND(svcorruption*2.00),svcorruption),
  endur=IF(endur>0,ROUND(endur*1.20),endur),
  damage=IF(damage>0,ROUND(damage*1.35),damage),
  attack=IF(attack>0,ROUND(attack*1.35),attack), accuracy=IF(accuracy>0,ROUND(accuracy*1.35),accuracy),
  spelldmg=IF(spelldmg>0,ROUND(spelldmg*1.35),spelldmg), healamt=IF(healamt>0,ROUND(healamt*1.35),healamt),
  backstabdmg=IF(backstabdmg>0,ROUND(backstabdmg*1.35),backstabdmg), elemdmgamt=IF(elemdmgamt>0,ROUND(elemdmgamt*1.35),elemdmgamt),
  combateffects=IF(combateffects>0,ROUND(combateffects*1.35),combateffects),
  strikethrough=IF(strikethrough>0,ROUND(strikethrough*1.35),strikethrough), damageshield=IF(damageshield>0,ROUND(damageshield*1.35),damageshield);
-- Ascended epic heroic (+25% of scaled stat, matching T4 Ascended, #8)
UPDATE tge SET
  heroic_str=heroic_str+IF(astr>0,ROUND(astr*0.25),0), heroic_sta=heroic_sta+IF(asta>0,ROUND(asta*0.25),0),
  heroic_agi=heroic_agi+IF(aagi>0,ROUND(aagi*0.25),0), heroic_dex=heroic_dex+IF(adex>0,ROUND(adex*0.25),0),
  heroic_int=heroic_int+IF(aint>0,ROUND(aint*0.25),0), heroic_wis=heroic_wis+IF(awis>0,ROUND(awis*0.25),0),
  heroic_cha=heroic_cha+IF(acha>0,ROUND(acha*0.25),0),
  heroic_mr=heroic_mr+IF(mr>0,ROUND(mr*0.25),0), heroic_fr=heroic_fr+IF(fr>0,ROUND(fr*0.25),0),
  heroic_cr=heroic_cr+IF(cr>0,ROUND(cr*0.25),0), heroic_dr=heroic_dr+IF(dr>0,ROUND(dr*0.25),0), heroic_pr=heroic_pr+IF(pr>0,ROUND(pr*0.25),0);
INSERT INTO items SELECT * FROM tge;
DROP TEMPORARY TABLE IF EXISTS tge;

-- Essence of Ascension (quest currency): clone Dryad Parts(8107) -> 900000, stackable
DELETE FROM items WHERE id=900000;
DROP TEMPORARY TABLE IF EXISTS tess;
CREATE TEMPORARY TABLE tess AS SELECT * FROM items WHERE id=8107;
-- nodrop=0 (tradeable, so it can be handed to the Forgemaster), norent=1 (permanent)
UPDATE tess SET id=900000, Name='Essence of Ascension', magic=1, nodrop=0, norent=1, stackable=1, stacksize=20, loregroup=0;
INSERT INTO items SELECT * FROM tess;
DROP TEMPORARY TABLE IF EXISTS tess;

-- Epic Forgemaster NPC (Dwarf smith) near the Magelo loremaster cluster
INSERT INTO npc_types (id,name,level,race,`class`,bodytype,hp,mana,gender,texture,helmtexture,size,loottable_id,merchant_id,
  npc_spells_id,npc_faction_id,mindmg,maxdmg,npcspecialattks,special_abilities,d_melee_texture1,d_melee_texture2,prim_melee_type,sec_melee_type,runspeed,lastname)
VALUES (999226,'Epic_Forgemaster',70,8,1,1,500000,0,0,2,0,5.5,0,0,0,0,0,0,'','',0,0,28,28,1.25,'Ascension')
ON DUPLICATE KEY UPDATE name=VALUES(name),race=VALUES(race),lastname=VALUES(lastname);
INSERT IGNORE INTO spawngroup (id,name,spawn_limit,dist,max_x,min_x,max_y,min_y,delay,mindelay,despawn,despawn_timer) VALUES (999226,'PoK_EpicForgemaster',1,0,0,0,0,0,0,15000,0,100);
INSERT IGNORE INTO spawnentry (spawngroupID,npcID,chance) VALUES (999226,999226,100);
INSERT IGNORE INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime,variance,pathgrid,animation) VALUES (999226,'poknowledge',0,368,250,-125,128,86400,0,0,0);

-- Essence global drop: ~1% on any NPC level 55+
INSERT INTO lootdrop (id,name,min_expansion,max_expansion) VALUES (990001,'GLB-EssenceOfAscension',-1,-1) ON DUPLICATE KEY UPDATE name=VALUES(name);
DELETE FROM lootdrop_entries WHERE lootdrop_id=990001;
INSERT INTO lootdrop_entries (lootdrop_id,item_id,item_charges,equip_item,chance,disabled_chance,trivial_min_level,trivial_max_level,multiplier,npc_min_level,npc_max_level,min_expansion,max_expansion)
VALUES (990001,900000,1,0,1,0,0,0,1,0,0,-1,-1);
INSERT INTO loottable (id,name,mincash,maxcash,avgcoin,done,min_expansion,max_expansion) VALUES (990001,'GLB-EssenceOfAscension',0,0,0,0,-1,-1) ON DUPLICATE KEY UPDATE name=VALUES(name);
DELETE FROM loottable_entries WHERE loottable_id=990001;
INSERT INTO loottable_entries (loottable_id,lootdrop_id,multiplier,droplimit,mindrop,probability) VALUES (990001,990001,1,1,0,100);
DELETE FROM global_loot WHERE id=9001;
INSERT INTO global_loot (id,description,loottable_id,enabled,min_level,max_level,min_expansion,max_expansion)
VALUES (9001,'Essence of Ascension (lvl55+)',990001,1,55,999,-1,-1);

-- Tier upgrade-roll chances (out of 10000), read by the loot hook in NPC::AddLootDrop.
-- Rule names keep the original Rare/Epic/Legendary tokens (internal only, avoids a
-- C++ rebuild); they map to Polished/Exalted/Ascended respectively.
INSERT INTO rule_values (ruleset_id, rule_name, rule_value, notes) VALUES
 (1,'Zone:LootTierRareChance','1000','Tiered loot: /10000 chance to upgrade a drop to Polished (+200000)'),
 (1,'Zone:LootTierEpicChance','200','Tiered loot: /10000 chance to upgrade to Exalted (+400000)'),
 (1,'Zone:LootTierLegendaryChance','25','Tiered loot: /10000 chance to upgrade to Ascended (+600000)')
ON DUPLICATE KEY UPDATE rule_value=VALUES(rule_value), notes=VALUES(notes);
