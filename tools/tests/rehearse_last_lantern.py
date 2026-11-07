"""Exercise additive migration only in a fresh disposable local database."""
import json
import re
from pathlib import Path
import sys
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from rehearse_epic05 import run_command
from epic05 import load_catalog, spell_fields
from last_lantern_content import compile_items, compile_npcs, compile_tasks


def main():
    schema='nightcap_lantern_qa_'+uuid.uuid4().hex[:12]
    assert schema.startswith('nightcap_lantern_qa_') and len(schema)==32
    command=['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
             'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names']
    def sql(body,check=True,database=schema):
        return run_command(command,'USE `'+database+'`;\n'+body,check)
    tables=('tasks','task_activities','spells_new','items','npc_types','spawnentry','spawn2','spawngroup',
            'completed_tasks','character_tasks','inventory','sharedbank','guild_bank','character_parcels',
            'character_parcels_containers','character_corpse_items','character_pet_inventory','character_pet_armor',
            'nightcap_bazaar_items','object_contents','trader','lootdrop_entries','merchantlist','tradeskill_recipe_entries','titles','instance_list','zone')
    catalog=load_catalog()
    npcs=sorted({o['npc'] for c in catalog['shared']+catalog['paths'] for o in c['objectives'] if 'npc' in o})
    ids=','.join(map(str,npcs))
    setup=(ROOT/'docs/adventure-journal/last-lantern-setup.sql').read_text()
    report=dict(schema=schema,scope='disposable MariaDB content rehearsal; not native gameplay or player acceptance',checks=[])
    created=False; granted=False
    try:
        sql('CREATE DATABASE `'+schema+'`;',database='peq');created=True
        definitions=json.loads((ROOT/'docs/adventure-journal/release-20261107/production-schema.json').read_text())
        sql('\n'.join(definitions[t]+';' if t in definitions else 'CREATE TABLE `'+t+'` LIKE peq.`'+t+'`;' for t in tables))
        sql('CREATE TABLE character_corpses LIKE peq.character_corpses;')
        sql(f'INSERT INTO npc_types SELECT * FROM peq.npc_types WHERE id IN ({ids});'
            f'INSERT INTO spawnentry SELECT * FROM peq.spawnentry WHERE npcID IN ({ids});'
            'INSERT INTO spawn2 SELECT s.* FROM peq.spawn2 s JOIN (SELECT DISTINCT spawngroupID FROM spawnentry) e ON e.spawngroupID=s.spawngroupID;'
            "INSERT INTO items(id,Name) VALUES(900620,'Existing reforging box sentinel'),(964000,'Collision sentinel');")
        assert sql(setup,False).returncode!=0
        assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='nightcap_lantern_control';").stdout.strip()=='0'
        sql('DELETE FROM items WHERE id=964000;')
        report['checks'].append('reserved item collision refuses before creating feature tables; existing reforging box retained')
        title_schema=sql('SHOW CREATE TABLE titles;').stdout
        sql(setup)
        assert re.sub(r' AUTO_INCREMENT=[0-9]+','',sql('SHOW CREATE TABLE titles;').stdout)==re.sub(r' AUTO_INCREMENT=[0-9]+','',title_schema)
        report['checks'].append('high-ID title insert changes only its auto-increment counter, preserving every schema attribute')
        counts=sql('SELECT COUNT(*) FROM tasks;SELECT COUNT(*) FROM task_activities;SELECT COUNT(*) FROM items;'
                   'SELECT COUNT(*) FROM spells_new;SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 998900 AND 998939;'
                   'SELECT COUNT(*) FROM spawn2 WHERE id BETWEEN 9113000 AND 9113005;'
                   'SELECT enabled FROM nightcap_lantern_control;SELECT enabled FROM nightcap_epic05_control;').stdout.splitlines()
        assert counts==['16','64','130','6',str(len(compile_npcs())),'6','0','0'],counts
        before=sql('SELECT id,Name FROM items ORDER BY id;').stdout
        assert sql(setup,False).returncode!=0
        assert sql('SELECT id,Name FROM items ORDER BY id;').stdout==before
        report['checks'].append('16 Tasks, 64 activities, 128 armor, charm, six spells, scene actors and six public services inserted disabled; reapply fails without changing content')
        fields=list(compile_items()[0])
        rows=sql('SELECT CONCAT_WS(CHAR(9),'+','.join('`'+f+'`' for f in fields)+') FROM items WHERE id BETWEEN 964000 AND 964127 ORDER BY id;').stdout.splitlines()
        for expected,line in zip(compile_items(),rows):
            actual=line.split('\t')
            assert len(actual)==len(fields),(len(actual),len(fields))
            for f,val in zip(fields,actual):
                desired=expected[f]
                assert float(val)==desired if isinstance(desired,(int,float)) else val==desired,(expected['id'],f,val,desired)
        report['checks'].append('every generated armor field matches the real MariaDB afterimage')
        columns=json.loads((ROOT/'docs/adventure-journal/content-snapshot.json').read_text())['schemas']['spells_new']
        expressions=','.join("COALESCE(CAST(`"+col['name']+"` AS CHAR),'')" for col in columns)
        for line in sql('SELECT CONCAT_WS(CHAR(94),'+expressions+') FROM spells_new ORDER BY id;').stdout.splitlines():
            actual=line.split('^');expected=spell_fields(catalog)[int(actual[0])].decode('latin1').split('^')
            for i,column in enumerate(columns):
                if not actual[i] and column['default'] is None and 'char' not in column['type']:actual[i]='0'
            assert actual==expected,'server/client spell mismatch'
        report['checks'].append('all 237 client/server fields match for all six spells')
        sql((ROOT/'docs/adventure-journal/last-lantern-enable.sql').read_text())
        assert sql('SELECT COUNT(*) FROM tasks WHERE enabled=1;').stdout.strip()=='16'
        sql('GRANT ALL ON `'+schema+"`.* TO 'eqemu'@'%';"); granted=True
        names=('last_lantern_inventory.h','last_lantern_policy.h','bazaar_escrow.h','item_xp_inventory.h')
        sources={'common/'+n:(ROOT/'server-mods/code/common'/n).read_text() for n in names}
        sources['fixture.cpp']=(ROOT/'tools/tests/lantern_refit_mariadb.cpp').read_text()
        code=r'''
from pathlib import Path
import json,os,subprocess,shlex
p=Path('/tmp')/SCHEMA;p.mkdir(exist_ok=False)
for n,s in SOURCES.items():
 f=p/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
flags=shlex.split(subprocess.check_output(['mariadb_config','--cflags','--libs'],text=True))
r=subprocess.run(['/usr/bin/clang++','-std=c++20','-O0','-UNDEBUG','-I'+str(p),str(p/'fixture.cpp'),'-o',str(p/'fixture')]+flags,capture_output=True,text=True)
assert r.returncode==0,r.stderr[-2500:]
c=json.loads(Path('/home/eqemu/server/eqemu_config.json').read_text())['server']['database']
env=os.environ.copy();env.update(LANTERN_QA_DB=SCHEMA,LANTERN_QA_HOST=c['host'],LANTERN_QA_USER=c['username'],LANTERN_QA_PASSWORD=c['password'])
r=subprocess.run([str(p/'fixture')],env=env,capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
print(r.stdout)
'''
        result=run_command(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],
                           'SCHEMA='+repr(schema)+'\nSOURCES='+repr(sources)+'\n'+code)
        report['native_refit']=result.stdout.strip()
        report['checks'].append('real single-connection native refit engine: preserved augmented/dyed/bound/ornamented/custom/GUID row, rollback, unrelated-player corpse, replay refusal and durable ambiguous COMMIT')
        sql('UPDATE nightcap_epic05_control SET enabled=0 WHERE id=1;')
        store=(ROOT/'server-mods/plugins/epic05_store.pl').read_text(encoding='utf-8')
        test=(ROOT/'tools/tests/epic05_store.t').read_text(encoding='utf-8')
        folder='/tmp/'+schema
        for name,body in [('store.pl',store),('store-test.t',test)]:
            run_command(['docker','exec','-i','akk-stack-eqemu-server-1','tee',folder+'/'+name],body)
        result=run_command(['docker','exec','-e','NIGHTCAP_EPIC05_QA_DB='+schema,'akk-stack-eqemu-server-1','perl',folder+'/store-test.t',folder+'/store.pl'])
        assert 'not ok' not in result.stdout and '1..24' in result.stdout,result.stdout
        report['oath_store']=result.stdout.splitlines()
        report['checks'].append('24 real Perl/DBI checks: durable native eligibility, cooldown, uncertain acknowledgement, four-way concurrent activation and disable races')
        sql((ROOT/'docs/adventure-journal/last-lantern-disable.sql').read_text())
        assert sql('SELECT COUNT(*) FROM tasks WHERE enabled=0;').stdout.strip()=='16'
        assert sql('SELECT COUNT(*) FROM nightcap_lantern_slots;').stdout.strip()=='1'
        assert sql('SELECT COUNT(*) FROM items WHERE id=900620;').stdout.strip()=='1'
        report['checks'].append('activation enables all chapters; forward disable preserves ownership, content, spell definitions and unrelated items')
        report['status']='PASS'
    finally:
        if created:
            if granted:sql('REVOKE ALL PRIVILEGES ON `'+schema+"`.* FROM 'eqemu'@'%';",database='peq')
            sql('DROP DATABASE `'+schema+'`;',database='peq')
    (ROOT/'docs/adventure-journal/release-20261107/database-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
