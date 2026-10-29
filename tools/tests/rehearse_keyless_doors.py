"""Exercise real SQL on an isolated local copy; never write local/live PEQ."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from keyless_doors import generate, plan
from pok_hub_migration import insert


def rehearse(capture_path=None):
    database = 'nightcap_keyless_test_' + uuid.uuid4().hex[:12]

    def query(sql, fail=False):
        result = subprocess.run([
            'docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-lc',
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw'],
            input=sql, text=True, capture_output=True, timeout=120)
        if fail:
            assert result.returncode != 0, 'Expected guarded rejection'
            assert 'Court ' in result.stderr, result.stderr
        elif result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout

    def run(sql, fail=False):
        return query('USE `' + database + '`;\n' + sql, fail)

    def snapshot():
        columns = [line.split('\t')[0] for line in run('SHOW COLUMNS FROM doors;').splitlines()]
        fields = ','.join('CAST(`' + c + '` AS CHAR)' for c in columns)
        rows = [dict(zip(columns, json.loads(line))) for line in run(
            'SELECT JSON_ARRAY(' + fields + ') FROM doors ORDER BY id;').splitlines()]
        for row in rows:
            for field in ('id', 'keyitem', 'lockpick'):
                row[field] = int(row[field])
        return {'doors': rows}

    checks = []
    query('CREATE DATABASE `' + database + '`;')
    try:
        if capture_path:
            captured = json.loads(capture_path.read_text(encoding='utf-8-sig'))
            inserts = [insert('doors', {**row, **captured['float_preimages'][str(row['id'])]})
                       for row in captured['doors']]
            run(captured['create_table'] + ';\n' + '\n'.join(inserts))
        else:
            run('CREATE TABLE doors LIKE peq.doors; INSERT INTO doors SELECT * FROM peq.doors;')
        baseline = snapshot()
        if capture_path:
            assert baseline['doors'] == captured['doors'], 'Production content reconstruction drift'
            checks.append('complete captured production door definitions reconstructed exactly')
        locked = [r for r in baseline['doors'] if r['keyitem'] or r['lockpick']]
        free = next(r for r in baseline['doors'] if not r['keyitem'] and not r['lockpick'])
        assert locked and free
        target = locked[0]['id']
        # Exact original numeric storage, retained for resetting fault injections.
        run('CREATE TABLE original LIKE doors; INSERT INTO original SELECT * FROM doors;')
        forward, inverse = generate(baseline)
        expected = plan(baseline)
        run(forward)
        assert snapshot() == expected
        checks.append('every existing lock removed; every other field and unlocked row preserved')
        run(forward, fail=True)
        assert snapshot() == expected
        checks.append('replay rejects atomically')
        run(inverse)
        assert snapshot() == baseline
        checks.append('inverse restores exact complete door table')

        def reset():
            run('TRUNCATE TABLE doors; INSERT INTO doors SELECT * FROM original;')

        for mutation in [
            f'UPDATE doors SET keyitem=keyitem+1 WHERE id={target}',
            f'UPDATE doors SET lockpick=lockpick+1 WHERE id={target}',
            f"UPDATE doors SET name=CONCAT('X',SUBSTRING(name,2)) WHERE id={target}",
            f'UPDATE doors SET pos_x=pos_x+1 WHERE id={target}',
            f'DELETE FROM doors WHERE id={target}',
            f'UPDATE doors SET keyitem=123 WHERE id={free["id"]}',
        ]:
            run(mutation + ';')
            drifted = snapshot()
            run(forward, fail=True)
            assert snapshot() == drifted
            reset()
        checks.append('key, pick, identity, position, deletion and new-lock drift reject atomically')

        # Unrelated edits to already-unlocked content must survive both directions.
        run(f'UPDATE doors SET pos_x=pos_x+1 WHERE id={free["id"]};')
        unrelated = snapshot()
        run(forward)
        assert snapshot() == plan(unrelated)
        run(inverse)
        assert snapshot() == unrelated
        reset()
        checks.append('unrelated unlocked content edits survive forward and inverse')

        run(forward)
        run(f'UPDATE doors SET guild=guild+1 WHERE id={target};')
        drifted = snapshot()
        run(inverse, fail=True)
        assert snapshot() == drifted
        reset()
        checks.append('inverse refuses changed afterimage without overwriting later edits')

        run('CREATE TRIGGER keyless_guard BEFORE UPDATE ON doors FOR EACH ROW SET NEW.keyitem=NEW.keyitem;')
        run(forward, fail=True)
        assert snapshot() == baseline
        run('DROP TRIGGER keyless_guard;')
        checks.append('unexpected triggers reject before writes')
        run('ALTER TABLE doors ENGINE=MyISAM;')
        run(forward, fail=True)
        assert snapshot() == baseline
        checks.append('nontransactional engine rejects before writes')
    finally:
        query('DROP DATABASE `' + database + '`;')
    return {'environment': 'isolated local MariaDB copy',
            'source': 'captured production doors' if capture_path else 'local PEQ doors',
            'door_rows': len(baseline['doors']),
            'locked_rows': len(locked), 'checks': checks, 'passed': True,
            'production_writes': False, 'local_peq_writes': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path)
    args = parser.parse_args()
    result = rehearse(args.capture)
    filename = 'production-rehearsal.json' if args.capture else 'rehearsal.json'
    out = ROOT / 'docs/ops/keyless-doors-20261029' / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
