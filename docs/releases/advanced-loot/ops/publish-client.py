"""Publish advanced loot only after the matching server is ready with player access closed."""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath

STAGE = Path('/opt/nightcap/releases/advanced-loot-client-2026093006')
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')
RELEASE = 'release/2026093006'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    entries = json.loads((STAGE / 'publication-files.json').read_text())
    audit = json.loads((STAGE / 'release-audit.json').read_text())
    assert audit['release'] == 2026093006 and len(audit['files']) == 46
    assert set(entries) == {'channel.json'} | {RELEASE + '/' + f['path'] for f in audit['files']}
    for name, expected in entries.items():
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        assert relative.as_posix() == name
        path = STAGE / name
        assert path.resolve().is_relative_to(STAGE.resolve()) and path.is_file() and not path.is_symlink()
        assert path.stat().st_size == expected['size'] and sha(path) == expected['sha256'], name
    assert entries['channel.json']['sha256'] == audit['channel_sha256']
    for entry in audit['files']:
        assert entries[RELEASE + '/' + entry['path']] == {k: entry[k] for k in ('size', 'sha256')}
    return entries


def unchanged(entries, baseline, ready=False):
    for name,expected in baseline['public'].items():
        allowed={expected['sha256']}
        if name=='channel.json':allowed.add(entries[name]['sha256'])
        assert sha(PUBLIC/name) in allowed,'Public drift: '+name
    activation=None
    server_manifest=None
    if ready:
        activation=json.loads(Path('/opt/nightcap/releases/advanced-loot-evidence-20260930/server-ready.json').read_text())
        server_manifest=json.loads(Path('/opt/nightcap/releases/advanced-loot-20260930/manifest.json').read_text())
        assert server_manifest['client_release']==2026093006
        assert server_manifest['client_channel_sha256']==entries['channel.json']['sha256']
    for service,expected in baseline['services'].items():
        cid=subprocess.check_output(['docker','compose','ps','-aq',service],cwd=PUBLIC.parent.parent,text=True,timeout=30).strip()
        data=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=30))[0]
        state=data['State']
        actual={'id':cid,'image_id':data['Image'],'started_at':state['StartedAt'],
                'restarts':data['RestartCount'],'running':state['Running'],
                'health':state.get('Health',{}).get('Status'),'oom_killed':state.get('OOMKilled',False)}
        if ready and service=='game':
            assert actual['image_id']==activation['image_id'] and actual['started_at']==activation['started_at']
            assert actual['restarts']==activation['restart_count'] and actual['running'] and actual['health']=='healthy' and not actual['oom_killed']
        elif ready and service=='gateway':
            assert actual['id']==expected['id'] and actual['image_id']==expected['image_id']
            assert not actual['running'],'Player access must remain closed until publication verification'
        else:
            assert actual==expected,'Service drift: '+service
            assert actual['running'] and not actual['oom_killed']
            if service in ('db','game'):assert actual['health']=='healthy'


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def copy_verified(source, target, digest):
    assert not target.is_symlink()
    if target.exists() and sha(target) == digest:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name(target.name + '.advloot-partial')
    assert not pending.is_symlink()
    shutil.copyfile(source, pending)
    assert sha(pending) == digest
    pending.chmod(0o644)
    with pending.open('r+b') as handle:
        os.fsync(handle.fileno())
    os.replace(pending, target)
    sync_directory(target.parent)


def publish(entries, baseline):
    unchanged(entries, baseline, ready=True)
    backup = STAGE / 'previous-channel.json'
    if not backup.exists():
        assert sha(PUBLIC / 'channel.json') == baseline['public']['channel.json']['sha256']
        with backup.open('xb') as handle:
            handle.write((PUBLIC / 'channel.json').read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        sync_directory(STAGE)
    assert sha(backup) == baseline['public']['channel.json']['sha256']
    target = PUBLIC / RELEASE
    assets = {name[len(RELEASE) + 1:]: entry for name, entry in entries.items() if name.startswith(RELEASE + '/')}
    if not target.exists():
        pending = target.with_name('.' + target.name + '.advloot-pending')
        assert not pending.is_symlink()
        pending.mkdir(parents=True, exist_ok=True)
        for name, entry in assets.items():
            copy_verified(STAGE / RELEASE / name, pending / name, entry['sha256'])
        assert {p.relative_to(pending).as_posix() for p in pending.rglob('*') if p.is_file()} == set(assets)
        for path in [pending, *pending.rglob('*')]:
            assert not path.is_symlink()
            path.chmod(0o755 if path.is_dir() else 0o644)
        sync_directory(pending)
        os.rename(pending, target)
        sync_directory(target.parent)
    assert not target.is_symlink()
    assert {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} == set(assets)
    for name, entry in assets.items():
        assert sha(target / name) == entry['sha256']
    unchanged(entries, baseline, ready=True)
    copy_verified(STAGE / 'channel.json', PUBLIC / 'channel.json', entries['channel.json']['sha256'])
    for name, entry in entries.items():
        assert sha(PUBLIC / name) == entry['sha256']
    unchanged(entries, baseline, ready=True)
    result = {'release': 2026093006, 'verified_files': 46,
              'channel_sha256': entries['channel.json']['sha256'],
              'previous_release': baseline['public']['channel.json']['signed']['release'],
              'matching_server_ready_gateway_closed': True, 'desktop_starter_guide_unchanged': True}
    (STAGE / 'published.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Assertions required')
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stage', 'publish'))
    args = parser.parse_args()
    assert Path(__file__).resolve() == STAGE / 'publish.py'
    with (STAGE / 'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        entries = inventory()
        baseline = json.loads((STAGE / 'baseline.json').read_text())
        assert baseline['public']['channel.json']['signed']['release'] < 2026093006
        unchanged(entries, baseline, ready=args.action=='publish')
        if args.action == 'stage':
            print(json.dumps({'staged_files': len(entries), 'production_unchanged': True}))
        else:
            publish(entries, baseline)
