-- Restore the NPC Death Touch spell-list rows removed by remove.sql, then restart zones.
INSERT INTO npc_spells_entries SELECT * FROM nightcap_death_touch_backup_20261103;
DROP TABLE nightcap_death_touch_backup_20261103;
