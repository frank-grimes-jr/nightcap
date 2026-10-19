"""Publish only the reviewed catalog and signed channel after owner approval.

Run on OVH with --stage /absolute/stage --publish. No service commands mutate state.
The exact signed inputs are pinned; the other 137 URLs and asset bytes are retained.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

OLD = '4fd7087b9a1d255c19c5ce7e3a3529c67459b339e0acbdf7dcf9a038c7cc6242'
NEW = '6db028c3f460fa2224c0398aa199384eeb4dd17fb6ba604740cfe7414da53bd5'
CATALOG = '2599919e5701d4b2dc43e569da72a3d99e503ae6f511f690d7a09fe581f1a8b4'
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def replace(source, target):
    pending = target.with_name(target.name + '.contract-repair-partial')
    require(not target.is_symlink() and not pending.is_symlink(), 'Symlink target')
    with pending.open('wb') as handle:
        handle.write(source)
        handle.flush()
        os.fsync(handle.fileno())
    pending.chmod(0o644)
    os.replace(pending, target)
    sync_dir(target.parent)


def services():
    result = {}
    for name in ('game', 'gateway', 'db', 'web', 'tunnel'):
        cid = subprocess.check_output(['docker', 'compose', 'ps', '-aq', name], cwd=PUBLIC.parent.parent, text=True, timeout=30).strip()
        row = json.loads(subprocess.check_output(['docker', 'inspect', cid], text=True, timeout=30))[0]
        state = row['State']
        require(state['Running'] and not state.get('OOMKilled'), 'Service unhealthy: ' + name)
        if name in ('game', 'db'):
            require(state.get('Health', {}).get('Status') == 'healthy', 'Service health: ' + name)
        result[name] = {k: row[k] for k in ('Id', 'Image', 'RestartCount')}
        result[name]['state'] = {k: state[k] for k in ('Running', 'StartedAt', 'OOMKilled')}
    return result


def publish(stage, public, snapshot=services):
    channel = (stage / 'channel.json').read_bytes()
    catalog = (stage / 'nightcap-patch-sites.json').read_bytes()
    require(sha(channel) == NEW and sha(catalog) == CATALOG, 'Candidate drift')
    current = (public / 'channel.json').read_bytes()
    require(sha(current) in (OLD, NEW), 'Public channel drift')
    # Pinned envelope was verified with the shipped Go trust before staging.
    manifest = json.loads(base64.b64decode(json.loads(channel)['manifest']))
    baseline = snapshot()
    partial = public / 'channel.json.contract-repair-partial'
    require(not partial.is_symlink(), 'Partial channel symlink')
    if partial.exists():
        require(sha(partial.read_bytes()) == NEW, 'Partial channel drift')
    excluded = {'channel.json', partial.name}
    controls = {p.name: sha(p.read_bytes()) for p in public.iterdir() if p.is_file() and p.name not in excluded}

    def unchanged():
        require(snapshot() == baseline, 'Service drift')
        require({p.name: sha(p.read_bytes()) for p in public.iterdir() if p.is_file() and p.name not in excluded} == controls, 'Public control drift')
        require(sha((public / 'channel.json').read_bytes()) in (OLD, NEW), 'Channel drift')

    # All inherited URLs stay exact; read only paths from the pinned envelope.
    for f in manifest['files']:
        if f['path'] == 'nightcap-patch-sites.json':
            require(f['sha256'] == CATALOG and f['size'] == len(catalog), 'Catalog metadata drift')
            continue
        prefix = 'https://play.nightcapgame.org/'
        require(f['url'].startswith(prefix), 'Host drift')
        path = public / f['url'][len(prefix):]
        require(path.resolve().is_relative_to(public.resolve()) and not path.is_symlink(), 'Invalid asset path')
        data = path.read_bytes()
        require(len(data) == f['size'] and sha(data) == f['sha256'], 'Retained asset drift: ' + f['path'])
    backup = stage / 'previous-channel.json'
    require(sha(backup.read_bytes()) == OLD, 'Previous signed channel missing')
    release = public / 'release/2026101901'
    require(not release.is_symlink() and not release.parent.is_symlink(), 'Release symlink')
    release.mkdir(exist_ok=True)
    sync_dir(release.parent)
    asset = release / 'nightcap-patch-sites.json'
    if asset.exists():
        require(not asset.is_symlink() and sha(asset.read_bytes()) == CATALOG, 'Immutable release drift')
    else:
        replace(catalog, asset)
    require({p.name for p in release.iterdir()} == {'nightcap-patch-sites.json'}, 'Unexpected release files')
    unchanged()
    replace(channel, public / 'channel.json')
    unchanged()
    require(sha((public / 'channel.json').read_bytes()) == NEW, 'Publication failed')
    return {'release': 2026101901, 'channel_sha256': NEW, 'changed_assets': 1,
            'preserved_assets': 137, 'services_before': baseline, 'services_after': snapshot(),
            'desktop_starter_guide_unchanged': True, 'public_controls': controls}


if __name__ == '__main__':
    import fcntl
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--publish', action='store_true', required=True)
    args = parser.parse_args()
    with (PUBLIC.parent.parent / '.deployment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = publish(args.stage.resolve(), PUBLIC)
        replace((json.dumps(result, indent=2) + '\n').encode(), args.stage / 'published.json')
        print(json.dumps(result))
