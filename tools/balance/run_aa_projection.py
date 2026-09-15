"""Host-side, isolated-only native proof of AA rank-chain projection and restore.

Uses the existing container administrator credential without returning it. Never
connects to PEQ, changes character ownership, or restarts a server process.
"""
import copy
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from aa_policy_preflight import read_json, SNAPSHOT_SQL
from aa_policy_projection import DATABASE, project, transaction_sql


RUNTIME = '/tmp/nightcap-balance-20260912'
SERVER = 'akk-stack-eqemu-server-1'
DB_CONTAINER = 'akk-stack-mariadb-1'
DOCS = Path(__file__).resolve().parents[2] / 'docs/balance'


def command(args, **kwargs):
    result = subprocess.run(args, capture_output=True, timeout=180, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout


def sql(statement):
    return command(['docker', 'exec', '-i', DB_CONTAINER, 'sh', '-c',
                    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot ' + DATABASE
                    + ' --batch --raw --skip-column-names'],
                   input=statement, text=True, encoding='utf-8')


def snapshot():
    data = {k: [] for k in ('abilities', 'ranks', 'prerequisites', 'purchases')}
    for line in sql(SNAPSHOT_SQL).splitlines():
        key, value = line.split('\t', 1)
        data[key].append(json.loads(value))
    return data


def dump_tables():
    return command(['docker', 'exec', DB_CONTAINER, 'sh', '-c',
                    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot '
                    '--single-transaction --skip-lock-tables --skip-comments '
                    '--skip-add-locks --order-by-primary --no-create-info '
                    + DATABASE + ' aa_ability aa_ranks'])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    raw = (json.dumps(value, separators=(',', ':')) + '\n').encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def native(value, rejected_rank=None):
    source, target = RUNTIME + '/aa-projection-case-input.json', RUNTIME + '/aa-projection-case-result.json'
    script = ('import sys; from pathlib import Path; '
              f'Path({source!r}).write_bytes(sys.stdin.buffer.read()); '
              f'Path({target!r}).unlink(missing_ok=True)')
    command(['docker', 'exec', '-i', SERVER, 'python3', '-c', script],
            input=json.dumps(value).encode())
    run = subprocess.run(['docker', 'exec', '-w', RUNTIME, '-e', 'NIGHTCAP_BALANCE_RNG_SEED=1729',
                          SERVER, './balance-zone', 'tests:balance', source, target],
                         capture_output=True, text=True, encoding='utf-8')
    if rejected_rank is not None:
        exists = subprocess.run(['docker', 'exec', SERVER, 'test', '-e', target], capture_output=True)
        expected = f'Native AA purchase gate rejected rank {rejected_rank}'
        if run.returncode != 1 or expected not in run.stderr or exists.returncode != 1:
            raise RuntimeError('Expected native purchase rejection: ' + run.stderr[-2000:])
        return {'exit_code': run.returncode, 'rejected_rank_id': rejected_rank,
                'native_error': run.stderr.strip(), 'output_absent': True}
    if run.returncode:
        raise RuntimeError('Native projection control failed: ' + run.stderr[-2000:])
    raw = command(['docker', 'exec', SERVER, 'cat', target])
    return {'native_raw_sha256': digest(raw), 'report': json.loads(raw)}


def inputs(matrix, specification, original_catalog):
    result = []
    catalogs = {b['profile']: b['aa_catalog'] for b in original_catalog['builds']}
    for policy in specification['policies']:
        allocations = [a for a in matrix['allocations'] if any(x['policy'] == policy['id'] for x in a['aliases'])]
        templates = {a['key']: next(c for c in matrix['cases'] if c['allocation_key'] == a['key']) for a in allocations}
        batch = {'builds': [copy.deepcopy(templates[a['key']]['input']['builds'][0]) for a in allocations],
                 'export_aa_catalog': True}
        maxima = [a for a in allocations if any(x['policy'] == policy['id'] and x['requested'] == 'all' for x in a['aliases'])]
        controls, fights = [], []
        for allocation in maxima:
            build = templates[allocation['key']]['input']['builds'][0]
            candidates = [(33, policy['caps']['33'] + 1, 'above_cap'), (1, 1, 'omitted_family')]
            if allocation['profile'] == 'war-clr-wiz':
                candidates.append((515, 1, 'omitted_twincast'))
            for aid, ordinal, kind in candidates:
                rank = next(r for r in catalogs[allocation['profile']] if r['ability_id'] == aid and r['rank'] == ordinal)
                changed = copy.deepcopy(build)
                changed['aa_rank_ids'].append(rank['rank_id'])
                changed['aa_budget'] += rank['cost']
                changed['aa_stage'] = str(changed['aa_budget'])
                changed['aa_policy'] = 'projection_gate_control'
                controls.append({'id': policy['id'] + '-' + allocation['profile'] + '-' + kind,
                                 'rank_id': rank['rank_id'], 'input': {'builds': [changed]}})
            fights.extend(c for c in matrix['cases'] if c['allocation_key'] == allocation['key'] and c['seed'] == 1729)
        result.append({'id': policy['id'], 'batch': batch, 'controls': controls, 'fights': fights})
    return result


def verify_batch(before, after, allowed):
    if len(before['builds']) != len(after['builds']):
        raise ValueError('Missing projected stat build')
    observed = set()
    for old, new in zip(before['builds'], after['builds']):
        expected = []
        for rank in old['aa_catalog']:
            if rank['rank_id'] in allowed:
                row = copy.deepcopy(rank)
                if row['next_rank_id'] not in allowed:
                    row['next_rank_id'] = -1
                expected.append(row)
        if new['aa_catalog'] != expected:
            raise ValueError('Native catalog does not equal the capped rank-chain projection')
        if {k: v for k, v in old.items() if k != 'aa_catalog'} != {k: v for k, v in new.items() if k != 'aa_catalog'}:
            raise ValueError('Allowed purchase stats changed under projection')
        observed.update(r['rank_id'] for r in new['aa_catalog'])
    if observed != allowed:
        raise ValueError('Compiled pool includes an unobserved native rank')


def main():
    report_path = DOCS / 'aa-projection-native.json.gz'
    if report_path.exists():
        raise ValueError('Refusing to overwrite existing native evidence')
    running = subprocess.run(['docker', 'exec', SERVER, 'pgrep', '-f',
                              '[b]alance-zone|[r]elease_pool_controls.py'], capture_output=True)
    if running.returncode != 1:
        raise ValueError('Isolated runtime is not verified idle')
    if sql('SELECT (SELECT COUNT(*) FROM account)+(SELECT COUNT(*) FROM character_data)+(SELECT COUNT(*) FROM character_alternate_abilities);').strip() != '0':
        raise ValueError('Isolated fixture contains account/character ownership')
    frozen = read_json(DOCS / 'aa-policy-snapshot.json.gz')
    before = snapshot()
    for key in ('abilities', 'ranks', 'prerequisites'):
        if before[key] != frozen[key]:
            raise ValueError('Clone AA tables differ from the preflight source: ' + key)
    specification = read_json(DOCS / 'aa-release-candidates.json')
    matrix = read_json(DOCS / 'gear-source-inputs.json')
    phases = inputs(matrix, specification, read_json(DOCS / 'native-aa-catalog.json'))
    binary = command(['docker', 'exec', SERVER, 'sha256sum', RUNTIME + '/balance-zone'], text=True).split()[0]
    if binary != read_json(DOCS / 'pet-resist-build.json')['binary_sha256']:
        raise ValueError('Native binary changed')
    original_dump = dump_tables()
    (DOCS / 'aa-projection-before.sql.gz').write_bytes(gzip.compress(original_dump, mtime=0))
    write(DOCS / 'aa-projection-inputs.json', phases)
    evidence = {'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'binary_sha256': binary, 'database': DATABASE, 'before_tables_sha256': digest(original_dump), 'phases': []}
    golden = {r['id']: r for r in read_json(DOCS / 'gear-source.json.gz')['runs']}
    for phase in phases:
        plan = project(before, specification, phase['id'])
        suffix = uuid4().hex[:12]
        forward = transaction_sql(plan, DATABASE, 'aa_project_' + suffix)
        restore = transaction_sql(plan, DATABASE, 'aa_restore_' + suffix, True)
        (DOCS / ('aa-projection-' + phase['id'] + '-apply.sql')).write_bytes(forward.encode())
        (DOCS / ('aa-projection-' + phase['id'] + '-restore.sql')).write_bytes(restore.encode())
        result = {'id': phase['id'], 'plan': plan,
                  'original_batch': native(phase['batch']), 'controls': [], 'fights': []}
        for control in phase['controls']:
            result['controls'].append({'id': control['id'], 'original': native(control['input'])})
        expected = copy.deepcopy(before)
        for table, rows, field in (('aa_ability', expected['abilities'], 'enabled'), ('aa_ranks', expected['ranks'], 'next_id')):
            changes = {rid: value for rid, old, value in plan['changes'][table]}
            for row in rows:
                row[field] = changes.get(row['id'], row[field])
        evidence['phases'].append(result)
        try:
            sql(forward)
            if snapshot() != expected:
                raise ValueError('Unexpected table state after projection')
            result['projected_batch'] = native(phase['batch'])
            verify_batch(result['original_batch']['report'], result['projected_batch']['report'], set(plan['allowed_rank_ids']))
            for control, recorded in zip(phase['controls'], result['controls']):
                recorded['projected'] = native(control['input'], control['rank_id'])
            for case in phase['fights']:
                observed = native(case['input'])
                if observed['native_raw_sha256'] != golden[case['id']]['native_raw_sha256'] or observed['report'] != golden[case['id']]['report']:
                    raise ValueError('Projected boss fight changed: ' + case['id'])
                result['fights'].append({'id': case['id'], **observed})
                print(phase['id'], case['id'], 'identical', flush=True)
        finally:
            current = snapshot()
            if current == expected:
                sql(restore)
            elif current != before:
                raise RuntimeError('Unexpected AA state; guarded recovery SQL retained; refusing a blind overwrite')
            sql(f'DROP PROCEDURE IF EXISTS `aa_project_{suffix}`; DROP PROCEDURE IF EXISTS `aa_restore_{suffix}`;')
            restored = dump_tables()
            result['restored_tables_sha256'] = digest(restored)
            result['restored_exactly'] = restored == original_dump and snapshot() == before
            write(report_path, evidence)
            if not result['restored_exactly']:
                raise RuntimeError('AA restoration differs from the original backup')
        print(phase['id'], 'restored exactly', flush=True)
    evidence['completed'] = True
    write(report_path, evidence)
    print('Both AA projections verified and restored', flush=True)


if __name__ == '__main__':
    main()
