"""Read-only final paired Hate release verification after admissions and wiki.

Never fingerprints dynamic player state after opening. Prints only compact,
nonsensitive evidence; does not install, publish, restart or write receipts.
"""
import argparse
import base64
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

STAGE = Path('/opt/nightcap/releases/hate-layout-20261029-v1')
OPERATOR_SHA = '3f79d3833e431dc33c3e6f6323f950e3da328ec8924e26b7f7c2823641d05850'
MANIFEST_SHA = '468f85c5b7b5d9b108b1b55c108b7a068b04d11d7021f72290df0f58973987e8'
IMAGE = 'sha256:0dec2bfc8b2e83a30301c2fc203c5688d44a2b39cf354b5e0e0b2ba8ed38f9dd'
CHANNEL_SHA = 'de5959ffdb6dff44e3de9626cb8dba7c57dd4787fbe9912505d5b1955f10c5d8'
WIKI = '20261029-hate-layout-v1'
WIKI_INVENTORY_SHA = '1f5a56909af7568b81da99035d311a2f1a7e190dff69454538c9f298a63743ff'
WEB_CONFIG_SHA = '46355a5e09bc63bc0a05713c02a315966378ef2ecbc5856bbab2140093a619c6'
CLIENT_RECEIPT = Path('/opt/nightcap/releases/hate-client-2026102901/published.json')
ASSETS = {'hateplane.s3d', 'hateplane_obj.s3d', 'hateplane_chr.s3d',
          'hateplaneb.s3d', 'hateplaneb_obj.s3d', 'hateplaneb_chr.s3d', 'hateplaneb_chr.txt'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def authenticate(path, digest):
    assert path.resolve() == path and path.is_file() and not path.is_symlink(), str(path)
    assert sha(path) == digest, str(path)


def services(op, expected):
    assert set(expected) == {'game', 'gateway', 'db', 'web', 'tunnel'}
    for name, before in expected.items():
        row = op.r.state(name)
        assert all(row[key] == before[key] for key in ('Id', 'Image', 'RestartCount')), name
        assert all(row['State'][key] == before['state'][key] for key in ('Running', 'StartedAt', 'OOMKilled')), name
        assert row['State']['Running'] and not row['State']['OOMKilled'], name
        if name in ('game', 'db'):
            assert row['State']['Health']['Status'] == 'healthy', name


def runtime_files(op, expected):
    assert all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in expected)
    row = op.r.state('game')
    code = ('from pathlib import Path;import hashlib,json;r=Path("/opt/nightcap");'
            'names=' + repr(sorted(expected)) + ';'
            'print(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in names}))')
    actual = json.loads(op.r.out('docker', 'exec', row['Id'], 'python3', '-B', '-c', code))
    assert actual == expected, 'Running container file drift'
    return len(actual)


def publications(op):
    public = op.ROOT / 'data/public'
    authenticate(public / 'channel.json', CHANNEL_SHA)
    envelope = json.loads((public / 'channel.json').read_text())
    channel = json.loads(base64.b64decode(envelope['manifest'], validate=True))
    assert channel['release'] == 2026102901
    files = {entry['path']: entry for entry in channel['files']}
    assert len(files) == len(channel['files']) and ASSETS <= set(files)
    for name in ASSETS:
        entry = files[name]
        assert entry['url'] == 'https://play.nightcapgame.org/release/2026102901/' + name
        path = public / urlsplit(entry['url']).path.lstrip('/')
        authenticate(path, entry['sha256'])
        assert path.stat().st_size == entry['size']
    pointer = public / 'wiki/current'
    assert pointer.is_symlink() and pointer.readlink() == Path('releases') / WIKI
    history = op.ROOT / 'website-history' / WIKI / 'manifest.json'
    manifest = json.loads(history.read_text())
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == WIKI_INVENTORY_SHA and len(manifest) == 499
    root = public / 'wiki/releases' / WIKI
    assert root.resolve() == root and not root.is_symlink()
    assert all(not path.is_symlink() for path in root.rglob('*'))
    assert {path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()} == set(manifest)
    for name, digest in manifest.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        authenticate(root / name, digest)
    authenticate(op.ROOT / 'nginx.conf', WEB_CONFIG_SHA)
    return {'client_release': channel['release'], 'added_client_assets': len(ASSETS),
            'wiki_release': WIKI, 'wiki_files': len(manifest), 'public_http_verified_here': False}


