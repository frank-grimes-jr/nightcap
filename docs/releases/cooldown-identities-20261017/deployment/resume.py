"""One-shot continuation of the held Oct 18 release; preserves Karl's authorized port.

Stage this file and test_resume.py under the original release's resume/ directory
with a separate manifest.json. Never reruns activation, rehearsal or the old backup.
"""
import argparse
import copy
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

STAGE = Path('/opt/nightcap/releases/cooldown-identities-20261018')
RECOVERY = STAGE / 'resume'
ORIGINAL_MANIFEST = '5684a9e663561ea77f35867cc89047297e0c30bbb77a3989d970e7358a5372fa'
HOLD_NAME = 'held-1792334750620816674.json'
HOLD_SHA = 'a7a39b4e0a10fd2b4144cc5e3ad263f345d2581652517b42d3288dff38752137'
DIFF_SHA = 'eaaa2a1b65948356785bb75699f381cc3450e49b1bd931cca342c120bcce0b74'
BEFORE_SHA = '7160dcd143d7802f9594187ca7c752de8bf531bf5bfda741847f5d60e660c9b7'
AFTER_SHA = '5c35442583802371a31cad2132e70e97fc932ac0aa9f28869ae8d36ad8e64b83'
CATALOG_SHA = 'cb4eac057afbbaac5fb3cc18ba402ae4eb74e5e1175a7e5803206c4dae95912d'
EXPECTED_DIFF = {
    'baseline_matches_stopped_fingerprint': True,
    'restored_fingerprint': BEFORE_SHA,
    'differences': [{'id': '27', 'columns': {
        'zone_id': {'before': '63', 'now': '36'},
        'y': {'before': '545.816', 'now': '-82'},
        'x': {'before': '6.74787', 'now': '35'},
        'z': {'before': '3.127', 'now': '3'},
        'heading': {'before': '322.5', 'now': '0'},
    }}],
}
op = None


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    with (RECOVERY / 'evidence' / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def manifest():
    value = read(RECOVERY / 'manifest.json')
    assert value['original_manifest_sha256'] == ORIGINAL_MANIFEST
    assert set(value['files']) == {'resume.py', 'test_resume.py'}
    for name, digest in value['files'].items():
        path = RECOVERY / name
        assert not path.is_symlink() and sha(path) == digest, name
    assert sha(STAGE / 'manifest.json') == ORIGINAL_MANIFEST
    original = read(STAGE / 'manifest.json')
    for name in ('rollout.py', 'capture.py', 'cooldown_identity_migration.py'):
        assert sha(STAGE / name) == original['files'][name], name
    return value


def known_hold():
    assert sorted(path.name for path in op.EVIDENCE.glob('held-*.json')) == [HOLD_NAME], 'New or missing hold'
    path = op.EVIDENCE / HOLD_NAME
    assert sha(path) == HOLD_SHA
    held = read(path)
    assert held['both_stopped'] and held['running'] == {'gateway': False, 'game': False}
    assert held['database_restored'] is False


def resolved_data():
    diff = op.PRIVATE / 'character-backup-diff.json'
    assert sha(diff) == DIFF_SHA and read(diff) == EXPECTED_DIFF, 'Unauthorized character delta'
    data = op.load('stopped-data.json', True)
    assert data['player']['character_data'] == {'rows': 31, 'sha256': BEFORE_SHA}
    data = copy.deepcopy(data)
    data['player']['character_data']['sha256'] = AFTER_SHA
    return data


def preserve_resolved(data):
    op.preserved(data)
    assert op.sql('SELECT id,zone_id,zone_instance,x,y,z,heading FROM character_data WHERE id=27;').strip() == '27\t36\t0\t35\t-82\t3\t0', 'Authorized port changed'


def verify_backup(receipt, expected_path):
    path = Path(receipt['path'])
    assert path == expected_path and not path.is_symlink()
    assert receipt['gzip_integrity'] == 'passed' and sha(path) == receipt['sha256']
    assert path.stat().st_size == receipt['compressed_bytes']
    size, tail = 0, b''
    with gzip.open(path, 'rb') as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            tail = (tail + chunk)[-4096:]
    assert size == receipt['uncompressed_bytes'] and size > 1000000
    assert b'-- Dump completed on' in tail, 'Truncated stopped backup'


def saved_inputs():
    inputs = op.load('migration-inputs.json')
    assert inputs['catalog_sha256'] == CATALOG_SHA == sha(op.PRIVATE / 'catalog.json')
    catalog = op.load('catalog.json', True)
    forward = (op.PRIVATE / 'forward.sql').read_text()
    reverse = (op.PRIVATE / 'rollback.sql').read_text()
    assert sha(op.PRIVATE / 'forward.sql') == inputs['forward_sha256']
    assert sha(op.PRIVATE / 'rollback.sql') == inputs['rollback_sha256']
    assert forward == op.migration.sql(catalog, CATALOG_SHA)
    assert reverse == op.migration.sql(catalog, CATALOG_SHA, True)
    rehearsal = op.load('stopped-migration-rehearsal.json')
    assert rehearsal == {'passed': True, 'catalog_sha256': CATALOG_SHA, 'new_timer_rows': 15, 'live_sql_modified': False}
    return inputs, catalog, forward


def before_live(p, data, before, item_rows):
    op.stopped()
    known_hold()
    for name in ('migration-attempted.json', 'migration-applied.json', 'verified-closed.json', 'opening.json', 'activated.json'):
        assert not (op.EVIDENCE / name).exists(), 'Original continuation already attempted'
    assert op.sql("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME IN ('nightcap_cooldown_schema','nightcap_cooldown_backup_v1','nightcap_cooldown_rollback_v1');").strip() == '0'
    assert op.sql('SELECT COUNT(*) FROM timers WHERE type>=1048576;').strip() == '0'
    assert op.sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='" + op.SCRATCH + "';").strip() == '0'
    assert op.timers() == before and op.item_recasts() == item_rows
    assert op.market_state() == op.load('market-before.json'), 'Market changed while held'
    preserve_resolved(data)
    op.untouched(p)


def continue_activation():
    manifest()
    op.manifest()
    p = op.load('preflight.json')
    assert p['manifest_sha256'] == ORIGINAL_MANIFEST
    assert (op.EVIDENCE / 'activation-started.json').exists() and (op.EVIDENCE / 'shutdown.json').exists()
    assert not (RECOVERY / 'evidence').exists(), 'Resume cannot be replayed'
    assert not (RECOVERY / 'private-backup').exists(), 'Prior supplemental backup exists'
    inputs, catalog, forward = saved_inputs()
    data = resolved_data()
    before, item_rows = op.load('stopped-timers.json', True), op.load('stopped-item-recasts.json', True)
    before_live(p, data, before, item_rows)
    verify_backup(op.load('backup.json'), STAGE / 'private-backup' / 'peq-before.sql.gz')
    assert op.shutil.disk_usage(op.ROOT).free >= 4 * 1024**3
    (RECOVERY / 'evidence').mkdir(mode=0o700)
    save('resume-started.json', {'manifest_sha256': sha(RECOVERY / 'manifest.json'),
        'original_manifest_sha256': ORIGINAL_MANIFEST, 'resolved_hold': {HOLD_NAME: HOLD_SHA},
        'authorized_request_thread': '01a14f71-6c38-7f42-afc7-6b00dcbabba5', 'character_diff_sha256': DIFF_SHA,
        'rehearsal_repeated': False, 'database_restored': False})
    try:
        save('resolved-data.json', data)
        previous_stage = op.r.STAGE
        try:
            op.r.STAGE = RECOVERY
            backup = op.r.database_backup()
        finally:
            op.r.STAGE = previous_stage
        verify_backup(backup, RECOVERY / 'private-backup' / 'peq-before.sql.gz')
        save('supplemental-backup.json', backup)
        before_live(p, data, before, item_rows)
        manifest()
        op.save('migration-attempted.json', inputs)
        op.sql(forward)
        added = op.verify_migration(catalog, CATALOG_SHA, before, item_rows)
        preserve_resolved(data)
        op.untouched(p)
        op.save('migration-applied.json', {'catalog_sha256': CATALOG_SHA, 'legacy_rows_preserved': len(before),
            'new_timer_rows': added, 'item_records_preserved': len(item_rows)})
        op.r.select(p['new_image_id'])
        op.r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        first = op.r.running(p['new_image_id'], op.binaries(p))
        op.health()
        op.time.sleep(16)
        op.health()
        current = op.r.running(p['new_image_id'], op.binaries(p))
        assert first['started_at'] == current['started_at']
        rotation = op.verify_market(op.load('market-before.json'), current['started_at'])
        preserve_resolved(data)
        op.untouched(p)
        op.verify_migration(catalog, CATALOG_SHA, before, item_rows)
        assert not op.r.state('gateway')['State']['Running']
        known_hold()
        op.save('verified-closed.json', {'runtime': current, 'game': op.r.compact('game'), 'market_rotation': rotation,
            'cache_sha256': p['cache_sha256'], 'player_tables_preserved': len(data['player']),
            'custom_tables_preserved': len(data['custom'])})
        save('hold-resolution.json', {'held_receipts': {HOLD_NAME: HOLD_SHA}, 'resolved_data_sha256': sha(RECOVERY / 'evidence' / 'resolved-data.json'),
            'verified_closed_sha256': sha(op.EVIDENCE / 'verified-closed.json'), 'character_diff_sha256': DIFF_SHA})
        print('Recovered migration verified; original hold retained and gateway closed.', flush=True)
    except BaseException:
        op.hold('Cooldown recovery failed/uncertain. Never replay SQL or start old uint16 code.')
        raise


def open_access():
    manifest()
    op.manifest()
    started = read(RECOVERY / 'evidence' / 'resume-started.json')
    assert started['manifest_sha256'] == sha(RECOVERY / 'manifest.json')
    p, a = op.load('preflight.json'), op.load('verified-closed.json')
    assert p['manifest_sha256'] == ORIGINAL_MANIFEST
    known_hold()
    resolution = read(RECOVERY / 'evidence' / 'hold-resolution.json')
    assert resolution == {'held_receipts': {HOLD_NAME: HOLD_SHA}, 'resolved_data_sha256': sha(RECOVERY / 'evidence' / 'resolved-data.json'),
        'verified_closed_sha256': sha(op.EVIDENCE / 'verified-closed.json'), 'character_diff_sha256': DIFF_SHA}
    assert not (op.EVIDENCE / 'opening.json').exists() and not (op.EVIDENCE / 'activated.json').exists()
    try:
        assert not op.r.state('gateway')['State']['Running'] and op.r.compact('game') == a['game']
        data = resolved_data()
        assert read(RECOVERY / 'evidence' / 'resolved-data.json') == data
        _, catalog, _ = saved_inputs()
        op.verify_migration(catalog, CATALOG_SHA, op.load('stopped-timers.json', True), op.load('stopped-item-recasts.json', True))
        preserve_resolved(data)
        op.untouched(p)
        op.health()
        assert op.verify_market(op.load('market-before.json'), a['runtime']['started_at']) == a['market_rotation']
        op.save('opening.json', {'catalog_sha256': CATALOG_SHA, 'client_channel_sha256': op.manifest()['client_channel_sha256'],
            'recovery_manifest_sha256': started['manifest_sha256'], 'resolved_hold': {HOLD_NAME: HOLD_SHA}})
        op.r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert op.r.state('gateway')['State']['Running']
        op.health()
        op.r.closed_ports()
        current = op.r.running(p['new_image_id'], op.binaries(p))
        assert current['started_at'] == a['runtime']['started_at']
        op.untouched(p)  # Player state can change after the gateway opens.
        op.save('activated.json', {'status': 'deployed', 'gateway_open': True, 'runtime': current,
            'migration': op.load('migration-applied.json'), 'market_rotation': a['market_rotation'], 'cache_sha256': p['cache_sha256'],
            'client_release': op.manifest()['client_release'], 'database_restored': False, 'owner_gameplay_accepted': False,
            'player_tables_preserved': a['player_tables_preserved'], 'custom_tables_preserved': a['custom_tables_preserved'],
            'recovery_manifest_sha256': started['manifest_sha256'], 'authorized_port_preserved': True})
        print('Cooldown correction deployed; authorized port preserved and access open.', flush=True)
    except BaseException:
        op.hold('Recovery opening failed/uncertain. Preserve subsequent activity; inspect receipts.')
        raise


def initialize():
    global op
    assert Path(__file__).resolve() == (RECOVERY / 'resume.py').resolve()
    manifest()
    sys.path.insert(0, str(STAGE))
    spec = importlib.util.spec_from_file_location('immutable_cooldown_rollout', STAGE / 'rollout.py')
    op = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(op)
    op.initialize()


if __name__ == '__main__':
    assert __debug__
    os.umask(0o077)
    initialize()
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['resume', 'open'])
    action = parser.parse_args().action
    with (op.ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (op.ROOT / 'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'resume': continue_activation, 'open': open_access}[action]()
