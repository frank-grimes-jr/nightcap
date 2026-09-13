-- =============================================================================
-- Spell vendor split (#21) — RoF2 merchant window caps at 500 items
--   (common/patches/rof2_limits.h: MERCHANT_SIZE = 500; client_process.cpp:850/856).
-- The Arcane (776), Divine (687) and Stalwart (681) Loremasters exceed it, so items
-- past slot 500 never reach the client — the caster vendor visibly stopped at ~"M"
-- (504 of its 776 items sort before "Spell: N").
--
-- Fix: a second "II" vendor per over-cap archetype. This file creates the 3 NPCs +
-- spawns (a back row behind the originals). vendor_restock.sql moves each over-cap
-- vendor's second alphabetical half onto its II partner.
--
-- Apply: docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < spell_vendor_split.sql
--        then re-run vendor_restock.sql, then restart the PoK zone.
--
-- IDs: NPCs 999234-999236, merchant_ids 99251-99253 (verified free 2026-07-16).
-- =============================================================================

-- --- NPCs: clone each base Loremaster's appearance (npc_types has 100+ cols) ---
DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999221; -- Arcane
UPDATE t_npc SET id=999234, name='Arcane_Loremaster_II',   lastname='Caster Spells (cont.)',  merchant_id=99251;
DELETE FROM npc_types WHERE id=999234;
INSERT INTO npc_types SELECT * FROM t_npc;

DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999222; -- Divine
UPDATE t_npc SET id=999235, name='Divine_Loremaster_II',   lastname='Priest Spells (cont.)',  merchant_id=99252;
DELETE FROM npc_types WHERE id=999235;
INSERT INTO npc_types SELECT * FROM t_npc;

DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999224; -- Stalwart
UPDATE t_npc SET id=999236, name='Stalwart_Loremaster_II', lastname='Knight Spells (cont.)',  merchant_id=99253;
DELETE FROM npc_types WHERE id=999236;
INSERT INTO npc_types SELECT * FROM t_npc;

DROP TEMPORARY TABLE IF EXISTS t_npc;

-- --- Spawns: back row (y+8) behind each partner ---
INSERT IGNORE INTO spawngroup (id,name,spawn_limit,dist,max_x,min_x,max_y,min_y,delay,mindelay,despawn,despawn_timer) VALUES
  (999234,'PoK_KeeperArcaneTomes_II',1,0,0,0,0,0,0,15000,0,100),
  (999235,'PoK_KeeperDivineTomes_II',1,0,0,0,0,0,0,15000,0,100),
  (999236,'PoK_KeeperStalwartTomes_II',1,0,0,0,0,0,0,15000,0,100);

INSERT IGNORE INTO spawnentry (spawngroupID,npcID,chance) VALUES
  (999234,999234,100),(999235,999235,100),(999236,999236,100);

INSERT IGNORE INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime,variance,pathgrid,animation) VALUES
  (999234,'poknowledge',0,325,272,-125,128,86400,0,0,0),
  (999235,'poknowledge',0,332,264,-125,128,86400,0,0,0),
  (999236,'poknowledge',0,355,272,-125,128,86400,0,0,0);

SELECT id, name, lastname, merchant_id FROM npc_types WHERE id IN (999234,999235,999236);
