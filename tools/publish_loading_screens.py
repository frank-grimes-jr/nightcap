"""Publish the reviewed gallery and desktop under OVH's existing deployment lock.

Run on the host as: python3 publish_loading_screens.py <staging-dir> stage|publish
The staging inventory, captured baseline and signatures are verified before upload.
"""
import argparse
import base64
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path, PurePosixPath

PUBLIC = Path('/opt/nightcap/deploy/production/data/public')
GAME = 'release/2026100407'
DESKTOP = 'launcher/2026100401'
CHANNELS = ('launcher-channel.json', 'channel.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_file(stage, name, record, baseline):
    source = stage/name
    if source.exists():
        assert source.resolve().is_relative_to(stage.resolve()) and not source.is_symlink()
        return source
    # Reuse already hosted private client bytes; upload only the new assets.
    assert name.startswith(GAME+'/'), 'Missing staged payload: '+name
    asset = name[len(GAME)+1:]
    prior = baseline['public']['channel.json']['signed']
    old = {f['path']:f for f in prior['files']}
    assert asset in old and record == {k:old[asset][k] for k in ('size','sha256')}
    source = PUBLIC/'release'/str(prior['release'])/asset
    assert source.resolve().is_relative_to(PUBLIC.resolve()) and not source.is_symlink()
    return source


def inventory(stage):
    entries = json.loads((stage/'publication-files.json').read_text())
    audit = json.loads((stage/'release-audit.json').read_text())
    baseline = json.loads((stage/'baseline.json').read_text())
    assert audit['release'] == 2026100407 and len(audit['files']) == 104
    expected = set(CHANNELS) | {GAME+'/'+f['path'] for f in audit['files']} | {DESKTOP+'/nightcap-desktop.exe'}
    assert set(entries) == expected
    for name, record in entries.items():
        p = PurePosixPath(name)
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
        assert p.as_posix() == name
        source = source_file(stage,name,record,baseline)
        assert source.stat().st_size == record['size'] and sha(source) == record['sha256'], name
    assert entries['channel.json']['sha256'] == audit['channel_sha256']
    for f in audit['files']:
        assert entries[GAME+'/'+f['path']] == {k:f[k] for k in ('size','sha256')}
    desktop = json.loads(base64.b64decode(json.loads((stage/'launcher-channel.json').read_bytes())['Channel']))
    assert desktop['release'] == 2026100401 and desktop['version'] == '0.4.0'
    assert desktop['url'] == 'https://play.nightcapgame.org/'+DESKTOP+'/nightcap-desktop.exe'
    assert entries[DESKTOP+'/nightcap-desktop.exe'] == {k:desktop[k] for k in ('size','sha256')}
    return entries


def unchanged(entries, baseline):
    for name, expected in baseline['public'].items():
        allowed = {expected['sha256']}
        if name in CHANNELS:
            allowed.add(entries[name]['sha256'])
        assert sha(PUBLIC/name) in allowed, 'Public drift: '+name
    for service, expected in baseline['services'].items():
        cid = subprocess.check_output(['docker','compose','ps','-q',service], cwd=PUBLIC.parent.parent, text=True, timeout=30).strip()
        data = json.loads(subprocess.check_output(['docker','inspect',cid], text=True, timeout=30))[0]
        state = data['State']
        actual = {'id':cid, 'image_id':data['Image'], 'started_at':state['StartedAt'],
                  'restarts':data['RestartCount'], 'running':state['Running'],
                  'health':state.get('Health',{}).get('Status'), 'oom_killed':state.get('OOMKilled',False)}
        assert actual == expected, 'Service drift: '+service
        assert actual['running'] and not actual['oom_killed']
        if service in ('game','db'): assert actual['health'] == 'healthy'


def sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def copy_verified(source, target, digest):
    assert not target.is_symlink()
    if target.exists() and sha(target) == digest: return
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name(target.name+'.loading-partial')
    assert not pending.is_symlink()
    shutil.copyfile(source,pending)
    assert sha(pending) == digest
    pending.chmod(0o644)
    with pending.open('r+b') as handle: os.fsync(handle.fileno())
    os.replace(pending,target)
    sync(target.parent)


def immutable_group(stage, entries, prefix, baseline):
    target = PUBLIC/prefix
    files = {name[len(prefix)+1:]:record for name,record in entries.items() if name.startswith(prefix+'/')}
    if not target.exists():
        pending = target.with_name('.'+target.name+'.loading-pending')
        assert not pending.is_symlink()
        pending.mkdir(parents=True,exist_ok=True)
        for name,record in files.items():
            source = source_file(stage,prefix+'/'+name,record,baseline)
            copy_verified(source,pending/name,record['sha256'])
        assert {p.relative_to(pending).as_posix() for p in pending.rglob('*') if p.is_file()} == set(files)
        for p in [pending,*pending.rglob('*')]:
            assert not p.is_symlink()
            p.chmod(0o755 if p.is_dir() else 0o644)
        sync(pending)
        os.rename(pending,target)
        sync(target.parent)
    assert not target.is_symlink()
    assert {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} == set(files)
    for name,record in files.items(): assert sha(target/name) == record['sha256']


def publish(stage, entries, baseline):
    unchanged(entries,baseline)
    for name in CHANNELS:
        backup = stage/('previous-'+name)
        if not backup.exists():
            assert sha(PUBLIC/name) == baseline['public'][name]['sha256']
            with backup.open('xb') as handle:
                handle.write((PUBLIC/name).read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            sync(stage)
        assert sha(backup) == baseline['public'][name]['sha256']
    # Both immutable trees precede either pointer; desktop pointer precedes game.
    for prefix in (DESKTOP,GAME): immutable_group(stage,entries,prefix,baseline)
    unchanged(entries,baseline)
    for name in CHANNELS:
        copy_verified(stage/name,PUBLIC/name,entries[name]['sha256'])
    for name,record in entries.items(): assert sha(PUBLIC/name) == record['sha256']
    unchanged(entries,baseline)
    result = {'release':2026100407, 'launcher_release':2026100401, 'launcher_version':'0.4.0',
              'verified_game_files':104, 'new_loading_images':56, 'preserved_game_files':48,
              'channel_sha256':entries['channel.json']['sha256'],
              'launcher_channel_sha256':entries['launcher-channel.json']['sha256'],
              'services_unchanged':True, 'starter_zip_guide_unchanged':True}
    (stage/'published.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Assertions required')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',type=Path)
    parser.add_argument('action',choices=('stage','publish'))
    args = parser.parse_args()
    assert args.stage.resolve() == Path('/opt/nightcap/releases/loading-screens-2026100407')
    with (PUBLIC.parent.parent/'.deployment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        entries = inventory(args.stage)
        baseline = json.loads((args.stage/'baseline.json').read_text())
        assert baseline['public']['channel.json']['signed']['release'] < 2026100407
        assert baseline['public']['launcher-channel.json']['signed']['release'] < 2026100401
        unchanged(entries,baseline)
        print(json.dumps(publish(args.stage,entries,baseline) if args.action == 'publish'
                         else {'staged_files':len(entries),'production_unchanged':True}))
