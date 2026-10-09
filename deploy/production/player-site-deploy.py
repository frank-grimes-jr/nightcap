"""Run as root on OVH. Stage or activate only a validated five-file website.

stage PACKAGE MANIFEST RELEASE EXPECTED_NGINX_SHA CONFIG
activate RELEASE
rollback RELEASE
Stage includes a real origin rehearsal and pointer rollback before publication.
Private receipts/preimages stay outside the public mount. No game/db restarts.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request

BASE = Path('/opt/nightcap/deploy/production')
SITES = BASE / 'data/public/player-site'
HISTORY = BASE / 'website-history'
FILES = {'index.html', 'site-assets/site.css', 'site-assets/moon.svg',
         'site-assets/traders-at-dusk.png', 'site-assets/master-of-three.png'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compose(*args):
    return subprocess.check_output(['docker', 'compose', *args], cwd=BASE, text=True).strip()


def containers():
    ids = compose('ps', '-q').splitlines()
    rows = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True))
    return {r['Config']['Labels']['com.docker.compose.service']:
            [r['Id'], r['State']['StartedAt']] for r in rows}


def pointer(target):
    temporary = SITES / '.next'
    if temporary.is_symlink():
        temporary.unlink()
    temporary.symlink_to(target)
    os.replace(temporary, SITES / 'current')


def current_pointer():
    current = SITES / 'current'
    if current.is_symlink():
        return os.readlink(current)
    assert not current.exists(), 'Unmanaged current directory'
    return None


def check_activation_preconditions(receipt, directory):
    assert current_pointer() == receipt['previous'], 'Website pointer changed since staging'
    assert (BASE/'nginx.conf').read_bytes() == (directory/'nginx.before').read_bytes()
    assert containers() == receipt['containers'], 'Services changed since staging'
    for name, digest in receipt['protected'].items():
        assert sha((BASE/'data/public'/name).read_bytes()) == digest, 'Protected file changed since staging'
    for name, digest in receipt['files'].items():
        assert sha((SITES/receipt['target']/name).read_bytes()) == digest, 'Staged file changed'


def probe(host, path, expected=200, digest=None, private=False):
    req = urllib.request.Request('http://10.88.1.4:8080' + path, headers={'Host': host})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status, data = response.status, response.read()
            if expected == 200:
                assert "default-src 'none'" in response.headers['Content-Security-Policy']
                if private:
                    directives = {v.strip().lower() for v in response.headers.get('Cache-Control', '').split(',')}
                    assert {'private', 'no-store', 'no-transform'} <= directives, 'Website cache privacy missing'
                    assert 'public' not in directives, 'Shared website caching enabled'
    except urllib.error.HTTPError as error:
        status, data = error.code, error.read()
    assert status == expected, (host, path, status, expected)
    if digest:
        assert sha(data) == digest, (host, path, 'hash mismatch')


def verify_routes(receipt):
    for name, digest in receipt['files'].items():
        route = '/' if name == 'index.html' else '/' + name
        probe('play.nightcapgame.org', route, digest=digest, private=True)
    for path in ('/player-site', '/player-site/current/index.html',
                 '/player-site/current/site-assets/site.css',
                 f"/player-site/{receipt['target']}/index.html",
                 f"/player-site/{receipt['target']}/site-assets/site.css"):
        probe('play.nightcapgame.org', path, 404)
    for host in ('nightcapgame.org', 'www.nightcapgame.org', 'unknown.invalid'):
        for path in ('/', '/index.html', '/site-assets/site.css', '/channel.json',
                     '/launcher-channel.json', '/guide.html', '/nightcap-friends.zip',
                     '/connect', '/.env', '/release/', '/website-history/'):
            probe(host, path, 404)


def restore(receipt, directory):
    current = SITES / 'current'
    if receipt['previous'] is None:
        if current.is_symlink():
            current.unlink()
    else:
        pointer(receipt['previous'])
    # The running container bind-mounts this inode: write in place, then validate.
    (BASE / 'nginx.conf').write_bytes((directory / 'nginx.before').read_bytes())
    compose('exec', '-T', 'web', 'nginx', '-t')
    compose('exec', '-T', 'web', 'nginx', '-s', 'reload')


def activate(receipt, directory):
    target = receipt['target']
    pointer(target)
    (BASE / 'nginx.conf').write_bytes((directory / 'nginx.after').read_bytes())
    compose('exec', '-T', 'web', 'nginx', '-t')
    compose('exec', '-T', 'web', 'nginx', '-s', 'reload')
    # A bounded retry permits the graceful worker generation to finish switching.
    import time
    for attempt in range(10):
        try:
            verify_routes(receipt)
            break
        except (AssertionError, OSError):
            if attempt == 9:
                raise
            time.sleep(.2)
    for name, digest in receipt['protected'].items():
        probe('play.nightcapgame.org', '/' + name, digest=digest)
    assert containers() == receipt['containers'], 'Service identity/start time changed'


def main():
    action = sys.argv[1]
    release = sys.argv[4] if action == 'stage' else sys.argv[2]
    if not re.fullmatch(r'[0-9]{8}-[a-z0-9-]+', release):
        raise ValueError('Invalid release name')
    directory = HISTORY / release
    if action == 'stage':
        _, _, package, manifest, _, expected, config = sys.argv
        before = (BASE / 'nginx.conf').read_bytes()
        assert sha(before) == expected, 'Unexpected live configuration drift'
        assert not directory.exists(), 'Release receipt already exists'
        manifest = json.loads(Path(manifest).read_text())
        assert set(manifest) == FILES
        target = SITES / release
        assert not target.exists()
        with tarfile.open(package) as archive:
            members = archive.getmembers()
            assert len(members) == len(FILES) and {m.name for m in members} == FILES
            for member in members:
                assert member.isfile() and member.size <= 6_000_000
                assert sha(archive.extractfile(member).read()) == manifest[member.name]
            # Public payload directories must be traversable by Nginx even when
            # the release wrapper uses umask 077 for private evidence/backups.
            SITES.mkdir(parents=True, exist_ok=True)
            SITES.chmod(0o755)
            target.mkdir()
            target.chmod(0o755)
            for member in members:
                output = target / member.name
                output.parent.mkdir(exist_ok=True)
                output.parent.chmod(0o755)
                output.write_bytes(archive.extractfile(member).read())
                output.chmod(0o644)
        previous = current_pointer()
        directory.mkdir(parents=True, mode=0o700)
        directory.chmod(0o700)
        receipt = {'target': release, 'previous': previous,
                   'files': manifest, 'containers': containers(),
                   'protected': {name: sha((BASE/'data/public'/name).read_bytes()) for name in
                                 ('channel.json','launcher-channel.json','guide.html','nightcap-friends.zip')}}
        (directory/'receipt.json').write_text(json.dumps(receipt, indent=2))
        (directory/'nginx.before').write_bytes(before)
        (directory/'nginx.after').write_bytes(Path(config).read_bytes())
        check_activation_preconditions(receipt, directory)
        try:
            activate(receipt, directory)
        finally:
            restore(receipt, directory)
        assert (BASE/'nginx.conf').read_bytes() == before
        assert current_pointer() == previous
        assert containers() == receipt['containers']
        print(json.dumps({'result':'STAGED_AND_ROLLBACK_REHEARSED','release':release}))
    else:
        receipt = json.loads((directory/'receipt.json').read_text())
        if action == 'activate':
            check_activation_preconditions(receipt, directory)
            try:
                activate(receipt, directory)
            except BaseException:
                restore(receipt, directory)
                raise
            print(json.dumps({'result':'ORIGIN_VERIFIED','release':release,'files':len(receipt['files'])}))
        elif action == 'rollback':
            assert (SITES/'current').is_symlink() and os.readlink(SITES/'current') == release
            assert (BASE/'nginx.conf').read_bytes() == (directory/'nginx.after').read_bytes()
            restore(receipt, directory)
            print(json.dumps({'result':'ROLLED_BACK','release':release}))
        else:
            raise ValueError('Unknown action')


if __name__ == '__main__':
    import fcntl
    HISTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (HISTORY/'.lock').open('a') as lock:
        os.chmod(HISTORY/'.lock', 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main()
