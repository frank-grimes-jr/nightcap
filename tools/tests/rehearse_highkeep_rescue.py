"""Rehearse actual DDL and native completion SQL in an owned, disposable MariaDB."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/dungeons/highkeep-rescue'


def main():
    name = 'nightcap-highkeep-rehearsal-' + uuid.uuid4().hex[:12]
    image = subprocess.check_output(['docker', 'inspect', '--format', '{{.Config.Image}}',
                                     'akk-stack-mariadb-1'], text=True).strip()
    container_id = subprocess.check_output(['docker', 'run', '-d', '--name', name,
        '--label', 'nightcap.highkeep-rehearsal=' + name, '--network', 'none',
        '--memory', '512m', '--cpus', '1', '--tmpfs', '/var/lib/mysql:rw',
        '-e', 'MYSQL_ALLOW_EMPTY_PASSWORD=yes', image], text=True).strip()

    def query(sql, database='information_schema', check=True):
        assert database in ('information_schema', 'highkeep_test')
        r = subprocess.run(['docker', 'exec', '-i', container_id, 'mariadb', '-uroot',
                            '-N', '-B', '--raw', database], input=sql, text=True, capture_output=True)
        if check and r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        return r

    try:
        for _ in range(45):
            process = subprocess.run(['docker', 'exec', container_id, 'cat', '/proc/1/comm'],
                                     text=True, capture_output=True)
            if process.stdout.strip() in ('mysqld', 'mariadbd') and not query('SELECT 1;', check=False).returncode:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Disposable MariaDB did not start')
        query('CREATE DATABASE highkeep_test;')
        ddl = (ROOT / 'server-mods/sql/20261024_highkeep_rescue.sql').read_text()
        query(ddl, 'highkeep_test')
        assert query('SELECT enabled FROM nightcap_highkeep_state;', 'highkeep_test').stdout.strip() == '0'
        original = (ROOT / 'server-mods/sql/20261016_dungeons.sql').read_text()
        for table in ('runs', 'members', 'kills'):
            start = original.index('CREATE TABLE nightcap_dungeon_' + table)
            query(original[start:original.index(';', start) + 1], 'highkeep_test')
        run = '00000000-0000-4000-8000-000000000001'
        query(f"INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES ('{run}',1,100,6,1,1,1,2026101601,10000);\n"
              f"INSERT INTO nightcap_highkeep_runs(run_id) VALUES ('{run}');", 'highkeep_test')
        for character, count in ((1, 4), (2, 3)):
            receipt = f'00000000-0000-4000-8000-{character:012d}'
            query(f"INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES ('{run}',{character},1,'{receipt}');\n" +
                  '\n'.join(f"INSERT INTO nightcap_dungeon_kills VALUES ('{run}',{character},{boss});" for boss in range(1, count + 1)), 'highkeep_test')
        # Extract the actual SQL expression, not a hand-maintained copy of eligibility.
        source = (ROOT / 'server-mods/code/zone/highkeep_rescue.inc').read_text()
        match = re.search(r'Query\(fmt::format\(("UPDATE nightcap_dungeon_members.*?),Now\(\),Q\(run.id\),c->CharacterID\(\)\)\)', source, re.S)
        assert match
        statement = ''.join(re.findall(r'"([^"\n]*)"', match[1]))
        def complete(character):
            return statement.format(500, "'" + run + "'", character) + ';'
        rescue = f"UPDATE nightcap_highkeep_runs SET rescued_at=500 WHERE run_id='{run}';"
        query('START TRANSACTION;' + complete(1) + rescue + 'ROLLBACK;', 'highkeep_test')
        assert query('SELECT SUM(completed_at) FROM nightcap_dungeon_members; SELECT rescued_at FROM nightcap_highkeep_runs;', 'highkeep_test').stdout.split() == ['0', '0']
        result = query('START TRANSACTION;' + complete(1) + 'SELECT ROW_COUNT();' + complete(2) +
                       'SELECT ROW_COUNT();' + rescue + 'COMMIT;' + complete(1) + 'SELECT ROW_COUNT();', 'highkeep_test')
        assert result.stdout.split() == ['1', '0', '0'], result.stdout
        query('UPDATE nightcap_highkeep_state SET enabled=1; UPDATE nightcap_highkeep_runs SET alarm=1; UPDATE nightcap_highkeep_state SET enabled=0;', 'highkeep_test')
        before = query('SELECT * FROM nightcap_highkeep_runs; SELECT character_id,completed_at,reward_drop_id FROM nightcap_dungeon_members ORDER BY character_id;', 'highkeep_test').stdout
        assert query(ddl, 'highkeep_test', False).returncode
        assert before == query('SELECT * FROM nightcap_highkeep_runs; SELECT character_id,completed_at,reward_drop_id FROM nightcap_dungeon_members ORDER BY character_id;', 'highkeep_test').stdout
        assert query('UPDATE nightcap_highkeep_state SET enabled=2;', 'highkeep_test', False).returncode
        assert query('UPDATE nightcap_highkeep_runs SET alarm=2;', 'highkeep_test', False).returncode
        assert query(f"INSERT INTO nightcap_highkeep_runs(run_id) VALUES ('{run}');", 'highkeep_test', False).returncode
        report = dict(status='passed', database='owned disposable MariaDB; removed after test',
                      default_disabled=True, personal_credit=True, completion_replay_refused=True,
                      transaction_rollback=True, repeated_install_refused=True, pause_preserves_progress=True,
                      constraints=True, production_changed=False, migration_sha256=hashlib.sha256(ddl.encode()).hexdigest(),
                      coordinator_sha256=hashlib.sha256(source.encode()).hexdigest())
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'sql-rehearsal.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        owned = json.loads(subprocess.check_output(['docker', 'inspect', container_id]))[0]
        assert owned['Id'] == container_id and owned['Config']['Labels']['nightcap.highkeep-rehearsal'] == name
        subprocess.run(['docker', 'rm', '-f', container_id], check=True, capture_output=True)


if __name__ == '__main__':
    main()
