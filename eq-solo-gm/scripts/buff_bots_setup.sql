-- =============================================================================
-- Buff bots (#29) — two hail-for-buffs NPCs in PoK, flanking the Chronicler
-- vendor cluster (which spans x 325-368, y 248-272).
--
--   999237 Matron_Restora  (free)  x=310 y=290  — SoW/HP/AC/regen/mana-regen,
--           spell rank scales with the hailing character's level bracket
--   999238 Magus_Goldwind  (paid)  x=390 y=290  — 100pp: all of the above plus
--           Bottle of Adventure III (21030): +50% XP, 2400 tics = 4 hours
--
-- Buff logic lives in quests/poknowledge/Matron_Restora.pl / Magus_Goldwind.pl.
-- Appearance tuples cloned from QA-proven PoK NPCs (999222 / 999221).
-- IDs 999237-999238 verified free in npc_types/spawngroup/spawnentry/spawn2
-- (2026-07-16).
--
-- Apply: docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < buff_bots_setup.sql
--        then restart the PoK zone (npc_types cached at zone boot).
-- =============================================================================

-- NPCs: clone appearance from existing custom PoK NPCs, strip merchant bits.
DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999222; -- Divine Loremaster look
UPDATE t_npc SET id=999237, name='Matron_Restora', lastname='Blessings', class=1, merchant_id=0;
DELETE FROM npc_types WHERE id=999237;
INSERT INTO npc_types SELECT * FROM t_npc;

DROP TEMPORARY TABLE IF EXISTS t_npc;
CREATE TEMPORARY TABLE t_npc AS SELECT * FROM npc_types WHERE id = 999221; -- Arcane Loremaster look
UPDATE t_npc SET id=999238, name='Magus_Goldwind', lastname='Premium Blessings', class=1, merchant_id=0;
DELETE FROM npc_types WHERE id=999238;
INSERT INTO npc_types SELECT * FROM t_npc;

DROP TEMPORARY TABLE IF EXISTS t_npc;

-- Spawns
DELETE FROM spawn2 WHERE spawngroupID IN (999237,999238);
DELETE FROM spawnentry WHERE spawngroupID IN (999237,999238);
DELETE FROM spawngroup WHERE id IN (999237,999238);

INSERT INTO spawngroup (id,name,spawn_limit,dist,max_x,min_x,max_y,min_y,delay,mindelay,despawn,despawn_timer) VALUES
  (999237,'PoK_BuffBot_Free',1,0,0,0,0,0,0,15000,0,100),
  (999238,'PoK_BuffBot_Paid',1,0,0,0,0,0,0,15000,0,100);

INSERT INTO spawnentry (spawngroupID,npcID,chance) VALUES
  (999237,999237,100),(999238,999238,100);

INSERT INTO spawn2 (spawngroupID,zone,version,x,y,z,heading,respawntime,variance,pathgrid,animation) VALUES
  (999237,'poknowledge',0,310,290,-125,128,86400,0,0,0),
  (999238,'poknowledge',0,390,290,-125,128,86400,0,0,0);

SELECT id, name, lastname, class FROM npc_types WHERE id IN (999237,999238);
