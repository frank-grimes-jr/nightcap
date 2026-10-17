"""Run emitted SQL only against session-local temporary items tables.

Run on the database host with planner.py alongside this file. The real items
table is read only, including capture of the production candidate preimages.
No durable table, item, player data, runtime or service is changed.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess


DB = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw',
      '--skip-column-names', '--quick', 'peq']
ROOT = '/opt/nightcap/deploy/production'


def query(sql):
    result = subprocess.run(DB, cwd=ROOT, input=sql, text=True,
                            capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Temporary-table rehearsal failed: ' + result.stderr[-1500:])
    return result.stdout


def run_rehearsal(planner):
    snapshot = query('SET SESSION TRANSACTION READ ONLY; '
                     'START TRANSACTION WITH CONSISTENT SNAPSHOT;\n' +
                     planner.CAPTURE_SQL + '\nROLLBACK;')
    production_rows = planner.read_snapshot(snapshot)
    fixture = [(1, 1, 1), (2, 1, 20), (3, 1, 75), (4, 1, 100),
               (5, 1, 200), (6, 0, 1), (7, 0, 0), (8, 1, 2147483647)]
    small = '1\t1\t1\n2\t1\t20\n3\t1\t75\n'
    results = []

    def case(name, rows, captured, should_fail=False, fault=False, repeat=False):
        # The temporary table shadows peq.items for this one connection only.
        # Its full schema is copied, so column types match production.
        setup = ('CREATE TEMPORARY TABLE nightcap_stack_schema LIKE peq.items;\n'
                 'CREATE TEMPORARY TABLE items LIKE nightcap_stack_schema;\n'
                 'DROP TEMPORARY TABLE nightcap_stack_schema;\n')
        for offset in range(0, len(rows), 500):
            values = ','.join(f"({i},{stackable},{size},'preserved',123,7)"
                              for i, stackable, size in rows[offset:offset + 500])
            setup += ('INSERT INTO items (id,stackable,stacksize,Name,price,maxcharges) VALUES ' +
                      values + ';\n')
        sql = planner.migration(captured)
        if fault:
            sql = sql.replace(' COMMIT;', " SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Injected failure';\n COMMIT;")
        preamble, block = sql.split('DELIMITER //\n', 1)
        body, ending = block.split('\nDELIMITER ;\n', 1)
        body = body.removesuffix(' //').replace('BEGIN NOT ATOMIC', 'BEGIN', 1) + ';'
        wrapped = (preamble + 'SET @caught=0;\nDELIMITER //\nBEGIN NOT ATOMIC\n'
                   ' DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @caught=1;\n' +
                   body + '\nEND //\nDELIMITER ;\n' + ending)
        sql = setup + wrapped
        if repeat:
            sql += wrapped
        sql += ("SELECT @caught;\nSELECT id,stackable,stacksize,Name,price,maxcharges "
                'FROM items ORDER BY id;\n')
        lines = query(sql).splitlines()
        if lines[0] != str(int(should_fail)):
            raise AssertionError(f'{name}: unexpected SQL acceptance/rejection')
        expected = []
        originals = dict(planner.read_snapshot(captured))
        for item_id, stackable, size in sorted(rows):
            after = (100 if (not should_fail or repeat) and item_id in originals else size)
            expected.append(f'{item_id}\t{stackable}\t{after}\tpreserved\t123\t7')
        if lines[1:] != expected:
            raise AssertionError(f'{name}: incorrect afterimage or preservation')
        results.append(dict(case=name, passed=True, rows=len(rows)))

    case('boundaries-and-unrelated-fields', fixture, small)
    case('missing-candidate', fixture[1:], small, True)
    case('changed-size-same-count', [(i, s, 30 if i == 2 else n) for i, s, n in fixture], small, True)
    case('replaced-id-same-count', [(9 if i == 2 else i, s, n) for i, s, n in fixture], small, True)
    case('new-candidate', fixture + [(9, 1, 20)], small, True)
    case('stackable-flag-drift', [(i, 0 if i == 2 else s, n) for i, s, n in fixture], small, True)
    case('failure-after-update-rolls-back', fixture, small, True, fault=True)
    case('repeat-rejected-without-loss', fixture, small, True, repeat=True)
    case('production-candidate-set', [(i, 1, n) for i, n in production_rows], snapshot)
    return dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                production_changed=False, candidate_count=len(production_rows),
                capture_sha256=hashlib.sha256(snapshot.encode()).hexdigest(),
                tests=results), snapshot


if __name__ == '__main__':
    import planner
    result, snapshot = run_rehearsal(planner)
    print(json.dumps(dict(evidence=result, snapshot=snapshot)))
