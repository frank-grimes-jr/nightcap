"""Rehearse Epic 0.5 only in a new disposable MariaDB schema; never modify PEQ."""
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from epic05 import load_catalog, task_rows, spell_fields


def run_command(arguments, body=None, check=True):
    result = subprocess.run(arguments, input=body, text=True, encoding='utf-8',
                            capture_output=True, timeout=120)
    if check and result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def main():
    schema = 'nightcap_epic05_qa_' + uuid.uuid4().hex[:12]
    command = ['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
               'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
               'exec mariadb -uroot --batch --raw --skip-column-names']
    def sql(text, database=schema, check=True):
        return run_command(command, 'USE `' + database + '`;\n' + text, check)
    catalog = load_catalog()
    npcs = sorted({o['npc'] for c in catalog['shared'] + catalog['paths'] for o in c['objectives'] if 'npc' in o})
    ids = ','.join(map(str,npcs))
    created = False
    granted = False
    evidence = {'scope':'isolated local MariaDB content and Perl/DBI boundary; not native gameplay',
                'schema':schema,'checks':[]}
    try:
        sql('CREATE DATABASE `' + schema + '`;', 'peq')
        created = True
        sql('GRANT ALL ON `' + schema + "`.* TO 'eqemu'@'%';")
        granted = True
        sql('\n'.join('CREATE TABLE `' + t + '` LIKE peq.`' + t + '`;' for t in
                      ['tasks','task_activities','spells_new','items','npc_types','spawnentry','spawn2']))
        sql(f'INSERT INTO npc_types SELECT * FROM peq.npc_types WHERE id IN ({ids});'
            f'INSERT INTO spawnentry SELECT * FROM peq.spawnentry WHERE npcID IN ({ids});'
            'INSERT INTO spawn2 SELECT s.* FROM peq.spawn2 s JOIN (SELECT DISTINCT spawngroupID FROM spawnentry) e ON e.spawngroupID=s.spawngroupID;'
            "INSERT INTO tasks(id,title,description) VALUES(1,'Unrelated sentinel','Preserve me');"
            "INSERT INTO items(id,Name) VALUES(1,'Unrelated sentinel');")
        setup = (ROOT/'docs/adventure-journal/setup.sql').read_text()
        sql("INSERT INTO items(id,Name) VALUES(900501,'Occupied');")
        rejected = sql(setup, check=False)
        assert rejected.returncode and 'Occupied Epic 0.5 item ID' in rejected.stderr, rejected.stderr
        assert sql('SELECT COUNT(*) FROM tasks;').stdout.strip() == '1'
        evidence['checks'].append('occupied ID refuses setup before content changes')
        sql('DELETE FROM items WHERE id=900501;')
        # An existing Classic identity with a later expansion spawn must fail.
        sql('UPDATE spawn2 SET min_expansion=4 WHERE spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID=73103);')
        rejected = sql(setup,check=False)
        assert rejected.returncode and 'Missing or changed encounter 73103' in rejected.stderr
        sql('UPDATE spawn2 SET min_expansion=-1 WHERE spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID=73103);')
        evidence['checks'].append('later-expansion spawn refuses setup')
        # A mid-transaction failure retains only empty DDL, never half the content.
        sql("CREATE TRIGGER epic05_fault BEFORE INSERT ON spells_new FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Injected write fault';")
        rejected = sql(setup,check=False)
        assert rejected.returncode and 'Injected write fault' in rejected.stderr
        counts = sql('SELECT COUNT(*) FROM tasks; SELECT COUNT(*) FROM task_activities; SELECT COUNT(*) FROM spells_new; SELECT COUNT(*) FROM nightcap_epic05_control; SELECT COUNT(*) FROM nightcap_epic05_state;').stdout.splitlines()
        assert counts == ['1','0','0','0','0'], counts
        sql('DROP TRIGGER epic05_fault; DROP TABLE nightcap_epic05_control,nightcap_epic05_state;')
        evidence['checks'].append('injected content-write failure rolls back every content row; empty DDL remains')
        sql(setup)
        counts = sql('SELECT COUNT(*) FROM tasks WHERE id BETWEEN 9500 AND 9507;'
                     'SELECT COUNT(*) FROM task_activities WHERE taskid BETWEEN 9500 AND 9507;'
                     'SELECT COUNT(*) FROM spells_new WHERE id BETWEEN 42800 AND 42805;'
                     'SELECT enabled FROM nightcap_epic05_control WHERE id=1;').stdout.splitlines()
        expected = ['8',str(len(task_rows(catalog)[1])),'6','0']
        assert counts == expected, (counts,expected)
        evidence['checks'].append('all content inserted; release disabled')
        assert sql(setup,check=False).returncode != 0
        evidence['checks'].append('reapplication refuses overwrite')
        # Compare every server spell field against the staged client schema.
        columns = json.loads((ROOT/'docs/adventure-journal/content-snapshot.json').read_text())['schemas']['spells_new']
        fields = ','.join("COALESCE(CAST(`" + col['name'] + "` AS CHAR),'')" for col in columns)
        rows = sql('SELECT CONCAT_WS(CHAR(94),' + fields + ') FROM spells_new WHERE id BETWEEN 42800 AND 42805 ORDER BY id;').stdout.splitlines()
        for row in rows:
            expected_row=spell_fields(catalog)[int(row.split('^',1)[0])].decode('latin1')
            # Nullable numeric defaults are exported as zero in the RoF2 format.
            actual=row.split('^'); expected_fields=expected_row.split('^')
            for index,column in enumerate(columns):
                if not actual[index] and column['default'] is None and 'char' not in column['type']:
                    actual[index]='0'
            assert actual == expected_fields, 'Client/server spell mismatch'
        evidence['checks'].append('all 237 server/client fields match for six spells')
        # Exercise the real Perl store against MariaDB through a DBI boundary adapter.
        store=(ROOT/'server-mods/plugins/epic05_store.pl').read_text()
        test=(ROOT/'tools/tests/epic05_store.t').read_text()
        container_dir='/tmp/'+schema
        run_command(['docker','exec','akk-stack-eqemu-server-1','mkdir','-p',container_dir])
        for name,body in [('store.pl',store),('test.t',test)]:
            run_command(['docker','exec','-i','akk-stack-eqemu-server-1','tee',container_dir+'/'+name],body)
        result=run_command(['docker','exec','-e','NIGHTCAP_EPIC05_QA_DB='+schema,
                            'akk-stack-eqemu-server-1','perl',container_dir+'/test.t',container_dir+'/store.pl'])
        assert 'not ok' not in result.stdout and '1..20' in result.stdout, result.stdout
        evidence['store_tests']=result.stdout.splitlines()
        evidence['checks'].append('Perl store: durable cooldown, SQL errors, uncertain acknowledgement, four-way concurrent reserve')
        before=sql('SELECT character_id,active_path,ready_at,uses FROM nightcap_epic05_state;').stdout
        sql((ROOT/'docs/adventure-journal/disable.sql').read_text())
        assert sql('SELECT character_id,active_path,ready_at,uses FROM nightcap_epic05_state;').stdout==before
        assert sql('SELECT COUNT(*) FROM tasks WHERE id BETWEEN 9500 AND 9507 AND enabled=0;').stdout.strip()=='8'
        assert sql('SELECT COUNT(*) FROM items WHERE id=900501;').stdout.strip()=='1'
        assert sql('SELECT COUNT(*) FROM spells_new WHERE id BETWEEN 42800 AND 42805;').stdout.strip()=='6'
        assert sql('SELECT title FROM tasks WHERE id=1;').stdout.strip()=='Unrelated sentinel'
        evidence['checks'].append('disable preserves attunement, cooldown, owned content definitions and unrelated rows')
        evidence['passed']=True
    finally:
        if created:
            if granted:
                sql('REVOKE ALL PRIVILEGES ON `' + schema + "`.* FROM 'eqemu'@'%';", 'peq')
            sql('DROP DATABASE `' + schema + '`;', 'peq')
    (ROOT/'docs/adventure-journal/database-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__': main()
