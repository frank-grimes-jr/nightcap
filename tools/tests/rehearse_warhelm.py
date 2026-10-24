"""Actual migration failure/replay checks in a new disposable local schema."""
import hashlib,json,sys,uuid,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_migration import insert
from rehearse_dungeons import query as source_query

CONTAINER='nightcap-kael-rehearsal'
def query(sql,database,check=True):
    assert database=='information_schema' or database.startswith('nightcap_dungeon_rehearsal_')
    p=subprocess.run(['docker','exec','-i',CONTAINER,'mariadb','-uroot','-N','-B','--raw',database],input=sql,text=True,capture_output=True)
    if check and p.returncode:raise RuntimeError(p.stderr[-3000:])
    return p

def main():
    out=ROOT/'docs/quests/warhelm'
    source=json.loads((out/'local-content.json').read_text())
    hazards=json.loads((out/'secondary-content.json').read_text())
    rows=json.loads((out/'install-rows.json').read_text())
    name='nightcap_dungeon_rehearsal_'+uuid.uuid4().hex[:12]
    print('Isolated schema: '+name,flush=True)
    found=subprocess.run(['docker','inspect',CONTAINER],capture_output=True)
    if found.returncode:
        image=subprocess.check_output(['docker','inspect','--format','{{.Config.Image}}','akk-stack-mariadb-1'],text=True).strip()
        subprocess.run(['docker','run','-d','--name',CONTAINER,'--network','none','--memory','512m','--cpus','1',
                        '--tmpfs','/var/lib/mysql:rw','-e','MYSQL_ALLOW_EMPTY_PASSWORD=yes',image],check=True,capture_output=True)
    elif json.loads(found.stdout)[0]['State']['Status']!='running':
        subprocess.run(['docker','start',CONTAINER],check=True,capture_output=True)
    for attempt in range(30):
        # Old logs survive a Docker restart; the temporary initialization server
        # also answers SELECT 1. Wait until the final daemon owns PID 1.
        process=subprocess.run(['docker','exec',CONTAINER,'cat','/proc/1/comm'],text=True,capture_output=True)
        if process.stdout.strip() in ('mysqld','mariadbd') and query('SELECT 1;','information_schema',False).returncode==0:break
        time.sleep(1)
    else:raise RuntimeError('Isolated rehearsal server did not become ready')
    query(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4;','information_schema')
    tables=set(rows)|set(hazards)|{'zone','doors','character_tasks','character_activities','completed_tasks','tasksets','content_flags','zone_state_spawns','inventory'}
    # Local PEQ predates the native dungeon schema; use its reviewed DDL only.
    for table in sorted(tables-{'nightcap_dungeon_spawns'}):
        ddl=source_query(f'SHOW CREATE TABLE peq.`{table}`;','information_schema').stdout.split('\t',1)[1].strip()
        query(ddl+';',name)
    schema=(ROOT/'server-mods/sql/20261016_dungeons.sql').read_text()
    start=schema.index('CREATE TABLE nightcap_dungeon_spawns')
    query(schema[start:schema.index(';',start)+1],name)
    query((ROOT/'server-mods/sql/20261024_warhelm_schema.sql').read_text(),name)
    for table in ('zone','spawn2','doors'):
        query('\n'.join(insert(table,r) for r in source[table]),name)
    for table,values in hazards.items():query('\n'.join(insert(table,r) for r in values),name)
    query("INSERT INTO nightcap_ashen_characters VALUES (42,1,100,0,'0-0-4000-8000-42');",name)
    migration=(ROOT/'server-mods/sql/20261024_warhelm_content.sql').read_text()
    def digest():
        return {t:query('CHECKSUM TABLE `'+t+'` EXTENDED;',name).stdout.strip().split('\t')[-1]
                for t in ('zone','spawn2','doors','ground_spawns','nightcap_ashen_characters')}
    before=digest()
    query('INSERT INTO inventory(character_id,slot_id,item_id) VALUES(4242,22,961020);',name)
    item_collision=query(migration,name,False)
    assert item_collision.returncode and 'Reserved item reference inventory.item_id' in item_collision.stderr,item_collision.stderr
    query('DELETE FROM inventory WHERE character_id=4242; DROP PROCEDURE nightcap_warhelm_20261024;',name)
    query('INSERT INTO tasksets(id,taskid) VALUES(4242,9801);',name)
    collision=query(migration,name,False)
    assert collision.returncode and 'Reserved task reference' in collision.stderr,collision.stderr
    query('DELETE FROM tasksets WHERE id=4242; DROP PROCEDURE nightcap_warhelm_20261024;',name)
    fault=migration.replace('COMMIT;',"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic failure'; COMMIT;")
    failure=query(fault,name,False)
    assert failure.returncode and 'synthetic failure' in failure.stderr,failure.stderr
    assert digest()==before
    assert query('SELECT COUNT(*) FROM items;',name).stdout.strip()=='0'
    query('DROP PROCEDURE nightcap_warhelm_20261024;',name)
    query(migration,name)
    checks=json.loads((out/'runtime-checks.json').read_text())
    results=query(';\n'.join(c['sql'] for c in checks)+';',name).stdout.strip().splitlines()
    assert len(results)==len(checks)
    assert all(value==c['expected'] for c,value in zip(checks,results)),[(c['label'],value) for c,value in zip(checks,results) if value!=c['expected']]
    assert digest()['nightcap_ashen_characters']==before['nightcap_ashen_characters']
    after=digest();repeat=query(migration,name,False)
    assert repeat.returncode and 'Reserved identity collision' in repeat.stderr,repeat.stderr
    assert after==digest()
    import dungeon_contract
    dungeon_contract.TABLES=['nightcap_ashen_state','nightcap_ashen_characters']
    metadata=dungeon_contract.schema_checks()
    values=query(';\n'.join(c['sql'] for c in metadata)+';',name).stdout.strip().splitlines()
    assert len(values)==len(metadata)
    for c,v in zip(metadata,values):c['expected']=v
    (out/'schema-checks.json').write_text(json.dumps(metadata,indent=2)+'\n')
    report=dict(status='passed isolated MariaDB rehearsal',database=name,content_checks=len(checks),
        task_reference_collision=True,item_reference_collision=True,mid_transaction_rollback=True,repeat_refused=True,
        campaign_progress_preserved=True,production_changed=False,
        migration_sha256=hashlib.sha256(migration.encode()).hexdigest())
    (out/'rehearsal.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
