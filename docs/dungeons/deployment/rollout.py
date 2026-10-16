"""Owner-authorized dungeon rollout. Never restore player SQL or replay access.

Preflight uses an isolated public-content database and scoped temporary account.
Once live SQL has been attempted, failures hold access for explicit reconciliation.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import mmap
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import struct
import subprocess
import sys
import time
import uuid

STAGE = Path('/opt/nightcap/releases/dungeons-20261016')
sys.path.insert(0, '/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
sys.path.insert(0, '/opt/nightcap/releases/equipment-race-policy-20261016')
spec = importlib.util.spec_from_file_location('previous_rollout', '/opt/nightcap/releases/equipment-race-policy-20261016/rollout.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
q.STAGE = STAGE
r.STAGE = STAGE
r.EVIDENCE = STAGE / 'evidence'
ROOT = r.ROOT
NAMES = {'world', 'zone', 'ucs', 'loginserver', 'shared_memory'}
REPLACE = {'world', 'zone', 'shared_memory'}
QUEST = 'quests/global/Instance_Keeper.pl'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save(name, value):
    with (r.EVIDENCE / name).open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(r.EVIDENCE, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load(name):
    return json.loads((r.EVIDENCE / name).read_text())


def sql(statement, database='peq'):
    assert database == 'peq' or re.fullmatch('nightcap_dungeon_stage_[0-9a-f]{12}', database)
    result = subprocess.run(['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw', '--quick',
        '--skip-column-names', database], cwd=ROOT,
        input='SET SESSION max_session_mem_used=134217728;\n' + statement, text=True,
        capture_output=True, timeout=600)
    if result.returncode:
        # SQL may contain a temporary password. Never echo it or command input.
        detail = 'Credential-bearing statement withheld' if 'IDENTIFIED BY' in statement else result.stderr[-1600:]
        raise RuntimeError('Dungeon database operation failed (' + str(result.returncode) + '): ' + detail)
    return result.stdout


def manifest():
    m = json.loads((STAGE / 'manifest.json').read_text())
    assert set(m['base_binaries']) == NAMES and set(m['binaries']) == REPLACE
    for name, digest in m['files'].items():
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
        target = STAGE / name
        assert target.resolve().is_relative_to(STAGE.resolve()) and not target.is_symlink()
        assert sha(target) == digest, name
    assert sha(Path(r.__file__)) == m['runtime_helper_sha256']
    assert sha(Path(q.__file__)) == m['previous_operator_sha256']
    assert sha(Path(q.c.__file__)) == m['previous_cache_helper_sha256']
    assert all(m['files']['bin/' + n] == h for n, h in m['binaries'].items())
    q.signed_client_receipt(m)
    return m


def policies():
    return sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')


def custom():
    tables = sql("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name LIKE 'nightcap\\_%' AND table_name NOT LIKE 'nightcap_dungeon_%' AND table_name NOT IN ('nightcap_market_offers','nightcap_market_state') ORDER BY table_name;").splitlines()
    return {table: sql('CHECKSUM TABLE `' + table + '` EXTENDED;').strip().split('\t')[-1] for table in tables}


def content(database='peq'):
    """Fingerprint every pre-existing row, excluding only explicitly owned keys."""
    rows = json.loads((STAGE / 'install-rows.json').read_text())
    tables = set(rows) | {'spawn2', 'doors', 'spells_new', 'merchantlist', 'zone', 'content_flags', 'faction_list'}
    result = {}
    for table in sorted(tables):
        if table.startswith('nightcap_dungeon_'):
            continue
        assert re.fullmatch('[a-z_][a-z0-9_]*', table)
        if table == 'items':
            # Native items has a UNIQUE ID index, not a primary key. Require the
            # whole, non-null single-column key before excluding owned rows.
            index = sql("SELECT s.column_name,s.non_unique,IFNULL(s.sub_part,0),c.is_nullable FROM information_schema.statistics s JOIN information_schema.columns c ON c.table_schema=s.table_schema AND c.table_name=s.table_name AND c.column_name=s.column_name WHERE s.table_schema=DATABASE() AND s.table_name='items' AND s.index_name='ID' ORDER BY s.seq_in_index;", database).strip()
            assert index == 'id\t0\t0\tNO', 'Native items unique ID contract changed'
            keys = ['id']
        else:
            keys = [line.split('\t')[0] for line in sql("SELECT column_name FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='" + table + "' AND index_name='PRIMARY' ORDER BY seq_in_index;", database).splitlines()]
        owned = rows.get(table, [])
        where = ''
        if owned:
            assert keys and all(set(keys) <= set(row) for row in owned), table
            assert all(isinstance(row[key], int) for row in owned for key in keys), table
            tuples = ','.join('(' + ','.join(str(row[key]) for key in keys) + ')' for row in owned)
            columns = '(' + ','.join('`' + key + '`' for key in keys) + ')'
            where = ' WHERE ' + columns + ' NOT IN (' + tuples + ')'
        columns = [line.split('\t') for line in sql("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='" + table + "' ORDER BY ordinal_position;", database).splitlines()]
        assert columns and all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', c[0]) for c in columns), table
        expressions = [('CAST(`' + name + '` AS DOUBLE)' if kind in ('float','double') else '`' + name + '`') for name, kind in columns]
        # Hash rows on the database and stream compact digests. Buffering all
        # native item columns can exhaust the container's client memory.
        data = sorted(sql('SELECT SHA2(JSON_ARRAY(' + ','.join(expressions) + '),256) FROM `' + table + '`' + where + ';', database).splitlines())
        assert all(re.fullmatch('[0-9a-f]{64}', digest) for digest in data), table
        result[table] = {'rows': len(data), 'sha256': hashlib.sha256('\n'.join(data).encode()).hexdigest()}
    return result


def records(path):
    result = {}
    with path.open('rb') as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        payload, count, maximum, current = struct.unpack_from('<IIII', data, 0)
        assert maximum == current and len(data) == payload + 8 == 20 + 4 * count + 1332 * maximum
        start = 16 + 4 * count
        for item in range(count):
            index = struct.unpack_from('<I', data, 16 + item * 4)[0]
            if index < current:
                value = data[start + index * 1332:start + (index + 1) * 1332]
                assert struct.unpack_from('<I', value, 440)[0] == item
                result[item] = hashlib.sha256(value).hexdigest()
    assert len(result) == current
    return result


def compare_cache(before, after):
    assert set(after) - set(before) == set(range(960000, 960330)), 'Wrong added item set'
    assert set(before) <= set(after)
    assert all(after[item] == digest for item, digest in before.items()), 'Existing item cache changed'
    return {'existing_items_preserved': len(before), 'custom_items_checked': 330,
            'all_records_sha256': hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()}


def binaries(p):
    return {**{n: p['old_hashes']['bin/' + n] for n in NAMES}, **manifest()['binaries']}


def expected_image(p):
    return {**p['old_hashes'], **{'bin/' + n: h for n, h in manifest()['binaries'].items()}}


def unchanged(p, installed=False):
    for service in ('db', 'web', 'tunnel'):
        assert r.compact(service) == p['services'][service], service
    runtime = dict(p['runtime'])
    if installed:
        runtime[QUEST] = manifest()['files'][QUEST]
    assert r.runtime() == runtime, 'Quest/plugin drift'
    assert r.public() == p['public'], 'Public client/website drift'
    assert policies() == p['policies'], 'Rule drift'
    assert content() == p['content'], 'Pre-existing public content drift'


def cache_contract(image, path):
    result = r.out('docker', 'run', '--rm', '--network', 'none', '--user', '0',
        '-v', str(STAGE) + ':/stage:ro', '-v', str(path.resolve()) + ':/items:ro',
        '--entrypoint', '/stage/cache_check', image, '/items').strip()
    assert result == '1332 330', result


def challenge_health():
    """Challenge the native world port now; Docker health can be stale."""
    r.call('docker', 'exec', r.state('game')['Id'], 'python3', '/opt/nightcap/start.py', '--health')


def audit_references():
    mapping = json.loads((STAGE / 'item-references.json').read_text())
    counts = {}
    for table, columns in mapping.items():
        for column in columns:
            exists = sql("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='" + table + "' AND column_name='" + column + "';").strip() == '1'
            if exists:
                value = int(sql(f'SELECT COUNT(*) FROM `{table}` WHERE `{column}` BETWEEN 960000 AND 960329;'))
                assert value == 0, 'Reserved item reference: ' + table + '.' + column
                counts[table + '.' + column] = value
    return counts


def runtime_config():
    mounts = [v for v in r.state('game')['Mounts'] if v['Destination'] == '/srv/nightcap/eqemu_config.json']
    assert len(mounts) == 1 and not mounts[0]['RW'], 'Unexpected configuration mount'
    path = Path(mounts[0]['Source'])
    assert path.resolve() == (ROOT / 'private/eqemu_config.json').resolve()
    return json.loads(path.read_text())


def rehearsal(p):
    database = 'nightcap_dungeon_stage_' + uuid.uuid4().hex[:12]
    username = 'nd_' + uuid.uuid4().hex[:12]
    password = secrets.token_hex(24)
    runtime = STAGE / 'rehearsal-runtime'
    runtime.mkdir(mode=0o700)
    (runtime / 'shared').mkdir()
    (runtime / 'logs').mkdir()
    created_user = False
    cfg_path = runtime / 'eqemu_config.json'
    try:
        sql('CREATE DATABASE `' + database + '`;')
        target = json.loads((STAGE / 'target-content.json').read_text())
        public = set(target['ddl']) | {'spawn2', 'doors', 'faction_list', 'spells_new', 'merchantlist', 'zone', 'content_flags', 'rule_sets', 'rule_values', 'variables', 'logsys_categories'}
        empty = {'instance_list', 'instance_list_player', 'character_advloot_claims', 'inventory', 'character_data', 'character_corpses', 'character_evolving_items'}
        public -= empty
        for table in sorted(public | empty):
            assert re.fullmatch('[a-z_][a-z0-9_]*', table)
            sql(f'CREATE TABLE `{table}` LIKE peq.`{table}`;', database)
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n' + '\n'.join(f'INSERT INTO `{t}` SELECT * FROM peq.`{t}`;' for t in sorted(public)) + '\nCOMMIT;', database)
        assert content(database) == p['content'], 'Clone differs from captured public content'
        sql(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}';")
        created_user = True
        sql(f"GRANT ALL ON `{database}`.* TO '{username}'@'%';")
        config = runtime_config()
        connection = config['server']['database']
        connection.update(db=database, username=username, password=password)
        config['server']['content_database'] = dict(connection)
        config['server'].setdefault('directories', {}).update(shared_memory='/runtime/shared/', logs='/runtime/logs/')
        cfg_path.write_text(json.dumps(config))
        cfg_path.chmod(0o600)
        networks = list(r.state('db')['NetworkSettings']['Networks'])
        assert len(networks) == 1
        def loader(image, name):
            command = ['docker', 'run', '--rm', '--network', networks[0], '--user', '0', '-v', str(runtime) + ':/runtime',
                '--workdir', '/runtime', '--entrypoint', '/opt/nightcap/bin/shared_memory', image, 'items']
            with (runtime / (name + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=240)
            assert result.returncode == 0, 'Isolated loader failed; private log retained'
            log = (runtime / (name + '.log')).read_text()
            assert not any(s in log for s in ('Unknown column', 'SQL syntax', 'Unable to connect', "doesn't exist"))
        loader(p['old_image_id'], 'before')
        before_path = runtime / 'before-items'
        (runtime / 'shared/items').rename(before_path)
        before = records(before_path)
        assert before == records(ROOT / 'data/server/shared/items'), 'Production cache differs from fresh loader baseline'
        for filename in ('20261016_dungeons.sql', '20261016_dungeon_content.sql', '20261016_dungeon_enable.sql'):
            sql((STAGE / 'sql' / filename).read_text(), database)
        assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;', database).strip() == '2026101601\t1'
        sql('UPDATE nightcap_dungeon_state SET enabled=0 WHERE id=1;', database)
        assert content(database) == p['content'], 'Migration changed existing public rows'
        loader(p['new_image_id'], 'after')
        cache_contract(p['new_image_id'], runtime / 'shared/items')
        result = compare_cache(before, records(runtime / 'shared/items'))
        result.update(status='passed', database=database, public_content_preserved=True,
            item_cache_sha256=sha(runtime / 'shared/items'), native_contract_activation=True)
        save('rehearsal.json', result)
        print(json.dumps({'status': 'production_content_rehearsal_passed', **result}), flush=True)
    finally:
        cfg_path.unlink(missing_ok=True)
        if created_user:
            sql(f"DROP USER '{username}'@'%';")


def preflight():
    m = manifest()
    assert not r.EVIDENCE.exists(), 'Existing evidence; do not replay preflight'
    services = {s: r.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')}
    old = services['game']
    assert services['gateway']['running'] and old['restarts'] == m['baseline_restarts']
    hashes = r.image_hashes(old['image_id'])
    assert {n: hashes['bin/' + n] for n in NAMES} == m['base_binaries']
    r.running(old['image_id'], m['base_binaries'], expected_restarts=m['baseline_restarts'])
    assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name LIKE 'nightcap_dungeon_%';").strip() == '0'
    q.verify_publication(m)
    r.closed_ports()
    references = audit_references()
    snapshot = {'manifest_sha256': sha(STAGE / 'manifest.json'), 'old_image_id': old['image_id'], 'old_hashes': hashes,
        'services': services, 'runtime': r.runtime(), 'public': r.public(), 'content': content(), 'policies': policies()}
    tag = 'nightcap-game:dungeons-base-20261016'
    r.call('docker', 'tag', old['image_id'], tag)
    (STAGE / 'Dockerfile').write_text('FROM ' + tag + '\nCOPY bin/world bin/zone bin/shared_memory /opt/nightcap/bin/\n')
    r.call('docker', 'build', '--network', 'none', '-t', 'nightcap-game:dungeons-20261016', str(STAGE))
    image = r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', 'nightcap-game:dungeons-20261016').strip()
    snapshot['new_image_id'] = image
    assert r.image_hashes(image) == expected_image(snapshot), 'Unexpected image files'
    layers = lambda value: json.loads(r.out('docker', 'image', 'inspect', value))[0]['RootFS']['Layers']
    before, after = layers(old['image_id']), layers(image)
    assert after[:len(before)] == before and len(after) == len(before) + 1
    for name in REPLACE:
        assert 'not found' not in r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', image, '/opt/nightcap/bin/' + name)
    r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', image, '-c', "import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/opt/nightcap/bin/loginserver', image, '--nightcap-crypto-self-test')
    r.EVIDENCE.mkdir(mode=0o700)
    save('references.json', references)
    rehearsal(snapshot)
    unchanged(snapshot)
    assert r.compact('game') == services['game'] and r.compact('gateway') == services['gateway']
    save('preflight.json', snapshot)
    print('Preflight passed; production remains open and unchanged.', flush=True)


def preserved(data):
    assert r.player_data() == data['player'], 'Player/receipt data drift while access closed'
    assert custom() == data['custom'], 'Existing custom data drift'


def hold(reason, access_uncertain=False):
    r.compose('stop', 'gateway')
    assert not r.state('gateway')['State']['Running']
    name = 'held-' + str(time.time_ns()) + '.json'
    save(name, {'reason': reason, 'gateway_open': False, 'database_restored': False, 'access_may_have_opened': access_uncertain})


def activate():
    m, p = manifest(), load('preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    assert not (r.EVIDENCE / 'activation-started.json').exists(), 'Activation already attempted; reconcile explicitly'
    assert r.compact('game') == p['services']['game'] and r.compact('gateway') == p['services']['gateway']
    unchanged(p)
    assert r.image_hashes(p['new_image_id']) == expected_image(p)
    save('activation-started.json', {'authorized': True, 'database_restored': False})
    try:
        r.compose('stop', 'gateway')
        shutdown_started = time.monotonic()
        r.compose('stop', '-t', '90', 'game')
        q.stopped()
        save('shutdown.json', {'duration_seconds': time.monotonic() - shutdown_started,
            'native_flush_confirmed': False,
            'note': 'Container exit zero does not prove native flush; supervisor may kill children after 75 seconds.',
            'previous_game': p['services']['game']})
        data = {'player': r.player_data(), 'custom': custom()}
        save('stopped-data.json', data)
        backup = r.database_backup()
        save('backup.json', backup)
        old_quest = ROOT / 'data/server' / QUEST
        shutil.copy2(old_quest, STAGE / 'private-backup/Instance_Keeper.pl')
        assert sha(old_quest) == p['runtime'][QUEST]
        save('sql-attempted.json', {'schema': m['files']['sql/20261016_dungeons.sql'], 'content': m['files']['sql/20261016_dungeon_content.sql']})
        sql((STAGE / 'sql/20261016_dungeons.sql').read_text())
        sql((STAGE / 'sql/20261016_dungeon_content.sql').read_text())
        assert sql('SELECT enabled FROM nightcap_dungeon_state;').strip() == '0'
        preserved(data)
        assert content() == p['content']
        mode = old_quest.stat()
        pending = old_quest.with_name('Instance_Keeper.pl.dungeons-pending')
        with pending.open('xb') as handle:
            handle.write((STAGE / QUEST).read_bytes()); handle.flush(); os.fsync(handle.fileno())
        os.chmod(pending, mode.st_mode & 0o777); os.chown(pending, mode.st_uid, mode.st_gid)
        os.replace(pending, old_quest)
        q.select(p['new_image_id'])
        r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        challenge_health()
        first = r.running(p['new_image_id'], binaries(p), expected_restarts=0)
        cache_path = ROOT / 'data/server/shared/items'
        cache_contract(p['new_image_id'], cache_path)
        cache = compare_cache(records(STAGE / 'rehearsal-runtime/before-items'), records(cache_path))
        assert cache['all_records_sha256'] == load('rehearsal.json')['all_records_sha256']
        time.sleep(16)
        challenge_health()
        result = r.running(p['new_image_id'], binaries(p), expected_restarts=0)
        assert result['started_at'] == first['started_at']
        sql((STAGE / 'sql/20261016_dungeon_enable.sql').read_text())
        assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip() == '2026101601\t1'
        preserved(data); unchanged(p, True); q.verify_publication(m)
        assert not r.state('gateway')['State']['Running']
        save('activated-closed.json', {'runtime': result, 'game': r.compact('game'), 'cache': cache,
            'cache_sha256': sha(cache_path), 'gateway_open': False, 'backup': backup,
            'player_tables_preserved': len(data['player']), 'custom_tables_preserved': len(data['custom'])})
        print('Candidate active and enabled; access remains closed for final verification.', flush=True)
    except BaseException:
        hold('Activation failed; preserve SQL, receipts and current image for explicit reconciliation')
        raise


def open_access():
    m, p, a = manifest(), load('preflight.json'), load('activated-closed.json')
    if (r.EVIDENCE / 'opening.json').exists():
        hold('Prior open attempt has an uncertain outcome; do not replay', True)
        raise RuntimeError('Opening already attempted; access held for reconciliation')
    if list(r.EVIDENCE.glob('held-*.json')):
        hold('Existing recovery hold; do not replay', True)
        raise RuntimeError('Recovery already required')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    access_uncertain = False
    try:
        if r.state('gateway')['State']['Running']:
            access_uncertain = True
            raise RuntimeError('Access already open; do not replay')
        assert r.compact('game') == a['game']
        preserved(load('stopped-data.json')); unchanged(p, True)
        assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip() == '2026101601\t1'
        assert sha(ROOT / 'data/server/shared/items') == a['cache_sha256']
        result = r.running(p['new_image_id'], binaries(p), expected_restarts=0)
        challenge_health()
        publication = q.verify_publication(m)
        save('opening.json', {'runtime': result, 'publication': publication})
        access_uncertain = True
        r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert r.state('gateway')['State']['Running']
        result = r.running(p['new_image_id'], binaries(p), expected_restarts=0)
        challenge_health()
        assert result['started_at'] == a['runtime']['started_at']
        unchanged(p, True); r.closed_ports()
        # Never compare/restore player snapshots after the gateway open attempt.
        save('activated.json', {**a, 'runtime': result, 'gateway_open': True, 'publication': publication,
            'enabled_revision': 2026101601, 'database_restored': False, 'owner_gameplay_accepted': False})
        print(json.dumps({'status': 'deployed', 'gateway_open': True, 'enabled_revision': 2026101601}), flush=True)
    except BaseException:
        hold('Open acknowledgment or verification uncertain; preserve subsequent activity', access_uncertain)
        raise


def report():
    m, p, a = manifest(), load('preflight.json'), load('activated.json')
    result = r.running(p['new_image_id'], binaries(p), expected_restarts=0)
    challenge_health()
    assert result['started_at'] == a['runtime']['started_at'] and r.compact('gateway')['running']
    unchanged(p, True); r.closed_ports(); q.verify_publication(m)
    assert sha(ROOT / 'data/server/shared/items') == a['cache_sha256']
    assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip() == '2026101601\t1'
    print(json.dumps({'status': 'healthy', 'runtime': result, 'gateway_open': True, 'cache': a['cache'], 'enabled_revision': 2026101601}), flush=True)


if __name__ == '__main__':
    assert __debug__, 'Assertions required'
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['preflight', 'activate', 'open', 'report'])
    action = parser.parse_args().action
    with (ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm_lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        q.require_no_gm_work()
        {'preflight': preflight, 'activate': activate, 'open': open_access, 'report': report}[action]()
