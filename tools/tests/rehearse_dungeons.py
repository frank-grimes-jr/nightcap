"""Rehearse dungeon installation in a new, isolated local MariaDB database.

Copies only captured public content into empty schema clones. Never writes PEQ
or copies players/accounts. Retains the isolated database and JSON evidence.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_migration import insert

def query(sql,database,check=True):
    assert re.fullmatch(r'nightcap_dungeon_rehearsal_[0-9a-f]{12}|information_schema',database)
    p=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-lc',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw '+database],
        input=sql,text=True,capture_output=True)
    if check and p.returncode:raise RuntimeError(p.stderr[-5000:])
    return p

def main():
    name='nightcap_dungeon_rehearsal_'+uuid.uuid4().hex[:12]
    print('Isolated rehearsal database: '+name,flush=True)
    data=json.loads((ROOT/'docs/dungeons/local-content.json').read_text())
    target=json.loads((ROOT/'docs/dungeons/target-content.json').read_text())
    payload=json.loads((ROOT/'docs/dungeons/install-rows.json').read_text())
    tables=set(target['ddl'])|{'spawn2','faction_list','doors','inventory','character_evolving_items','character_data','character_corpses'}
    query('CREATE DATABASE `'+name+'` CHARACTER SET utf8mb4;', 'information_schema')
    for table in sorted(tables):query(f'CREATE TABLE `{table}` LIKE peq.`{table}`;',name)
    for table in ('spawn2','spawnentry','spawngroup','npc_types','doors'):
        query('\n'.join(insert(table,r) for r in data[table]),name)
    # Only the native loot identities used by the donor, never character items.
    query('\n'.join(insert('items',r) for r in target['items']),name)
    query('\n'.join(insert('faction_list',r) for r in target['faction_list']),name)
    claims=(ROOT/'server-mods/sql/20260930_advanced_loot.sql').read_text()
    claims=re.search(r'CREATE TABLE character_advloot_claims \(.*?ENGINE=InnoDB;',claims,re.S)[0]
    query(claims,name)
    schema=(ROOT/'server-mods/sql/20261016_dungeons.sql').read_text()
    query(schema,name)
    before={t:query(f'CHECKSUM TABLE `{t}` EXTENDED;',name).stdout.strip()
            for t in ('spawn2','doors','character_data','inventory')}
    migration=(ROOT/'server-mods/sql/20261016_dungeon_content.sql').read_text()
    query(migration,name)
    counts={table:int(query(f'SELECT COUNT(*) FROM `{table}`;',name).stdout.strip()) for table in payload}
    assert counts['nightcap_dungeon_spawns']==188 and counts['tasks']==14 and counts['task_activities']==118
    assert int(query('SELECT COUNT(*) FROM items WHERE id BETWEEN 960000 AND 960329;',name).stdout)==330
    assert query('SELECT enabled FROM nightcap_dungeon_state;',name).stdout.strip()=='0'
    after={t:query(f'CHECKSUM TABLE `{t}` EXTENDED;',name).stdout.strip() for t in before}
    assert before==after,'Public spawn, door or player data changed'
    second=query(migration,name,False)
    assert second.returncode and 'Reserved identity collision' in second.stderr,'Repeat install did not fail closed'
    assert counts=={table:int(query(f'SELECT COUNT(*) FROM `{table}`;',name).stdout.strip()) for table in payload}
    # Real transaction failure: no partial death/credit may escape rollback.
    run=str(uuid.uuid4());receipt=str(uuid.uuid4())
    query(f"INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES ('{run}',60000,1,36,1,1,42,2026101601,9999999999);\n"
          f"INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES ('{run}',1,960001,'{receipt}');",name)
    query(f"START TRANSACTION; INSERT INTO nightcap_dungeon_deaths VALUES ('{run}',7011); INSERT INTO nightcap_dungeon_kills VALUES ('{run}',1,1); ROLLBACK;",name)
    assert query('SELECT COUNT(*) FROM nightcap_dungeon_deaths;',name).stdout.strip()=='0'
    assert query('SELECT COUNT(*) FROM nightcap_dungeon_kills;',name).stdout.strip()=='0'
    # Both modes retain independently identified corpses from successive deaths
    # at one spawn. The short native marker must fit the actual native schema.
    corpse1=str(uuid.uuid4());corpse2=str(uuid.uuid4())
    query(f"START TRANSACTION; INSERT INTO nightcap_dungeon_respawns VALUES ('{run}',7011,200000,100000); INSERT INTO nightcap_dungeon_corpses VALUES ('{run}',7011,'{corpse1}','{{}}',9999999999); ROLLBACK;",name)
    assert query('SELECT COUNT(*) FROM nightcap_dungeon_respawns;',name).stdout.strip()=='0'
    assert query('SELECT COUNT(*) FROM nightcap_dungeon_corpses;',name).stdout.strip()=='0'
    query(f"INSERT INTO nightcap_dungeon_corpses VALUES ('{run}',7011,'{corpse1}','{{}}',9999999999),('{run}',7011,'{corpse2}','{{}}',9999999999);",name)
    assert query('SELECT COUNT(*) FROM nightcap_dungeon_corpses;',name).stdout.strip()=='2'
    query(f"INSERT INTO instance_list(id,zone,version,start_time,duration,notes) VALUES (60000,36,0,1,43200,'nc-dungeon:{run}');",name)
    assert query('SELECT LENGTH(notes) FROM instance_list WHERE id=60000;',name).stdout.strip()=='47'
    assert query(f"SELECT COUNT(*) FROM nightcap_dungeon_runs r JOIN instance_list i ON i.id=r.instance_id AND i.start_time=r.instance_start AND i.notes=CONCAT('nc-dungeon:',r.run_id);",name).stdout.strip()=='1'
    query("UPDATE instance_list SET start_time=2,notes='legacy-reused' WHERE id=60000;",name)
    assert query("SELECT COUNT(*) FROM nightcap_dungeon_runs r JOIN instance_list i ON i.id=r.instance_id AND i.start_time=r.instance_start AND i.notes=CONCAT('nc-dungeon:',r.run_id);",name).stdout.strip()=='0'
    query(f"START TRANSACTION; INSERT INTO nightcap_dungeon_deaths VALUES ('{run}',7011); INSERT INTO nightcap_dungeon_kills VALUES ('{run}',1,1); COMMIT;",name)
    duplicate=query(f"INSERT INTO nightcap_dungeon_deaths VALUES ('{run}',7011);",name,False)
    assert duplicate.returncode and 'Duplicate entry' in duplicate.stderr
    query(f"UPDATE nightcap_dungeon_members SET completed_at=1 WHERE run_id='{run}'; UPDATE nightcap_dungeon_runs SET retired=1,expires_at=1 WHERE run_id='{run}';",name)
    assert query(f"SELECT reward_item,reward_drop_id FROM nightcap_dungeon_members WHERE run_id='{run}' AND completed_at>0;",name).stdout.strip()==f'960001\t{receipt}'
    evidence={'database':name,'scope':'isolated local content/schema rehearsal; no server or gameplay acceptance',
              'migration_sha256':hashlib.sha256(migration.encode()).hexdigest(),'schema_sha256':hashlib.sha256(schema.encode()).hexdigest(),'counts':counts,
              'public_and_player_preservation':before==after,'repeat_install_rejected':True,
              'death_rollback_atomic':True,'duplicate_death_rejected':True,'earned_claim_retained_after_retirement':True,
              'grind_corpse_timer_rollback_atomic':True,'successive_corpses_coexist':True,'native_marker_fits':True,'instance_reuse_rejected':True}
    (ROOT/'docs/dungeons/rehearsal.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))

if __name__=='__main__':main()
