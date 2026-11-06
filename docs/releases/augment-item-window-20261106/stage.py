"""Stage only the authorized augment native/content payload. Does not change services."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'augment-audit-20261106'))
from probe import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STAGE='/opt/nightcap/releases/augment-item-window-20261106-v1'
UPLOAD='/home/ubuntu/augment-item-window-20261106-v1.tar.gz'


def main(zone,archive,revision):
    payload={'bin/zone':Path(zone).read_bytes(),'rollout.py':(HERE/'rollout.py').read_bytes()}
    assert hashlib.sha256(payload['bin/zone']).hexdigest()=='3fc2b901c98dfc2816298a051f3462a6db0a724ccfa649ff213da3d840186588'
    pins={n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}
    with tarfile.open(archive,'x:gz') as tar:
        for name,data in payload.items():
            entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o755 if name=='bin/zone' else 0o600
            tar.addfile(entry,io.BytesIO(data))
    digest=hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    code=f'''import fcntl,hashlib,json,os,tarfile
from pathlib import Path
root=Path('/opt/nightcap/deploy/production');stage=Path({STAGE!r});upload=Path({UPLOAD!r});pins={pins!r}
prior=Path('/opt/nightcap/releases/augment-audit-20261106-v1');os.umask(0o077)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not stage.exists(),'Inspect existing release before reuse'
 assert hashlib.sha256(upload.read_bytes()).hexdigest()=={digest!r}
 deployed=json.loads((prior/'evidence/activation/deployed.json').read_text());pm=json.loads((prior/'manifest.json').read_text())
 stage.mkdir(mode=0o700)
 with tarfile.open(upload,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==len(pins) and {{x.name for x in members}}==set(pins)
  for member in members:
   assert member.isfile();path=stage/member.name;assert path.resolve().is_relative_to(stage)
   data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==pins[member.name]
   path.parent.mkdir(parents=True,exist_ok=True)
   with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
   path.chmod(0o755 if member.name=='bin/zone' else 0o600)
 manifest={{'release':'augment-item-window-20261106-v1','source_revision':{revision!r},'base_image_id':deployed['runtime']['image_id'],
   'base_hashes':{{**pm['base_hashes'],'bin/zone':pm['files']['bin/zone']}},'prior_rollout_sha256':hashlib.sha256((prior/'rollout.py').read_bytes()).hexdigest(),
   'zone_sha256':pins['bin/zone'],'files':pins,'owner_deploy_authorized':'2026-11-06 chat: Merge the augment changes to main and deploy to OVH for live QA','owner_gameplay_accepted':False}}
 with (stage/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno())
 upload.unlink();print(json.dumps({{'stage':str(stage),'base_image':manifest['base_image_id'],'payload_files':len(pins),'zone_sha256':pins['bin/zone']}}))
'''
    subprocess.run(SSH+['test ! -e '+UPLOAD],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(archive),SSH[-1]+':'+UPLOAD],check=True,timeout=600)
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=120)
    if p.returncode:raise RuntimeError(p.stderr[-2200:])
    (HERE/'staged.json').write_text(p.stdout)
    print(p.stdout)


if __name__=='__main__':main(*sys.argv[1:4])
