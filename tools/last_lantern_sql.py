"""Generate guarded additive campaign SQL; never connect to a database."""
import json
from pathlib import Path
from epic05 import insert, load_catalog, migration_sql, refuse, task_rows
from dungeon_migration import ITEM_REFERENCES
from last_lantern_content import ROOT, OUT, REVISION, compile_items, compile_npcs, compile_tasks


def migration():
    original = load_catalog()
    sql = migration_sql(original)
    tasks, activities = task_rows(original)
    for table, rows in [('tasks', tasks), ('task_activities', activities)]:
        for row in rows:
            statement = insert(table, row) + '\n'
            assert sql.count(statement) == 1
            sql = sql.replace(statement, '')
    sql = sql.replace('BETWEEN 9500 AND 9507', 'BETWEEN 9500 AND 9515')
    tables = ('nightcap_lantern_control', 'nightcap_lantern_slots', 'nightcap_lantern_refits',
              'nightcap_lantern_runs', 'nightcap_lantern_members', 'nightcap_lantern_memorials')
    checks = [refuse("EXISTS (SELECT 1 FROM instance_list WHERE version=80) OR EXISTS (SELECT 1 FROM zone WHERE version=80)", 'Reserved scene version is occupied'),
              refuse("EXISTS (SELECT 1 FROM titles WHERE id=995501 OR title_set=995501)", 'Campaign title occupied'),
              refuse("(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('tasks','task_activities','spells_new','items','npc_types','spawn2','spawnentry','spawngroup','titles') AND engine='InnoDB')<>9", 'Transactional campaign content required'),
              refuse("EXISTS (SELECT 1 FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('tasks','task_activities','spells_new','items','npc_types','spawn2','spawnentry','spawngroup','titles'))", 'Unexpected campaign content trigger'),
              refuse("EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ("+
                     ','.join("'"+t+"'" for t in tables)+"))", 'Campaign schema exists; require operator review'),
              refuse('EXISTS (SELECT 1 FROM items WHERE id BETWEEN 964000 AND 964127)', 'Campaign armor IDs occupied'),
              refuse('EXISTS (SELECT 1 FROM npc_types WHERE id BETWEEN 998900 AND 998939)', 'Campaign NPC range occupied'),
              refuse('EXISTS (SELECT 1 FROM spawngroup WHERE id BETWEEN 998900 AND 998905)', 'Campaign spawn groups occupied'),
              refuse('EXISTS (SELECT 1 FROM spawnentry WHERE spawngroupID BETWEEN 998900 AND 998905 OR npcID BETWEEN 998900 AND 998939)', 'Campaign spawn entries occupied'),
              refuse('EXISTS (SELECT 1 FROM spawn2 WHERE id BETWEEN 9113000 AND 9113005 OR spawngroupID BETWEEN 998900 AND 998905)', 'Campaign spawn positions occupied'),
              refuse('EXISTS (SELECT 1 FROM completed_tasks WHERE taskid BETWEEN 9500 AND 9515)', 'Campaign history unexpectedly occupied'),
              refuse('EXISTS (SELECT 1 FROM character_tasks WHERE taskid BETWEEN 9500 AND 9515)', 'Campaign active Tasks unexpectedly occupied')]
    for table, column in [('inventory','item_id'), ('sharedbank','item_id'), ('guild_bank','item_id'),
                          ('character_parcels','item_id'), ('character_parcels_containers','item_id'),
                          ('character_corpse_items','item_id'), ('character_pet_inventory','item_id'),
                          ('character_pet_armor','item_id'), ('nightcap_bazaar_items','item_id'),
                          ('object_contents','itemid'), ('trader','item_id'), ('lootdrop_entries','item_id'),
                          ('merchantlist','item'), ('tradeskill_recipe_entries','item_id')]:
        checks.append(refuse(f'EXISTS (SELECT 1 FROM `{table}` WHERE `{column}`=900501 OR `{column}` BETWEEN 964000 AND 964127)', 'Campaign item references occupied: '+table))
    references={table:list(columns) for table,columns in ITEM_REFERENCES.items()}
    references['nightcap_bazaar_items']=['item_id']
    for table,columns in sorted(references.items()):
        for column in columns:
            exists=f"EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{column}')"
            conflict=f"EXISTS (SELECT 1 FROM `{table}` WHERE `{column}`=900501 OR `{column}` BETWEEN 964000 AND 964127)"
            checks.append('IF '+exists+' THEN '+refuse(conflict,'Reserved item reference collision: '+table+'.'+column)+' END IF;')
    schema = '''CREATE TABLE nightcap_lantern_control (
 id TINYINT UNSIGNED PRIMARY KEY, revision BIGINT UNSIGNED NOT NULL, enabled TINYINT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;
CREATE TABLE nightcap_lantern_slots (
 character_id INT UNSIGNED NOT NULL, armor_slot TINYINT UNSIGNED NOT NULL,
 item_id INT UNSIGNED NOT NULL, drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 PRIMARY KEY(character_id,armor_slot), UNIQUE KEY(drop_id)
) ENGINE=InnoDB;
CREATE TABLE nightcap_lantern_refits (
 request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 character_id INT UNSIGNED NOT NULL, armor_slot TINYINT UNSIGNED NOT NULL,
 input_id INT UNSIGNED NOT NULL, output_id INT UNSIGNED NOT NULL,
 inventory_before MEDIUMBLOB NOT NULL, inventory_after MEDIUMBLOB NOT NULL
) ENGINE=InnoDB;
CREATE TABLE nightcap_lantern_runs (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 instance_id SMALLINT UNSIGNED NOT NULL, instance_start INT UNSIGNED NOT NULL,
 scene TINYINT UNSIGNED NOT NULL, owner_id INT UNSIGNED NOT NULL,
 expires_at BIGINT UNSIGNED NOT NULL, revision BIGINT UNSIGNED NOT NULL,
 UNIQUE KEY(instance_id,instance_start)
) ENGINE=InnoDB;
CREATE TABLE nightcap_lantern_members (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 character_id INT UNSIGNED NOT NULL, PRIMARY KEY(run_id,character_id), KEY(character_id)
) ENGINE=InnoDB;
CREATE TABLE nightcap_lantern_memorials (
 character_id INT UNSIGNED PRIMARY KEY, inscription TINYINT UNSIGNED NOT NULL
) ENGINE=InnoDB;
'''
    assert sql.count('CREATE TABLE nightcap_epic05_control') == 1
    sql = sql.replace('CREATE TABLE nightcap_epic05_control', '\n'.join(checks)+'\n'+schema+'CREATE TABLE nightcap_epic05_control')
    rows = [insert('nightcap_lantern_control', dict(id=1, revision=REVISION, enabled=0)),
            insert('titles',dict(id=995501,title_set=995501,suffix='the Lanternbearer'))]
    tasks, activities = compile_tasks()
    rows += [insert('tasks', r) for r in tasks]
    rows += [insert('task_activities', r) for r in activities]
    rows += [insert('items', r) for r in compile_items()]
    rows += [insert('npc_types', r) for r in compile_npcs()]
    geometry = json.loads((OUT/'release-20261107/geometry.json').read_text())
    zones = {r['zone']:r['name'] for r in json.loads((OUT/'release-20261107/production-content.json').read_text())['zones']}
    for index, pose in enumerate(geometry['public']):
        npc = pose['npc']
        rows += [insert('spawngroup', dict(id=npc, name='Nightcap_Last_Lantern_'+str(npc))),
                 insert('spawnentry', dict(spawngroupID=npc,npcID=npc,chance=100,min_expansion=-1,max_expansion=-1)),
                 insert('spawn2', dict(id=9113000+index,spawngroupID=npc,zone=zones[pose['zone']],version=0,
                                      x=pose['x'],y=pose['y'],z=pose['z'],heading=pose['heading'],
                                      respawntime=300,_condition=0,cond_value=1,min_expansion=-1,max_expansion=-1))]
    sql=sql.replace('\nCOMMIT;', '\n'+'\n'.join(rows)+'\nCOMMIT;')
    return sql


def main():
    (OUT/'last-lantern-setup.sql').write_text(migration(),encoding='utf-8')
    (OUT/'last-lantern-enable.sql').write_text('START TRANSACTION;\nUPDATE tasks SET enabled=1 WHERE id BETWEEN 9500 AND 9515;\nUPDATE nightcap_epic05_control SET enabled=1 WHERE id=1 AND native_contract=1 AND catalog_version=1;\nUPDATE nightcap_lantern_control SET enabled=1 WHERE id=1 AND revision=2026110701;\nCOMMIT;\n')
    (OUT/'last-lantern-disable.sql').write_text('-- Forward recovery: retain the personal-item native policy and all player state.\nSTART TRANSACTION;\nUPDATE nightcap_lantern_control SET enabled=0 WHERE id=1;\nUPDATE nightcap_epic05_control SET enabled=0 WHERE id=1;\nUPDATE tasks SET enabled=0 WHERE id BETWEEN 9500 AND 9515;\nCOMMIT;\n')
    print('Generated guarded additive setup and preserving enable/disable scripts.')


if __name__=='__main__':main()
