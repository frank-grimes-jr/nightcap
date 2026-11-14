"""Publish the combat guides after the paired native game release has opened."""
import json
from pathlib import Path
import subprocess
import sys
from prepare import ART, BASE, HERE, PREVIOUS, RELEASE, ROOT, save, sha

sys.path.insert(0, str(HERE.parent / 'ops'))
from probe import SSH, STAGE, remote

def main():
    candidate = json.loads((HERE / 'candidate.json').read_bytes())
    game = json.loads((HERE.parent / 'ops/production-verified.json').read_bytes())
    assert game['result'] == 'PASS' and game['gateway_open'] and game['workers'] == 12 and game['restarts'] == 0
    prior = json.loads((ROOT / 'docs/releases/sympathetic-clicks-20261113/wiki/publication.json').read_bytes())
    assert prior['result'] == 'PASS' and prior['release'] == PREVIOUS
    paths = [ART / (RELEASE + '.tar.gz'), ART / (RELEASE + '.tar.json')]
    assert [sha(p) for p in paths] == [candidate['package_sha256'], candidate['manifest_sha256']]
    before = BASE / (PREVIOUS + '.tar.json')
    assert sha(before) == candidate['previous_manifest_sha256']
    paths.extend(BASE / 'wiki-source/wiki' / name for name in ('deploy.py','update.py','test_deploy.py','test_update.py','nginx.conf'))
    upload = '/home/ubuntu/wiki-' + RELEASE
    values = dict(RELEASE=RELEASE, PREVIOUS=PREVIOUS, EXPECTED=json.loads(before.read_bytes()),
                  CONFIG=prior['config_sha256'], GAME=STAGE, RECEIPT=game['deployed_receipt'], UPLOAD=upload,
                  PINS={p.name:sha(p) for p in paths})
    script = '\n'.join(key+'='+repr(value) for key,value in values.items())+'\n'+GATES
    remote(script+'\ncheck_game()\ncheck_before()')
    ssh = SSH[:-1]
    subprocess.run(ssh+['mkdir -p -m 700 '+upload],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,paths),ssh[-1]+':'+upload+'/'],check=True,timeout=300)
    result = json.loads(remote(script+PUBLISH,timeout=1000))
    save(HERE / 'publication.json',result)
    print(result)

GATES = """
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production')
release=Path('/opt/nightcap/releases')/GAME
receipt=release/'evidence/activation/deployed.json'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def check_game():
    assert sha(receipt)==RECEIPT
    game=json.loads(receipt.read_bytes())
    assert game['gateway_open'] and sha(root/'data/public/channel.json')==game['client_channel_sha256']
    info=json.loads(subprocess.check_output(['docker','inspect','nightcap-production-game-1','nightcap-production-gateway-1']))
    assert info[0]['Image']==game['image'] and info[0]['State']['Health']['Status']=='healthy'
    assert all(r['State']['Running'] for r in info)
    return game
def check_before():
    assert (root/'data/public/wiki/current').readlink()==Path('releases')/PREVIOUS
    assert json.loads((root/'website-history'/PREVIOUS/'manifest.json').read_bytes())==EXPECTED
    assert sha(root/'nginx.conf')==CONFIG
"""

PUBLISH = """
with (root/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    game=check_game()
    check_before()
    upload=Path(UPLOAD)
    assert set(PINS)=={f.name for f in upload.iterdir()}
    destination=Path('/opt/nightcap/releases')/('wiki-'+RELEASE)
    destination.mkdir(mode=0o700,exist_ok=True)
    assert not destination.is_symlink() and not (destination/'publication.json').exists()
    for name,pin in PINS.items():
        source=upload/name
        assert source.is_file() and not source.is_symlink() and sha(source)==pin
        target=destination/name
        if not target.exists():
            with target.open('xb') as output,source.open('rb') as input_file:
                shutil.copyfileobj(input_file,output)
        assert target.is_file() and not target.is_symlink() and sha(target)==pin
    tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=destination,capture_output=True,text=True,timeout=180)
    assert tests.returncode==0,tests.stderr[-1800:]
    loader=importlib.util.spec_from_file_location('release_deploy',destination/'deploy.py')
    deploy=importlib.util.module_from_spec(loader)
    loader.loader.exec_module(deploy)
    services=deploy.services()
    inode=(root/'nginx.conf').stat().st_ino
    result=json.loads(subprocess.check_output(['python3',str(destination/'update.py'),str(destination/(RELEASE+'.tar.gz')),
                        str(destination/(RELEASE+'.tar.json')),RELEASE,PREVIOUS,CONFIG],timeout=720))
    assert result['result']=='PASS' and result['rollback_rehearsed'] and result['files']==len(EXPECTED)
    assert (root/'data/public/wiki/current').readlink()==Path('releases')/RELEASE
    assert (root/'nginx.conf').stat().st_ino==inode and sha(root/'nginx.conf')==CONFIG
    assert deploy.services()==services and check_game()==game
    result.update(source=game['source'],game_image=game['image'],game_receipt_sha256=RECEIPT,
                  client_release=game['client_release'],client_channel_sha256=game['client_channel_sha256'],
                  config_inode_preserved=True,linux_publisher_tests=tests.stderr.strip().splitlines()[-3:])
    (destination/'publication.json').write_text(json.dumps(result,indent=2)+chr(10))
    print(json.dumps(result))
"""

if __name__ == '__main__':
    main()
