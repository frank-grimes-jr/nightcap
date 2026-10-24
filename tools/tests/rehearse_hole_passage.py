"""Rehearse on a unique disposable LOCAL database; never update local/live PEQ."""
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from hole_passage import generate, plan
from pok_hub_migration import insert


def rehearse():
    database = 'nightcap_hole_test_' + uuid.uuid4().hex[:12]
    def query(sql, fail=False):
        command = ['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-lc',
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw']
        result = subprocess.run(command, input=sql, text=True, capture_output=True, timeout=60)
        if fail:
            assert result.returncode != 0, 'Expected fail-closed rejection'
        elif result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout
    def run(sql, fail=False):
        return query('USE `' + database + '`;\n' + sql, fail)
    def snapshot():
        cols = list(capture['doors'][0])
        return [json.loads(line) for line in run('SELECT JSON_ARRAY(' +
                ','.join('`' + c + '`' for c in cols) + ') FROM doors ORDER BY id;').splitlines()]
    capture = json.loads((ROOT / 'docs/ops/hole-keyless-passage-20261024/production-before.json').read_text(encoding='utf-8-sig'))
    forward, rollback = generate(capture)
    checks = []
    query('CREATE DATABASE `' + database + '`;')
    try:
        run('CREATE TABLE doors LIKE peq.doors;\n' + '\n'.join(insert('doors', d) for d in capture['doors']))
        baseline = snapshot()
        run(forward)
        expected = [[row[c] for c in capture['doors'][0]] for row in plan(capture)['doors']]
        assert snapshot() == expected, 'Unexpected door change'
        checks.append('forward changes only entrance keyitem and lockpick across all captured doors')
        run(forward, fail=True)
        assert snapshot() == expected
        checks.append('repeat forward rejects without mutation')
        run(rollback)
        assert snapshot() == baseline
        checks.append('inverse restores every captured door exactly')
        for change in ["keyitem=6378", "lockpick=61", "name='parock105'", 'pos_x=pos_x+1']:
            run('UPDATE doors SET ' + change + ' WHERE id=10599;')
            before = snapshot()
            run(forward, fail=True)
            assert snapshot() == before
            run('DELETE FROM doors WHERE id=10599;\n' + insert('doors', next(d for d in capture['doors'] if d['id'] == 10599)))
        checks.append('key, pick skill, case-sensitive identity and position drift all reject atomically')
        run('CREATE TRIGGER hole_test BEFORE UPDATE ON doors FOR EACH ROW SET NEW.keyitem=NEW.keyitem;')
        run(forward, fail=True)
        assert snapshot() == baseline
        run('DROP TRIGGER hole_test;')
        checks.append('unexpected trigger rejects without mutation')
        run('ALTER TABLE doors ENGINE=MyISAM;')
        run(forward, fail=True)
        assert snapshot() == baseline
        checks.append('nontransactional engine rejects without mutation')
    finally:
        query('DROP DATABASE `' + database + '`;')
    return {'environment': 'isolated local MariaDB schema', 'door_rows': len(capture['doors']),
            'checks': checks, 'passed': True, 'production_writes': False}


if __name__ == '__main__':
    result = rehearse()
    (ROOT / 'docs/ops/hole-keyless-passage-20261024/rehearsal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
