"""OVH-only immutable wiki release, guarded web reload and rehearsed config rollback.

Run as root with package, hash manifest, release name, config preimage hash and
wiki vhost path. Does not configure Cloudflare, restart containers or change game data.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tarfile
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = Path('/opt/nightcap/deploy/production')
HOST = 'wiki.nightcapgame.org'
PROTECTED = ['/', '/channel.json', '/launcher-channel.json', '/guide.html', '/nightcap-friends.zip']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def services():
    ids = command('docker','ps','-q','--filter','label=com.docker.compose.project=nightcap-production').splitlines()
    return sorted((v['Name'],v['Id'],v['State']['StartedAt']) for v in json.loads(command('docker','inspect',*ids)))


def probe(host, path, method='GET'):
    request = Request('http://10.88.1.4:8080'+path,headers={'Host':host},method=method)
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        digest = hashlib.sha256()
        for chunk in iter(lambda:response.read(65536),b''):
            digest.update(chunk)
        return response.status, digest.hexdigest(), dict(response.headers)


def protected():
    return {p:probe('play.nightcapgame.org',p)[:2] for p in PROTECTED}


def reload_web():
    command('docker','exec','nightcap-production-web-1','nginx','-t')
    command('docker','exec','nightcap-production-web-1','nginx','-s','reload')


def wait_for_host(expected):
    for _ in range(40):
        if probe(HOST,'/')[0] == expected:
            return
        time.sleep(0.25)
    raise RuntimeError('Web reload did not reach expected wiki state')


def verify(manifest):
    for path, expected in manifest.items():
        status,digest,headers = probe(HOST,'/'+path)
        if status != 200 or digest != expected:
            raise RuntimeError(f'Wiki bytes differ: {path} {status}')
        if headers.get('X-Content-Type-Options') != 'nosniff' or "script-src 'self'" not in headers.get('Content-Security-Policy',''):
            raise RuntimeError('Missing wiki response security policy')
    for host in [HOST,'nightcapgame.org','www.nightcapgame.org','invalid.example']:
        for path in ['/channel.json','/launcher-channel.json','/nightcap-friends.zip','/guide.html','/connect','/player-site/current/index.html','/wiki/current/index.html','/.env','/../channel.json','/missing.html']:
            expected = (400,404) if path.startswith('/../') else (404,)
            if probe(host,path)[0] not in expected:
                raise RuntimeError(f'Unexpected exposed route: {host}{path}')
    if probe(HOST,'/index.html','POST')[0] not in [403,405]:
        raise RuntimeError('Wiki accepts writes')


def unpack(archive, manifest, destination):
    if not 1 <= len(manifest) <= 10000:
        raise ValueError('Invalid manifest size')
    allowed = re.compile(r'(?:[a-z0-9-]+\.html|search-index\.json|sitemap\.xml|robots\.txt|assets/(?:wiki\.css|search\.js|moon\.svg|traders-at-dusk\.png))\Z')
    if any(not allowed.fullmatch(name) or not re.fullmatch('[a-f0-9]{64}', digest) for name,digest in manifest.items()):
        raise ValueError('Manifest contains a forbidden path or digest')
    with tarfile.open(archive,'r:gz') as tar:
        members = tar.getmembers()
        if len(members) != len(manifest) or {m.name for m in members} != set(manifest):
            raise ValueError('Archive and manifest differ')
        if any(not m.isfile() or m.size > 10_000_000 for m in members):
            raise ValueError('Archive contains a link, special file or oversized member')
        if sum(m.size for m in members) > 32_000_000:
            raise ValueError('Wiki archive exceeds the 32 MB uncompressed budget')
        # Read and validate all payload bytes before writing anything.
        contents = {m.name:tar.extractfile(m).read() for m in members}
        if any(sha(data)!=manifest[name] for name,data in contents.items()):
            raise ValueError('Archive hash mismatch')
    destination.mkdir(parents=True,exist_ok=False)
    destination.chmod(0o755)
    for name,data in contents.items():
        path = destination/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.parent.chmod(0o755)
        path.write_bytes(data)
        path.chmod(0o644)


def main(args):
    if not re.fullmatch(r'\d{8}-[a-z0-9-]+',args.release):
        raise ValueError('Invalid release name')
    config = BASE/'nginx.conf'
    before = config.read_bytes()
    if sha(before) != args.expected_config_sha:
        raise ValueError('Active web configuration changed; inspect it before retrying')
    if f'server_name {HOST};'.encode() in before:
        raise ValueError('Wiki host already installed; use the documented update procedure')
    wiki_root = BASE/'data/public/wiki'
    pointer = wiki_root/'current'
    if pointer.exists() or pointer.is_symlink():
        raise ValueError('Existing wiki pointer; this installer is for the initial activation')
    receipt = BASE/'website-history'/args.release
    receipt.mkdir(parents=True,exist_ok=False)
    (receipt/'nginx.before.conf').write_bytes(before)
    old_services,old_protected = services(),protected()
    if len(old_services) != 5 or any(status!=200 for status,digest in old_protected.values()):
        raise RuntimeError('Existing production baseline is not healthy')
    manifest = json.loads(args.manifest.read_text())
    release = wiki_root/'releases'/args.release
    unpack(args.archive,manifest,release)
    wiki_root.chmod(0o755)
    release.parent.chmod(0o755)
    candidate = before + b'\n' + args.vhost.read_bytes()
    (receipt/'nginx.after.conf').write_bytes(candidate)
    (receipt/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (receipt/'baseline.json').write_text(json.dumps({'services':old_services,'protected':old_protected},indent=2)+'\n')
    if config.read_bytes() != before:
        raise RuntimeError('Web config changed during staging; activation refused')
    try:
        pointer.symlink_to(Path('releases')/args.release)
        # Preserve the inode of the config mounted into the running web container.
        config.write_bytes(candidate)
        reload_web()
        wait_for_host(200)
        verify(manifest)
        # Rehearse the real inverse configuration before final activation.
        config.write_bytes(before)
        reload_web()
        wait_for_host(404)
        if probe(HOST,'/')[0] != 404 or protected() != old_protected:
            raise RuntimeError('Config rollback rehearsal failed')
        config.write_bytes(candidate)
        reload_web()
        wait_for_host(200)
        verify(manifest)
        if services()!=old_services or protected()!=old_protected:
            raise RuntimeError('Production service or private-download preservation failed')
    except BaseException as failure:
        recovery_errors = []
        try:
            config.write_bytes(before)
            reload_web()
        except BaseException as recovery:
            recovery_errors.append(str(recovery))
        finally:
            try:
                if pointer.is_symlink() and pointer.resolve()==release.resolve():
                    pointer.unlink()
            except BaseException as cleanup:
                recovery_errors.append(str(cleanup))
        try:
            wait_for_host(404)
            if protected()!=old_protected or services()!=old_services:
                raise RuntimeError('Recovery preservation check failed')
        except BaseException as verification:
            recovery_errors.append(str(verification))
        if recovery_errors:
            raise RuntimeError('Deployment failed; recovery requires attention: '+ '; '.join(recovery_errors)) from failure
        raise
    report = {'result':'PASS','hostname':HOST,'release':args.release,'files':len(manifest),'config_sha256':sha(candidate),'service_ids_start_times_preserved':True,'private_downloads_preserved':True,'rollback_rehearsed':True,'cloudflare_public_route':'not verified'}
    (receipt/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('release')
    parser.add_argument('expected_config_sha')
    parser.add_argument('vhost',type=Path)
    args = parser.parse_args()
    with (BASE/'website-history'/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        main(args)
