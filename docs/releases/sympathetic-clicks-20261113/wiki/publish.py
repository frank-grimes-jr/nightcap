"""Publish this four-file content delta using the existing guarded wiki updater."""
import json
import subprocess
import sys

from prepare import ART, HERE, PARENT, PARENT_SOURCE, PREVIOUS, RELEASE, ROOT, save, sha

sys.path.insert(0, str(ROOT / 'docs/releases/classic-raid-augments-20261112'))
from probe import SSH, remote


REMOTE = '''
import fcntl, hashlib, importlib.util, json, os, shutil, subprocess
from pathlib import Path
os.umask(0o077)
root = Path('/opt/nightcap/deploy/production')
release = Path('/opt/nightcap/releases/sympathetic-clicks-20261113-v1')
deployment = release/'evidence/activation/deployed.json'
live = json.loads(deployment.read_bytes())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def game_gate():
    current = json.loads(deployment.read_bytes())
    assert current == live and live['gateway_open'] and str(live['client_release']) == '2026111301'
    assert sha(root/'data/public/channel.json') == live['client_channel_sha256']
    game = json.loads(subprocess.check_output(['docker','inspect','nightcap-production-game-1']))[0]
    gateway = json.loads(subprocess.check_output(['docker','inspect','nightcap-production-gateway-1']))[0]
    assert game['State']['Running'] and game['State']['Health']['Status'] == 'healthy'
    assert game['Image'] == live['image'] and gateway['State']['Running']
def base_gate():
    assert (root/'data/public/wiki/current').readlink() == Path('releases')/PREVIOUS
    assert json.loads((root/'website-history'/PREVIOUS/'manifest.json').read_bytes()) == BASE
    assert sha(root/'nginx.conf') == CONFIG
'''

ACTIVATE = '''
destination = Path('/opt/nightcap/releases')/('wiki-'+RELEASE)
upload = Path(UPLOAD)
with (root/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    game_gate()
    base_gate()
    assert set(p.name for p in upload.iterdir()) == set(PINS)
    destination.mkdir(mode=0o700, exist_ok=True)
    assert not destination.is_symlink() and not (destination/'publication.json').exists()
    for name, expected in PINS.items():
        source = upload/name
        assert source.is_file() and not source.is_symlink() and sha(source) == expected
        target = destination/name
        if not target.exists():
            with target.open('xb') as result, source.open('rb') as original:
                shutil.copyfileobj(original, result)
        assert not target.is_symlink() and sha(target) == expected
    tests = subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],
                           cwd=destination, capture_output=True, text=True, timeout=180)
    assert tests.returncode == 0, tests.stderr[-1600:]
    loader = importlib.util.spec_from_file_location('deploy',destination/'deploy.py')
    deploy = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(deploy)
    services = deploy.services()
    assert len(services) == 5
    config = root/'nginx.conf'
    inode = config.stat().st_ino
    before_channel = sha(root/'data/public/channel.json')
    raw = subprocess.check_output(['python3',str(destination/'update.py'),str(destination/(RELEASE+'.tar.gz')),
                                  str(destination/(RELEASE+'.tar.json')),RELEASE,PREVIOUS,CONFIG],timeout=720)
    result = json.loads(raw)
    assert result['result'] == 'PASS' and result['files'] == 631 and result['rollback_rehearsed']
    assert (root/'data/public/wiki/current').readlink() == Path('releases')/RELEASE
    assert deploy.services() == services and config.stat().st_ino == inode and sha(config) == CONFIG
    game_gate()
    result.update(source=live['source'], image=live['image'], client_release=live['client_release'],
                  client_channel_sha256=before_channel, game_deployment_receipt_sha256=sha(deployment),
                  configuration_inode_preserved=True, canonical_https_verification='separate public-verification.json',
                  linux_publisher_tests=tests.stderr.strip().splitlines()[-3:])
    (destination/'publication.json').write_text(json.dumps(result,indent=2)+chr(10))
    print(json.dumps(result))
'''


def main():
    candidate = json.loads((HERE/'candidate.json').read_bytes())
    assert sha(ART/(RELEASE+'.tar.gz')) == candidate['package_sha256']
    assert sha(ART/(RELEASE+'.tar.json')) == candidate['manifest_sha256']
    assert sha(PARENT/(PREVIOUS+'.tar.json')) == candidate['previous_manifest_sha256']
    previous_receipt = json.loads((PARENT_SOURCE/'docs/releases/wiki-simple-ste-20261113/publication.json').read_bytes())
    assert previous_receipt['release'] == PREVIOUS and previous_receipt['result'] == 'PASS'
    config = previous_receipt['config_sha256']
    expected = json.loads((PARENT/(PREVIOUS+'.tar.json')).read_bytes())
    paths = [ART/(RELEASE+'.tar.gz'), ART/(RELEASE+'.tar.json')]
    paths.extend(ART/'wiki-source/wiki'/name for name in ('deploy.py','update.py','test_deploy.py','test_update.py','nginx.conf'))
    upload = '/home/ubuntu/wiki-' + RELEASE
    values = dict(RELEASE=RELEASE, PREVIOUS=PREVIOUS, BASE=expected, CONFIG=config,
                  UPLOAD=upload, PINS={p.name:sha(p) for p in paths})
    prefix = '\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+REMOTE
    remote(prefix+'\ngame_gate()\nbase_gate()')
    # Files are staged in the operator's private directory. The immutable release
    # destination and symlink are owned by the guarded deployment on the host.
    ssh = SSH[:-1]
    subprocess.run(ssh + ['mkdir -p -m 700 '+upload], check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,paths),ssh[-1]+':'+upload+'/'], check=True, timeout=300)
    result = json.loads(remote(prefix + ACTIVATE, timeout=1000))
    save(HERE/'publication.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
