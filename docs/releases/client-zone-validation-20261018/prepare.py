"""Stage the signed zone-only addition without changing public metadata."""
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

STAGE = Path('/opt/nightcap/releases/client-zone-validation-20261018')
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old_raw = (STAGE / 'previous-channel.json').read_bytes()
    new_raw = (STAGE / 'channel.json').read_bytes()
    old = json.loads(base64.b64decode(json.loads(old_raw)['manifest']))
    new = json.loads(base64.b64decode(json.loads(new_raw)['manifest']))
    assert old['release'] == 2026101702 and new['release'] == 2026101801
    assert len(old['files']) == 106 and len(new['files']) == 138
    assert sha(PUBLIC / 'channel.json') == hashlib.sha256(old_raw).hexdigest()
    assert new['patch_notes'][1:] == old['patch_notes']
    assert new['minimum_launcher'] == old['minimum_launcher'] == '0.6.0'
    assert new['tombstones'] == old['tombstones']
    previous = {f['path']: f for f in old['files']}
    pins = json.loads((STAGE / 'zone-archives.json').read_text())['files']
    entries = {}
    for f in new['files']:
        name = f['path']
        rel = PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
        assert f['url'] == 'https://play.nightcapgame.org/release/2026101801/' + name
        if name in previous:
            prior = previous[name]
            assert all(f[k] == prior[k] for k in ('size', 'sha256', 'required'))
            url = urlsplit(prior['url'])
            assert url.scheme == 'https' and url.netloc == 'play.nightcapgame.org'
            relative = PurePosixPath(url.path.lstrip('/'))
            assert relative.parts[0] == 'release' and '..' not in relative.parts
            source = PUBLIC / relative
        else:
            assert name in pins and f['sha256'] == pins[name]['sha256'] and f['required']
            source = STAGE / 'assets' / name
        assert source.is_file() and not source.is_symlink()
        assert source.stat().st_size == f['size'] and sha(source) == f['sha256'], name
        target = STAGE / 'release/2026101801' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert sha(target) == f['sha256']
        else:
            shutil.copyfile(source, target)
        entries['release/2026101801/' + name] = {k: f[k] for k in ('size', 'sha256')}
    assert set(previous) <= {f['path'] for f in new['files']}
    assert set(pins) <= {f['path'] for f in new['files']}
    entries['channel.json'] = {'size': len(new_raw), 'sha256': hashlib.sha256(new_raw).hexdigest()}
    (STAGE / 'publication-files.json').write_text(json.dumps(entries, indent=2) + '\n')
    (STAGE / 'release-audit.json').write_text(json.dumps({
        'release': new['release'], 'files': new['files'],
        'channel_sha256': entries['channel.json']['sha256'],
        'previous_assets_unchanged': True, 'added_assets': sorted(set(pins) - set(previous))}, indent=2) + '\n')
    public = {p.name: {'sha256': sha(p)} for p in PUBLIC.iterdir() if p.is_file() and not p.is_symlink()}
    public['channel.json']['signed'] = {'release': old['release']}
    services = {}
    for service in ('game', 'gateway', 'db', 'web', 'tunnel'):
        row = json.loads(subprocess.check_output(['docker', 'inspect', 'nightcap-production-' + service + '-1'], text=True))[0]
        state = row['State']
        services[service] = {'id': row['Id'], 'image_id': row['Image'], 'started_at': state['StartedAt'],
                             'restarts': row['RestartCount'], 'running': state['Running'],
                             'health': state.get('Health', {}).get('Status'), 'oom_killed': state.get('OOMKilled', False)}
    with (STAGE / 'baseline.json').open('x') as handle:
        json.dump({'public': public, 'services': services}, handle, indent=2)
    assert sha(PUBLIC / 'channel.json') == hashlib.sha256(old_raw).hexdigest()
    print(json.dumps({'staged': 138, 'added': 32, 'existing_preserved': 106, 'public_unchanged': True}))


if __name__ == '__main__':
    import fcntl
    with (PUBLIC.parent.parent / '.deployment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main()
