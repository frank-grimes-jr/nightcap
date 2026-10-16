"""Temporary AA duration rollout: replace zone and preserve the signed client.

Never restores SQL or retries uncertain access. The current image supplies every
unchanged binary/support file, including the deployed divine-summon loader.
"""
import argparse
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time

STAGE = Path('/opt/nightcap/releases/aa-temporary-buffs-20261016')
sys.path.insert(0, '/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
r.STAGE = STAGE
r.EVIDENCE = STAGE / 'evidence'
ROOT = r.ROOT
BINARY_NAMES = {'world', 'zone', 'ucs', 'loginserver', 'shared_memory'}
CLIENT_RECEIPT = 'client-verification.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def exists(name):
    return (r.EVIDENCE / name).exists()


def manifest():
    value = json.loads((STAGE / 'manifest.json').read_text())
    assert re.fullmatch('[0-9a-f]{64}', value.get('client_channel_sha256', '')), 'Missing signed client channel hash'
    assert isinstance(value.get('client_release'), int) and value['client_release'] > 0, 'Missing client release'
    assert set(value.get('base_binaries', {})) == BINARY_NAMES, 'Missing complete reviewed native baseline'
    assert all(re.fullmatch('[0-9a-f]{64}', digest) for digest in value['base_binaries'].values()), 'Invalid reviewed native baseline hash'
    assert set(value['binaries']) in ({'zone'}, BINARY_NAMES), 'Unsupported native replacement set'
    assert re.fullmatch('[0-9a-f]{64}', value['binaries']['zone']), 'Invalid candidate zone hash'
    assert sha(Path(r.__file__)) == value['runtime_helper_sha256'], 'Runtime helper drift'
    assert {'zone', 'rollout.py', 'test_rollout.py', CLIENT_RECEIPT} <= set(value['files']), 'Unpinned release input'
    for name, digest in value['files'].items():
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        path = STAGE / name
        assert path.resolve().is_relative_to(STAGE.resolve()) and not path.is_symlink() and sha(path) == digest, name
    assert value['files']['zone'] == value['binaries']['zone'], 'Candidate zone mismatch'
    assert isinstance(value.get('baseline_restarts'), int) and value['baseline_restarts'] >= 0, 'Missing reviewed restart baseline'
    signed_client_receipt(value)
    return value


def signed_client_receipt(m):
    # The existing launcher verifier authenticates the staged envelope against
    # the previously shipped production key. Pin its exact report in manifest.
    path = STAGE / CLIENT_RECEIPT
    assert sha(path) == m['files'][CLIENT_RECEIPT], 'Client signature verification receipt drift'
    receipt = json.loads(path.read_text())
    assert receipt.get('signature') == 'valid against shipped production public key', 'Client signature not verified'
    assert receipt.get('release') == m['client_release'], 'Client verification release mismatch'
    assert receipt.get('channel_sha256') == m['client_channel_sha256'], 'Client verification channel mismatch'
    assert isinstance(receipt.get('verified_files'), int) and receipt['verified_files'] > 0, 'Client files not verified'
    return receipt


def verify_publication(m):
    receipt = signed_client_receipt(m)
    public = ROOT / 'data/public'
    raw = (public / 'channel.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m['client_channel_sha256'], 'Signed client channel is not published'
    envelope = json.loads(raw)
    assert envelope.get('signature'), 'Published channel lacks signature'
    signed = json.loads(base64.b64decode(envelope['manifest'], validate=True))
    assert signed['release'] == m['client_release'], 'Published release mismatch'
    assert datetime.fromisoformat(signed['expires'].replace('Z', '+00:00')) > datetime.now(timezone.utc), 'Signed client expired'
    files = signed['files']
    assert len(files) == receipt['verified_files'], 'Published file count mismatch'
    release = public / 'release' / str(m['client_release'])
    names = set()
    for entry in files:
        name = entry['path']
        relative = PurePosixPath(name)
        assert name and not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        assert relative.as_posix() == name and name not in names and entry['required'], 'Unsafe signed asset'
        names.add(name)
        assert entry['url'] == f"https://play.nightcapgame.org/release/{m['client_release']}/{name}", 'Unexpected signed asset URL'
        path = release / name
        assert path.resolve().is_relative_to(release.resolve()) and not path.is_symlink(), 'Unsafe published asset'
        assert path.stat().st_size == entry['size'] and sha(path) == entry['sha256'], 'Published asset differs: ' + name
    assert {path.relative_to(release).as_posix() for path in release.rglob('*') if path.is_file()} == names, 'Unexpected published files'
    return {'release': m['client_release'], 'channel_sha256': m['client_channel_sha256'], 'verified_files': len(files)}


def policies():
    return r.sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')


def extras():
    tables = r.sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap\\_%' AND TABLE_NAME NOT IN ('nightcap_market_offers','nightcap_market_state') ORDER BY TABLE_NAME;").splitlines()
    assert all(re.fullmatch('[a-zA-Z0-9_]+', name) for name in tables)
    result = {name: r.sql('CHECKSUM TABLE `' + name + '` EXTENDED;').strip().split('\t')[-1] for name in tables}
    assert all(value.isdigit() for value in result.values()), 'Invalid custom table checksum'
    return result


def unchanged(p, channel=None):
    for service in ('db', 'web', 'tunnel'):
        assert r.compact(service) == p['services'][service], 'Supporting service drift: ' + service
    assert r.runtime() == p['runtime'], 'Quest/plugin drift'
    public = dict(p['public'])
    if channel is not None:
        assert channel == public['channel.json'], 'Existing client publication changed'
    assert r.public() == public, 'Public channel/launcher/archive/guide drift'
    assert policies() == p['policies'], 'Policy drift'
    assert r.content_data() == p['content'], 'Content drift'


def binaries(p, candidate=False):
    result = {name: p['old_hashes']['bin/' + name] for name in BINARY_NAMES}
    if candidate:
        result['zone'] = p['zone_sha256']
    return result


def select(image):
    path = ROOT / '.env'
    lines = path.read_text().splitlines()
    assert sum(line.startswith('NIGHTCAP_GAME_IMAGE=') for line in lines) == 1
    data = '\n'.join('NIGHTCAP_GAME_IMAGE=' + image if line.startswith('NIGHTCAP_GAME_IMAGE=') else line for line in lines) + '\n'
    pending = path.with_name('.env.aa-temporary-buffs-' + str(time.time_ns()))
    mode = path.stat()
    with pending.open('x') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(pending, mode.st_mode & 0o777)
    os.chown(pending, mode.st_uid, mode.st_gid)
    os.replace(pending, path)


def validate_image(image):
    libraries = r.out('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'ldd', image, '/opt/nightcap/bin/zone')
    assert 'not found' not in libraries, 'Missing zone runtime library'
    r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python3', image, '-c', "import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker', 'run', '--rm', '--network', 'none', '--entrypoint', '/opt/nightcap/bin/loginserver', image, '--nightcap-crypto-self-test')


def preflight():
    m = manifest()
    assert not r.EVIDENCE.exists(), 'Existing rollout evidence; do not replay'
    old = r.compact('game')
    assert old['running'] and old['health'] == 'healthy' and old['restarts'] == m['baseline_restarts'], 'Unhealthy or unexpected baseline'
    hashes = r.image_hashes(old['image_id'])
    old_binaries = {name: hashes['bin/' + name] for name in BINARY_NAMES}
    assert m['base_binaries'] == old_binaries, 'Deployed baseline differs'
    if set(m['binaries']) == BINARY_NAMES:
        assert m['binaries'] == {**old_binaries, 'zone': m['binaries']['zone']}, 'Unrelated binary replacement'
    r.running(old['image_id'], old_binaries, expected_restarts=old['restarts'])
    services = {name: r.compact(name) for name in ('game', 'gateway', 'db', 'web', 'tunnel')}
    assert services['game'] == old, 'Baseline changed before capture'
    assert services['gateway']['running'], 'Gateway not in expected baseline state'
    r.closed_ports()
    snapshot = {'manifest_sha256': sha(STAGE / 'manifest.json'), 'old_image_id': old['image_id'],
                'old_hashes': hashes, 'zone_sha256': m['binaries']['zone'], 'services': services,
                'runtime': r.runtime(), 'public': r.public(), 'content': r.content_data(), 'policies': policies()}
    assert snapshot['public']['channel.json'] == m['client_channel_sha256'], 'Existing client changed before native activation'
    verify_publication(m)
    tag = 'nightcap-game:aa-temporary-buffs-base-20261016'
    r.call('docker', 'tag', old['image_id'], tag)
    assert r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', tag).strip() == old['image_id']
    (STAGE / 'Dockerfile').write_text('FROM ' + tag + '\nCOPY zone /opt/nightcap/bin/zone\n')
    r.call('docker', 'build', '--network', 'none', '-t', 'nightcap-game:aa-temporary-buffs-20261016', str(STAGE))
    new = r.out('docker', 'image', 'inspect', '--format', '{{.Id}}', 'nightcap-game:aa-temporary-buffs-20261016').strip()
    assert r.image_hashes(new) == {**hashes, 'bin/zone': m['binaries']['zone']}, 'Candidate modified unrelated runtime files'
    layers = lambda image: json.loads(r.out('docker', 'image', 'inspect', image))[0]['RootFS']['Layers']
    before, after = layers(old['image_id']), layers(new)
    assert after[:len(before)] == before and len(after) == len(before) + 1, 'Unexpected image ancestry'
    validate_image(new)
    validate_image(old['image_id'])
    unchanged(snapshot)
    assert r.compact('game') == services['game'] and r.compact('gateway') == services['gateway'], 'Baseline changed during preflight'
    r.EVIDENCE.mkdir(mode=0o700)
    snapshot.update(new_image_id=new, backup=r.database_backup())
    save('preflight.json', snapshot)
    print(json.dumps({'status': 'preflight_passed', 'new_image_id': new, 'old_image_id': old['image_id'], 'baseline_restarts': old['restarts']}), flush=True)


def stopped():
    game = r.state('game')['State']
    assert not r.state('gateway')['State']['Running'] and not game['Running'], 'Services did not stop'
    assert game['ExitCode'] == 0 and not game.get('OOMKilled'), 'Unclean game shutdown'


def preserved(p, data):
    assert r.player_data() == data['player'] and extras() == data['custom'], 'Persisted data drift while gateway closed'


def hold(reason, p, access_uncertain=False):
    r.compose('stop', 'gateway')
    assert not r.state('gateway')['State']['Running'], 'Gateway failed to close'
    save('recovery-held.json', {'old_image_id': p['old_image_id'], 'current_image_id': r.compact('game')['image_id'],
                              'gateway_open': False, 'database_restored': False,
                              'access_may_have_opened': access_uncertain, 'reason': reason})


def recover(p, data, access_uncertain=False, allow_reopen=True):
    # Once an open command was issued, retain the candidate and every subsequent
    # player write. A lost reply never authorizes an image/access or SQL replay.
    if not access_uncertain:
        try:
            access_uncertain = (r.compact('game')['image_id'] == p['new_image_id']
                                and r.state('gateway')['State']['Running'])
        except BaseException:
            access_uncertain = True
    if access_uncertain:
        hold('Gateway acknowledgment or post-open verification uncertain; operator reconciliation required', p, True)
        return
    try:
        r.compose('stop', 'gateway')
        r.compose('stop', '-t', '90', 'game')
        assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
        assert r.image_hashes(p['old_image_id']) == p['old_hashes'], 'Rollback image drift'
        select(p['old_image_id'])
        r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        same_container = r.compact('game')['id'] == p['services']['game']['id']
        restart_count = p['services']['game']['restarts'] if same_container else 0
        r.running(p['old_image_id'], binaries(p), expected_restarts=restart_count)
        if data is not None:
            preserved(p, data)
        unchanged(p)  # In particular, only the paired OLD public channel permits reopening.
        r.closed_ports()
        if not allow_reopen:
            hold('Open validation failed; prior image restored but access checks require reconciliation', p)
            return
        save('recovery-opening.json', {'old_image_id': p['old_image_id'], 'database_restored': False})
        r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert r.state('gateway')['State']['Running']
        unchanged(p)
        r.closed_ports()
        save('rolled-back.json', {'old_image_id': p['old_image_id'], 'database_restored': False, 'gateway_open': True})
    except BaseException:
        hold('Recovery validation failed, persisted data drifted, or public channel is new/unknown', p,
             access_uncertain=exists('recovery-opening.json'))
        raise


def activate():
    m, p = manifest(), load('preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json'), 'Manifest changed'
    assert not exists('activation-started.json'), 'Activation already started; do not replay'
    assert r.compact('game') == p['services']['game'] and r.compact('gateway') == p['services']['gateway'], 'Baseline service drift'
    assert r.image_hashes(p['new_image_id']) == {**p['old_hashes'], 'bin/zone': m['binaries']['zone']}
    unchanged(p)
    r.closed_ports()
    data = None
    save('activation-started.json', {'new_image_id': p['new_image_id'], 'database_restored': False})
    try:
        r.compose('stop', 'gateway')
        r.compose('stop', '-t', '90', 'game')
        stopped()
        data = {'player': r.player_data(), 'custom': extras()}
        save('stopped-data.json', data)
        select(p['new_image_id'])
        r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        first = r.running(p['new_image_id'], binaries(p, True), expected_restarts=0)
        time.sleep(5)
        result = r.running(p['new_image_id'], binaries(p, True), expected_restarts=0)
        assert result['started_at'] == first['started_at'], 'Candidate restarted during verification'
        preserved(p, data)
        unchanged(p)
        assert not r.state('gateway')['State']['Running'], 'Gateway reopened during activation'
        save('activated-closed.json', {'runtime': result, 'game': r.compact('game'), 'gateway_open': False,
                                       'player_tables_preserved': len(data['player']), 'custom_tables_preserved': len(data['custom']),
                                       'database_restored': False, 'backup': p['backup']})
        print(json.dumps({'status': 'activated_closed', 'zone_sha256': p['zone_sha256'], 'gateway_open': False}), flush=True)
    except BaseException:
        recover(p, data)
        raise


def open_access():
    m, p = manifest(), load('preflight.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json'), 'Manifest changed'
    a, data = load('activated-closed.json'), load('stopped-data.json')
    assert not exists('opening.json') and not exists('recovery-held.json'), 'Access/recovery already attempted; do not replay'
    access_uncertain = False
    try:
        if r.state('gateway')['State']['Running']:
            access_uncertain = True
            raise RuntimeError('Gateway already open; preserve candidate and subsequent activity')
        assert r.compact('game') == a['game'], 'Activated runtime changed before access'
        result = r.running(p['new_image_id'], binaries(p, True), expected_restarts=0)
        assert result['started_at'] == a['runtime']['started_at'], 'Activated runtime restarted'
        publication = verify_publication(m)
        preserved(p, data)
        unchanged(p, m['client_channel_sha256'])
        r.closed_ports()
        save('opening.json', {'runtime': result, 'publication': publication, 'database_restored': False})
        access_uncertain = True
        r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert r.state('gateway')['State']['Running'], 'Gateway did not open'
        result = r.running(p['new_image_id'], binaries(p, True), expected_restarts=0)
        assert result['started_at'] == a['runtime']['started_at'], 'Runtime restarted at access boundary'
        unchanged(p, m['client_channel_sha256'])
        r.closed_ports()
        # Player state can legitimately change now. Never compare/rewrite it.
        save('activated.json', {**a, 'runtime': result, 'gateway_open': True, 'publication': publication})
        print(json.dumps({'status': 'activated', 'gateway_open': True, **publication}), flush=True)
    except BaseException:
        recover(p, data, access_uncertain=access_uncertain, allow_reopen=False)
        raise


def report():
    m, p, a = manifest(), load('preflight.json'), load('activated.json')
    assert p['manifest_sha256'] == sha(STAGE / 'manifest.json')
    result = r.running(p['new_image_id'], binaries(p, True), expected_restarts=0)
    assert result['started_at'] == a['runtime']['started_at'] and r.compact('gateway')['running']
    unchanged(p, m['client_channel_sha256'])
    r.closed_ports()
    publication = verify_publication(m)
    print(json.dumps({'status': 'healthy', 'runtime': result, 'gateway_open': True, 'database_restored': False,
                      'player_tables_preserved': a['player_tables_preserved'], 'custom_tables_preserved': a['custom_tables_preserved'],
                      'publication': publication}), flush=True)


def require_no_gm_work():
    assert not (ROOT / 'private/gm-maintenance.json').exists(), 'GM maintenance is active'
    assert r.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1', 'GM SQL action in flight'


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required')
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['preflight', 'activate', 'open', 'report'])
    action = parser.parse_args().action
    with (ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm_lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require_no_gm_work()
        {'preflight': preflight, 'activate': activate, 'open': open_access, 'report': report}[action]()
