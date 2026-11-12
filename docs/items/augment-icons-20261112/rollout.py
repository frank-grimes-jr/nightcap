"""One-shot native deployment + exact five-icon repair; never restore inventories."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/augment-icons-20261112-v1')
EVIDENCE = STAGE / 'evidence'
TAG = 'nightcap-game:augment-icons-20261112-v1'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def initialize():
    global m, prior, r, h, base, startup, market, sql, repair
    m = read(STAGE / 'manifest.json')
    assert m['owner_authorization'] == 'Deploy the fix and repair the affected item icons, preserving the augments and all other item data.'
    for name, pin in m['files'].items():
        path = STAGE / name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and sha(path) == pin, name
    path = Path('/opt/nightcap/releases/last-lantern-20261107-v4/rollout.py')
    assert sha(path) == m['prior_operator_sha256']
    spec = importlib.util.spec_from_file_location('prior_lantern', path)
    prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior); prior.initialize()
    r, h, base, startup, market, sql = prior.r, prior.h, prior.base, prior.startup, prior.market, prior.sql
    repair = {}
    exec((STAGE / 'repair.py').read_text(), repair)
    assert sha(Path(m['capture'])) == m['capture_sha256']
    assert r.image_hashes(m['base_image_id']) == m['base_hashes']
    proof = read(STAGE / 'native-build.json')
    assert proof['status'] == 'PASS' and len(proof['dependency_closures']) == 3
    assert read(STAGE / 'repair-rehearsal.json')['status'] == 'PASS'
    for name in ('world', 'zone', 'shared_memory'):
        assert proof['shipping']['baseline-' + name] == m['base_hashes']['bin/' + name]
        assert proof['shipping']['candidate-' + name] == m['binaries'][name] == m['files']['bin/' + name]


def binaries(candidate=True):
    result = {key[4:]: value for key, value in m['base_hashes'].items() if key.startswith('bin/')}
    return {**result, **m['binaries']} if candidate else result


def content():
    result = prior.content()
    # The prior release owns excluded campaign scopes; preserve those too.
    for table in prior.SCOPES:
        result[table + '/complete-icon-release'] = prior.digest(table)
    for table in prior.NEW_TABLES:
        result[table + '/complete-icon-release'] = prior.digest(table)
    return result


def unchanged(before, after_open=False):
    for name in ('db', 'web', 'tunnel'):
        assert r.compact(name) == before['services'][name], name
    assert r.runtime() == before['runtime'], 'Quest/plugin drift'
    assert h.publication() == before['publication'], 'Public channel/wiki drift'
    assert h.caches() == before['caches'], 'Shared cache drift'
    actual, expected = content(), before['content']
    if after_open:
        # Once access is open, legitimate campaign progress may resume.
        mutable = {table + '/complete-icon-release' for table in prior.NEW_TABLES}
        actual = {key: value for key, value in actual.items() if key not in mutable}
        expected = {key: value for key, value in expected.items() if key not in mutable}
    assert actual == expected, 'Content/campaign data drift'
    assert prior.p.rules() == before['rules'], 'Rules drift'


def contract():
    return {'dungeon': prior.prior.contract(), 'lantern': prior.check_content(enabled=1)}


def image():
    r.call('docker', 'tag', m['base_image_id'], TAG + '-base')
    (STAGE / 'Dockerfile').write_text('FROM ' + TAG + '-base\nCOPY bin/ /opt/nightcap/bin/\n')
    (STAGE / '.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/world\n!bin/zone\n!bin/shared_memory\n')
    r.call('docker', 'build', '--pull=false', '--network', 'none', '-t', TAG, str(STAGE))
    value = r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', TAG).strip()
    assert r.image_hashes(value) == {**m['base_hashes'], **{'bin/' + k: v for k, v in m['binaries'].items()}}
    layers = lambda name: json.loads(r.out('docker', 'image', 'inspect', name))[0]['RootFS']['Layers']
    assert layers(value)[:-1] == layers(m['base_image_id'])
    for name in m['binaries']:
        assert 'not found' not in r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', value, '/opt/nightcap/bin/' + name)
    r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', value, '-c',
           'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return value


def preflight():
    assert not EVIDENCE.exists(), 'Existing attempt; inspect receipts instead of replaying'
    assert prior.players() == 0
    services = {name: r.compact(name) for name in ('game', 'gateway', 'db', 'web', 'tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values())
    assert services['game']['health'] == services['db']['health'] == 'healthy'
    assert services['game']['image_id'] == m['base_image_id']
    r.running(m['base_image_id'], binaries(False), services['game']['restarts'])
    base.health(); startup.startup_guards(); r.closed_ports(); checks = contract()
    assert shutil.disk_usage(ROOT).free > 4 * 1024**3
    repair['prepare'](sql, read(Path(m['capture'])))
    EVIDENCE.mkdir(mode=0o700)
    before = {'manifest_sha256': sha(STAGE / 'manifest.json'), 'services': services, 'checks': checks,
              'runtime': r.runtime(), 'publication': h.publication(), 'caches': h.caches(),
              'content': content(), 'rules': prior.p.rules()}
    save(EVIDENCE / 'preflight-started.json', before)
    dry = EVIDENCE / 'boot-preflight'; dry.mkdir(mode=0o700)
    previous = base.EVIDENCE; base.EVIDENCE = dry
    try:
        base.boot_state(prior.saved())
    finally:
        base.EVIDENCE = previous
    before['image'] = image()
    unchanged(before)
    assert all(r.compact(name) == state for name, state in services.items())
    save(EVIDENCE / 'preflight.json', before)
    print('Preflight passed; current game and access unchanged.', flush=True)


def activate():
    before = read(EVIDENCE / 'preflight.json'); folder = EVIDENCE / 'activation'
    assert before['manifest_sha256'] == sha(STAGE / 'manifest.json') and not folder.exists()
    assert prior.players() == 0
    unchanged(before); startup.startup_guards()
    assert all(r.compact(name) == state for name, state in before['services'].items())
    folder.mkdir(mode=0o700); save(folder / 'started.json', {'image': before['image']})
    try:
        r.compose('stop', 'gateway')
        for elapsed in range(0, 125, 25):
            print('Draining admissions: ' + str(elapsed) + '/125 seconds.', flush=True); time.sleep(25)
        assert prior.players() == 0
        started = time.monotonic(); r.compose('stop', '-t', '90', 'game')
        assert time.monotonic() - started < 70
        state = r.state('game')['State']
        assert not state['Running'] and not state['OOMKilled'] and state['ExitCode'] == 0
        assert not r.state('gateway')['State']['Running']
        unchanged(before); startup.startup_guards()
        data = prior.saved(); market_before = market.market()
        save(folder / 'stopped-state.json', data); save(folder / 'market-before.json', market_before)
        prepared = repair['prepare'](sql, read(Path(m['capture'])))
        save(folder / 'repair-before.json', prepared)
        r.STAGE = folder; base.EVIDENCE = folder
        save(folder / 'backup.json', r.database_backup()); assert prior.saved() == data
        statement = repair['statement'](prepared)
        with (folder / 'repair.sql').open('x') as handle:
            handle.write(statement); handle.flush(); os.fsync(handle.fileno())
        sql(statement)
        repaired = repair['verify'](sql, prepared)
        save(folder / 'repair-verified.json', repaired)
        # Compute normal boot effects from the repaired current state. Never
        # restore a player snapshot or replay an uncertain SQL transaction.
        repaired_data = prior.saved()
        differences = {key for key in data if data[key] != repaired_data[key]}
        assert differences == {'inventory'}, differences
        expected = base.boot_state(repaired_data)
        unchanged(before); contract(); r.select(before['image'])
        r.compose('up', '-d', '--no-deps', '--wait', '--wait-timeout', '240', 'game')
        first = r.running(before['image'], binaries()); base.health(); time.sleep(8)
        current = r.running(before['image'], binaries()); assert first['started_at'] == current['started_at']
        assert prior.saved() == expected, 'Unexpected saved-state boot drift'
        repair['verify'](sql, prepared)
        rotation = market.verify_market(market_before, current['started_at'])
        unchanged(before); checks = contract(); base.health(); r.closed_ports()
        logs = r.out('docker', 'compose', 'logs', '--no-color', '--since', current['started_at'], 'game')
        assert not any(text in logs for text in ('MySQL Error', 'Orphaned Rule', 'Unknown column', 'Dungeon schema drift', 'Dungeon content drift', 'Dungeon item cache drift'))
        save(folder / 'verified-closed.json', {'runtime': current, 'game': r.compact('game'), 'checks': checks,
                                             'market': rotation, 'repair': repaired})
        print('Runtime and five icon-only repairs verified; access remains closed.', flush=True)
    except BaseException:
        h.hold(folder)
        raise


def open_access():
    before = read(EVIDENCE / 'preflight.json'); folder = EVIDENCE / 'activation'
    verified = read(folder / 'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder / 'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game') == verified['game']
        assert prior.saved() == read(folder / 'expected-boot-state.json')
        repair['verify'](sql, read(folder / 'repair-before.json'))
        unchanged(before); contract(); base.health(); r.closed_ports()
        save(folder / 'opening.json', {'owner_authorized': True})
        r.compose('up', '-d', '--no-deps', '--wait', '--wait-timeout', '60', 'gateway')
        current = r.running(before['image'], binaries()); base.health(); r.closed_ports()
        assert current['started_at'] == verified['runtime']['started_at'] and r.state('gateway')['State']['Running']
        unchanged(before, after_open=True)
        save(folder / 'deployed.json', {**verified, 'runtime': current, 'gateway_open': True,
             'source_revision': m['source_revision'], 'database_restored': False,
             'client_update_required': False, 'owner_visual_accepted': False})
        print('Icon fix and five saved-item repairs deployed; access restored. No client update required.', flush=True)
    except BaseException:
        h.hold(folder)
        raise


def main():
    assert __debug__; os.umask(0o077); initialize()
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=('preflight', 'activate', 'open'))
    action = parser.parse_args().action
    with (ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (ROOT / 'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'preflight': preflight, 'activate': activate, 'open': open_access}[action]()


if __name__ == '__main__':
    main()
