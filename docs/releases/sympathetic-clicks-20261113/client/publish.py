"""Publish the two signed Classic sympathetic assets under the paired rollout lock."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil

OLD = 'f254ffea77b2c9f60506c8cd8d89099b7a334ed63fcdf4df7b12747667b67554'
NEW = '1740eedf5ed7153fb5e2f262a147d0ffd8fb8574476963ac617912490def05ae'
RELEASE = 2026111301
PREVIOUS = 2026111202
PINS = {'dbstr_us.txt': 'c8d8cc97e88a4256090e7c41192f909f6651b79e97b4f484140f3075b426501c', 'spells_us.txt': '63067836b4b903dab1804d15bf1a1f73502ddc998a1a8ab9fdd5675b2780498b'}
PARTIAL = '.sympathetic-20261113-partial'


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


def publish(stage, public, snapshot):
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
    require(set(after) == set(before) and set(PINS) <= set(before), 'Inventory drift')
    for name, f in after.items():
        expected = dict(before[name])
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