def verify(op, guard_sha):
    authenticate(op.STAGE / 'manifest.json', MANIFEST_SHA)
    manifest = op.manifest()
    preflight = op.read(op.EVIDENCE / 'preflight.json')
    assert preflight['manifest_sha256'] == MANIFEST_SHA and preflight['image'] == IMAGE
    guard_path = op.STAGE / 'wiki-activation-guard.json'
    authenticate(guard_path, guard_sha)
    guard = op.read(guard_path)
    deployed_path = op.EVIDENCE / 'activation/deployed.json'
    assert guard['verified'] is True and guard['owner_gameplay_accepted'] is False
    assert guard['runtime_receipt'] == str(deployed_path) and guard['client_receipt'] == str(CLIENT_RECEIPT)
    authenticate(deployed_path, guard['runtime_receipt_sha256'])
    authenticate(CLIENT_RECEIPT, guard['client_receipt_sha256'])
    deployed = op.read(deployed_path)
    client = op.read(CLIENT_RECEIPT)
    assert deployed['gateway_open'] is True and deployed['database_restored'] is False
    assert deployed['owner_gameplay_accepted'] is False
    assert deployed['runtime']['image_id'] == IMAGE
    assert client['release'] == 2026102901
    assert guard['channel_sha256'] == client['channel_sha256'] == manifest['client_channel_new_sha256'] == CHANNEL_SHA
    services(op, guard['services_after'])
    runtime = op.r.running(IMAGE, op.binaries(), deployed['runtime']['restart_count'])
    assert runtime['started_at'] == deployed['runtime']['started_at']
    assert sum(name == 'zone' for name, digest in runtime['processes']) == 12
    for name in ('world', 'ucs', 'loginserver'):
        assert sum(kind == name for kind, digest in runtime['processes']) == 1
    file_count = runtime_files(op, {**manifest['base_hashes'], **manifest['candidate_hashes']})
    checks = op.contract()
    assert checks == {'schema': 51, 'content': 650}
    # public_preflight() deliberately is NOT used: it requires empty owned scopes.
    # Full installed contract plus complement fingerprints cover installed content.
    expected = {**preflight, 'publication': {
        'channels': dict(preflight['publication']['channels']),
        'wiki': str(Path('releases') / WIKI)}}
    op.unchanged(expected, quests=True, client=True)
    published = publications(op)
    op.base.health()
    op.r.closed_ports()
    services(op, guard['services_after'])
    authenticate(guard_path, guard_sha)
    authenticate(deployed_path, guard['runtime_receipt_sha256'])
    authenticate(CLIENT_RECEIPT, guard['client_receipt_sha256'])
    return {'status': 'passed', 'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'image_id': IMAGE, 'native_zone_workers': 12, 'runtime_files': file_count,
            'schema_checks': 51, 'content_checks': 650, 'services_preserved_since_open': True,
            'quest_content_cache_preserved': True, **published, 'owner_gameplay_accepted': False,
            'dynamic_player_state_compared': False, 'mutations_performed': False}


def main():
    import fcntl
    assert __debug__
    parser = argparse.ArgumentParser()
    parser.add_argument('--activation-guard-sha256', required=True)
    args = parser.parse_args()
    assert len(args.activation_guard_sha256) == 64 and all(c in '0123456789abcdef' for c in args.activation_guard_sha256)
    authenticate(STAGE / 'rollout.py', OPERATOR_SHA)
    authenticate(STAGE / 'manifest.json', MANIFEST_SHA)
    spec = importlib.util.spec_from_file_location('hate_final_verification_target', STAGE / 'rollout.py')
    op = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(op)
    assert op.STAGE == STAGE
    op.initialize()
    with (op.ROOT / '.deployment.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(json.dumps(verify(op, args.activation_guard_sha256)), flush=True)


if __name__ == '__main__':
    main()
