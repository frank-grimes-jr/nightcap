"""Rehearse only against a NEW, isolated items clone. Never updates peq."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from tier_spell_scaling import capture_sql, migration_sql, plan, verification_sql


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'nightcap_spell_rehearsal_[0-9]{8}', args.database):
        raise ValueError('Only a dated isolated rehearsal database is allowed')
    args.output.mkdir(parents=True, exist_ok=False)

    def sql(statement, check=True, database=None):
        command = ['docker', 'exec', '-i', 'akk-stack-mariadb-1',
                   'sh', '-c',
                   'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names']
        result = subprocess.run(command, input=f'USE `{database or args.database}`;\n'+statement, capture_output=True, text=True,
                                encoding='utf-8', check=False)
        if check and result.returncode:
            raise RuntimeError(f'Exit {result.returncode}: {result.stderr[-4000:]} {result.stdout[-1000:]}')
        return result

    # Fail if the destination exists; never overwrite someone else's rehearsal.
    sql(f'CREATE DATABASE `{args.database}`; CREATE TABLE `{args.database}`.items LIKE peq.items;'
        f' INSERT INTO `{args.database}`.items SELECT * FROM peq.items;', database='peq')
    capture = sql(capture_sql()).stdout
    (args.output/'items.jsonl').write_text(capture, encoding='utf-8')
    rows = plan([json.loads(line) for line in capture.splitlines()])
    if not rows:
        raise ValueError('Clone has no legacy values to repair')
    forward, rollback = migration_sql(rows), migration_sql(rows, True)
    (args.output/'forward.sql').write_text(forward, encoding='utf-8')
    (args.output/'rollback.sql').write_text(rollback, encoding='utf-8')
    columns = sql('SHOW COLUMNS FROM items;').stdout.splitlines()
    names = [line.split('\t')[0] for line in columns]

    def fingerprint(excluded=()):
        selected = ','.join('`'+name+'`' for name in names if name not in excluded)
        data = sql('SELECT SHA2(JSON_ARRAY('+selected+'),256) FROM items ORDER BY id;').stdout
        if not data or any(not re.fullmatch('[0-9a-f]{64}', row) for row in data.splitlines()):
            raise ValueError('Incomplete or NULL item-row fingerprint')
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    checks = []
    before = fingerprint()
    preserved = fingerprint(('spelldmg', 'healamt'))
    # Verify rejection after locks but before writes, then recover only the
    # procedure created by the failed test in this isolated database.
    first = rows[0]
    sql(f'UPDATE items SET spelldmg=spelldmg+1 WHERE id={first["id"]};')
    drift_before = fingerprint()
    rejected = sql(forward, check=False)
    assert rejected.returncode and 'Item preimage drift' in rejected.stderr, rejected.stderr
    assert fingerprint() == drift_before, 'Failed transaction changed item data'
    sql('DROP PROCEDURE nightcap_apply_spell_plan;'
        f'UPDATE items SET spelldmg={first["old"][0]} WHERE id={first["id"]};')
    assert fingerprint() == before
    checks.append('preimage drift rejected without writes')

    sql(forward)
    verify = sql(verification_sql()).stdout
    assert len(verify.splitlines()) == 4 and all(line.endswith('\t0') for line in verify.splitlines()), verify
    assert fingerprint(('spelldmg', 'healamt')) == preserved
    checks.extend(['all four tier formulas verified', 'every other item column preserved'])
    after = fingerprint()
    replay = sql(forward, check=False)
    assert replay.returncode and 'Item preimage drift' in replay.stderr, replay.stderr
    assert fingerprint() == after
    sql('DROP PROCEDURE nightcap_apply_spell_plan;')
    checks.append('replay rejected without writes')
    sql(rollback)
    assert fingerprint() == before
    checks.append('exact full-table rollback')
    result = dict(database=args.database, changed_items=len(rows), checks=checks,
                  before_sha256=before, after_sha256=after,
                  untouched_columns_sha256=preserved,
                  input_sha256=hashlib.sha256(capture.encode('utf-8')).hexdigest())
    (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
