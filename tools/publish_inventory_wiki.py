"""Publish the reproduced scoped wiki delta only after the paired release opens."""
import argparse
import hashlib
import json
import subprocess
from inventory_release_support import HERE,ART,SSH,STAGE,remote,save
from prepare_inventory_wiki import PREVIOUS,RELEASE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    candidate=json.loads((HERE/'wiki-candidate.json').read_text())
    baseline=json.loads((ART/'release-baseline.json').read_text())
    signed=json.loads((ART/'signed/verification.json').read_text())
    assert candidate['public_source_reproduced'] and candidate['files']==614 and candidate['preserved_files']==609
    wiki=ART/'wiki-source/wiki';archive=ART/(RELEASE+'.tar.gz')
    paths=[archive,archive.with_suffix('.json')]+[wiki/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    upload='/home/ubuntu/wiki-inventory-combat-20261112-v1'
    if not args.resume:
        subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
        subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,paths),SSH[-1]+':'+upload+'/'],check=True,timeout=300)
    values={'PINS':pins,'UPLOAD':upload,'PREVIOUS':PREVIOUS,'RELEASE':RELEASE,
        'ARCHIVE':archive.name,'MANIFEST':archive.with_suffix('.json').name,'BASELINE':baseline['wiki_manifest'],
        'CHANNEL':signed['channel_sha256'],'CANDIDATE':candidate,'NATIVE_STAGE':STAGE,'RESUME':args.resume}
    code='\n'.join(k+'='+repr(v) for k,v in values.items())+'''\nfrom pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');upload=Path(UPLOAD)
stage=Path('/opt/nightcap/releases/wiki-inventory-combat-20261112-v1')
if RESUME:
 assert stage.is_dir() and not (stage/'publication.json').exists(),'Existing completion receipt: inspect instead of replay'
 for name,pin in PINS.items():
  p=stage/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
else:
 assert not stage.exists()
 assert {p.name for p in upload.iterdir()}==set(PINS);stage.mkdir(mode=0o700)
 for name,pin in PINS.items():
  p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
  shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
(stage/'linux-tests.log').write_text(tests.stdout+chr(10)+tests.stderr)
assert tests.returncode==0,tests.stderr[-2000:]
spec=importlib.util.spec_from_file_location('inventory_native_guard',Path(NATIVE_STAGE)/'rollout.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);prior=module.initialize()
deployed=prior.read(prior.EVIDENCE/'activation/paired-deployed.json');assert deployed['gateway_open']
services={n:prior.r.compact(n) for n in ('game','gateway','db','web','tunnel')}
config=root/'nginx.conf';config_pin=hashlib.sha256(config.read_bytes()).hexdigest();inode=config.stat().st_ino
def guard():
 assert {n:prior.r.compact(n) for n in services}==services
 assert hashlib.sha256((root/'data/public/channel.json').read_bytes()).hexdigest()==CHANNEL
 assert hashlib.sha256(config.read_bytes()).hexdigest()==config_pin and config.stat().st_ino==inode
 prior.r.running(deployed['runtime']['image_id'],prior.binaries());prior.base.health()
with (root/'.deployment.lock').open('r+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=root/'data/public/wiki/current';assert pointer.is_symlink() and str(pointer.readlink())=='releases/'+PREVIOUS
 assert json.loads((root/'website-history'/PREVIOUS/'manifest.json').read_text())==BASELINE
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/ARCHIVE),str(stage/MANIFEST),RELEASE,PREVIOUS,config_pin],timeout=300))
 guard();assert str(pointer.readlink())=='releases/'+RELEASE
result.update(linux_tests=tests.stderr.strip().splitlines()[-1],changed_existing=CANDIDATE['changed_existing'],
 preserved_files=CANDIDATE['preserved_files'],public_source_reproduced=True,native_services_preserved=True,
 channel_config_inode_preserved=True,player_visual_acceptance='OPEN',availability='Live testing')
(stage/'publication.json').write_text(json.dumps(result,indent=2)+chr(10))
print(json.dumps(result))
'''
    result=remote(code,timeout=600);save(HERE/'wiki-publication.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
