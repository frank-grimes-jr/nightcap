"""Publish the approved three-file advanced-loot delta; never restart a service.

The locally verified signed envelope and archive bytes are pinned. All inherited
URLs are kept and checked before publication. Run under the deployment lock.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil

OLD = 'e0201dd35be1501208c6783eeb3c6194e2d7b9ec080f70ef4f09f52d744dacd5'
NEW = 'f254ffea77b2c9f60506c8cd8d89099b7a334ed63fcdf4df7b12747667b67554'
RELEASE = 2026111202
PREVIOUS = 2026111201
PINS = {'dinput8.dll': 'df16b336eb0a8f744e588bcbc092125d0090fd18b50aa269c38017901a029d2d', 'nightcap-patch-sites.json': 'f2a3e4c735e830dd97b261b7b8aa173d4ecaffa01b515bc89167b2c0da68a0f9', 'uifiles/nightcap/equi_inventory.xml': '545e9692f01bde1071bab4c927a66b13a6a9b2c07b638ad48e2c2cbd8bff5ab2'}
ADDED = set()
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')
PARTIAL = '.inventory-combat-stats-20261112-partial'


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
    pending = target.with_name(target.name + PARTIAL)
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
        require(state['Running'] and not state.get('OOMKilled'), 'Service must remain running: ' + name)
        if name in ('game', 'db'):
            require(state.get('Health', {}).get('Status') == 'healthy', 'Service health: ' + name)
        result[name] = {k: row[k] for k in ('Id', 'Image', 'RestartCount')}
        result[name]['state'] = {k: state[k] for k in ('Running', 'StartedAt', 'OOMKilled')}
    return result


def publish(stage, public, snapshot=services):
    channel = (stage / 'channel.json').read_bytes()
    previous = (stage / 'previous-channel.json').read_bytes()
    assets = {name: (stage / name).read_bytes() for name in PINS}
    require(sha(channel) == NEW and sha(previous) == OLD, 'Candidate or baseline drift')
    require(all(sha(data) == PINS[name] for name, data in assets.items()), 'Candidate archive drift')
    require(not (public / 'channel.json').is_symlink(), 'Channel symlink')
    require(sha((public / 'channel.json').read_bytes()) in (OLD, NEW), 'Public channel drift')
    # These exact envelopes were signature-checked with the shipped Go policy.
    decode = lambda raw: json.loads(base64.b64decode(json.loads(raw)['manifest'], validate=True))
    manifest, old = decode(channel), decode(previous)
    require(old['release'] == PREVIOUS and manifest['release'] == RELEASE, 'Release drift')
    before = {f['path']: f for f in old['files']}
    after = {f['path']: f for f in manifest['files']}
    require(len(before) == len(old['files']) and len(after) == len(manifest['files']), 'Duplicate inventory')
    require(set(after) == set(before) | ADDED and not (set(before) & ADDED) and set(PINS) <= set(after), 'Inventory drift')
    for name, f in after.items():
        expected = dict(before[name]) if name in before else {'path':name, 'required':True}
        if name in PINS:
            expected.update(sha256=PINS[name], size=len(assets[name]), url=f'https://play.nightcapgame.org/release/{RELEASE}/{name}')
        require(f == expected, 'Descriptor drift: ' + name)
    retained = dict(manifest)
    for key in ('release', 'expires', 'files', 'patch_notes'):
        retained[key] = old[key]
    require(retained == old and manifest['patch_notes'][1:] == old['patch_notes'], 'Policy/history drift')
    baseline = snapshot()
    partial = public / ('channel.json' + PARTIAL)
    require(not partial.is_symlink(), 'Partial channel symlink')
    if partial.exists():
        require(channel.startswith(partial.read_bytes()), 'Partial channel drift')
    excluded = {'channel.json', partial.name}
    controls = lambda: {p.name: sha(p.read_bytes()) for p in public.iterdir() if p.is_file() and p.name not in excluded}
    control_hashes = controls()

    def unchanged():
        require(snapshot() == baseline, 'Service drift')
        require(controls() == control_hashes, 'Public control drift')
        require(sha((public / 'channel.json').read_bytes()) in (OLD, NEW), 'Channel drift')

    for name, f in after.items():
        if name in PINS:
            continue
        prefix = 'https://play.nightcapgame.org/'
        require(f['url'].startswith(prefix), 'Host drift')
        path = public / f['url'][len(prefix):]
        require(path.resolve().is_relative_to(public.resolve()) and not path.is_symlink(), 'Invalid asset path')
        data = path.read_bytes()
        require(len(data) == f['size'] and sha(data) == f['sha256'], 'Retained asset drift: ' + name)
    release = public / 'release' / str(RELEASE)
    require(not release.is_symlink() and not release.parent.is_symlink(), 'Release symlink')
    allowed = set(PINS) | {name + PARTIAL for name in PINS}
    directories = {str(parent).replace('\\','/') for name in PINS for parent in Path(name).parents if str(parent) != '.'}
    def inventory():
        found=set()
        if release.exists():
            for path in release.rglob('*'):
                name=path.relative_to(release).as_posix()
                require(not path.is_symlink(), 'Release file symlink')
                if path.is_dir():
                    require(name in directories, 'Unexpected release directory')
                    continue
                require(path.is_file() and name in allowed, 'Unexpected release files')
                found.add(name)
                if name in PINS:
                    require(sha(path.read_bytes()) == PINS[name], 'Immutable release drift')
                else:
                    require(assets[name.removesuffix(PARTIAL)].startswith(path.read_bytes()), 'Partial archive drift')
        return found
    inventory()
    unchanged()
    require(shutil.disk_usage(public).free >= sum(map(len, assets.values())) + 350*1024**2, 'Publication disk reserve')
    release.mkdir(exist_ok=True)
    release.chmod(0o755)
    sync_dir(release.parent)
    for name in sorted(directories, key=lambda name: (name.count('/'),name)):
        directory=release/name
        directory.mkdir(exist_ok=True)
        directory.chmod(0o755)
        sync_dir(directory.parent)
    for name, data in assets.items():
        path = release / name
        if not path.exists():
            replace(data, path)
        path.chmod(0o644)
        with path.open('rb') as handle:os.fsync(handle.fileno())
        sync_dir(path.parent)
    require(inventory() == set(PINS), 'Unexpected release files')
    unchanged()
    replace(channel, public / 'channel.json')
    unchanged()
    require(sha((public / 'channel.json').read_bytes()) == NEW, 'Publication failed')
    return {'release': RELEASE, 'channel_sha256': NEW, 'changed_assets': len(PINS),
            'preserved_assets': len(after) - len(PINS), 'services_before': baseline,
            'services_after': snapshot(), 'desktop_starter_guide_unchanged': True,
            'public_controls': control_hashes}


if __name__ == '__main__':
    raise SystemExit('Paired release: use rollout.py publish-client behind the verified closed gateway')
