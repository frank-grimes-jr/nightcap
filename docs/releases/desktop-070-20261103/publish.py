"""Publish desktop 0.7.0 (launcher release 2026110301); never restart a service.

Two owner-gated steps under the deployment lock:
  exe     write the immutable launcher/2026110301/nightcap-desktop.exe (not yet referenced)
  switch  replace launcher-channel.json with the pinned signed envelope
Game channel, starter ZIP, guide and every other public file must stay byte-identical.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

OLD = '67a94a6d56fca08d21c0d808a2929855ec9e20bf8891ccd390f23cf1f18c3e8e'
NEW = 'abd6a3bceba70aae02b7ddf178c23832ecdd665bf6a708a47e1e7a4c82172d9b'
EXE = '4a13096be5ffba28accbb81822c1e9d6232adb38daada468c48d84f9a6302824'
EXE_SIZE = 12592640
RELEASE = 2026110301
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')
PARTIAL = '.desktop-070-partial'


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


def replace(data, target):
    pending = target.with_name(target.name + PARTIAL)
    require(not target.is_symlink() and not pending.is_symlink(), 'Symlink target')
    with pending.open('wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    pending.chmod(0o644)
    os.replace(pending, target)
    sync_dir(target.parent)


def controls(public):
    # Every top-level public file except the launcher channel must not change.
    return {p.name: sha(p.read_bytes()) for p in public.iterdir()
            if p.is_file() and p.name not in ('launcher-channel.json', 'launcher-channel.json' + PARTIAL)}


def publish(stage, public, mode):
    channel = (stage / 'launcher-channel.json').read_bytes()
    exe = (stage / 'nightcap-desktop.exe').read_bytes()
    require(sha(channel) == NEW and sha(exe) == EXE and len(exe) == EXE_SIZE, 'Candidate drift')
    signed = json.loads(__import__('base64').b64decode(json.loads(channel)['Channel'], validate=True))
    require(signed['release'] == RELEASE and signed['version'] == '0.7.0' and signed['sha256'] == EXE
            and signed['url'] == f'https://play.nightcapgame.org/launcher/{RELEASE}/nightcap-desktop.exe', 'Signed channel drift')
    live = public / 'launcher-channel.json'
    require(not live.is_symlink() and sha(live.read_bytes()) in (OLD, NEW), 'Public launcher channel drift')
    before = controls(public)
    folder = public / 'launcher' / str(RELEASE)
    target = folder / 'nightcap-desktop.exe'
    require(not folder.is_symlink() and not folder.parent.is_symlink(), 'Launcher symlink')
    if folder.exists():
        names = {p.name for p in folder.iterdir()}
        require(names <= {target.name, target.name + PARTIAL}, 'Unexpected launcher release files')
        if target.exists():
            require(sha(target.read_bytes()) == EXE, 'Immutable desktop drift')
    if mode == 'exe':
        folder.mkdir(exist_ok=True)
        folder.chmod(0o755)
        sync_dir(folder.parent)
        if not target.exists():
            replace(exe, target)
        require(sha(target.read_bytes()) == EXE and {p.name for p in folder.iterdir()} == {target.name}, 'Desktop write failed')
    else:
        require(target.exists() and sha(target.read_bytes()) == EXE, 'Upload the desktop before switching')
        replace(channel, live)
        require(sha(live.read_bytes()) == NEW, 'Switch failed')
    require(controls(public) == before, 'Public control drift')
    return {'mode': mode, 'release': RELEASE, 'desktop_sha256': EXE,
            'launcher_channel_sha256': sha(live.read_bytes()), 'public_controls': before}


if __name__ == '__main__':
    import fcntl
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--mode', choices=('exe', 'switch'), required=True)
    args = parser.parse_args()
    with (PUBLIC.parent.parent / '.deployment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(json.dumps(publish(args.stage.resolve(), PUBLIC, args.mode)))
