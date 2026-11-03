-- Remove NPC Death Touch: Cazic Touch (982, 3087, 7477) and Touch of Vinitras (2859)
-- from every NPC spell list. Rows are kept in a backup table for rollback.sql.
-- Fails (instead of overwriting the backup) if run twice.
-- Apply, then restart zones: npc_spells is loaded at zone boot, #repop is not enough.
CREATE TABLE nightcap_death_touch_backup_20261103 AS
  SELECT * FROM npc_spells_entries WHERE spellid IN (982, 2859, 3087, 7477);
DELETE FROM npc_spells_entries WHERE spellid IN (982, 2859, 3087, 7477);
SELECT (SELECT COUNT(*) FROM nightcap_death_touch_backup_20261103) AS backed_up,
       (SELECT COUNT(*) FROM npc_spells_entries WHERE spellid IN (982, 2859, 3087, 7477)) AS remaining;
