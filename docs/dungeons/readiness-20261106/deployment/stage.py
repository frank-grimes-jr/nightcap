"""Stage an authenticated main Keeper build; does not change game services."""
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from probe import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
STAGE='/opt/nightcap/releases/dungeon-readiness-20261106-v1'
UPLOAD='/home/ubuntu/dungeon-readiness-20261106-v1.tar.gz'


def main(revision):
    assert re.fullmatch('[0-9a-f]{40}',revision)
    proof=json.loads((HERE.parent/'native-build-current.json').read_text())
    contract=(ROOT/'docs/dungeons/runtime-contract.json').read_bytes()
    proof['runtime_contract_sha256']=hashlib.sha256(contract).hexdigest()
    payload={'bin/zone':(HERE.parent/'bin/zone').read_bytes(),'rollout.py':(HERE/'rollout.py').read_bytes(),
             'runtime-contract.json':contract,'native-build.json':(json.dumps(proof,indent=2)+'\n').encode(),
             'world_count.py':(HERE/'world_count.py').read_bytes()}
    assert hashlib.sha256(payload['bin/zone']).hexdigest()==proof['candidate_shipping_sha256']
    assert proof['retained_baseline_shipping_sha256']=='ea6ad5324fbfd976210d060ad3efd29616c9da53a73f36f5d4fd7cfbd8743d6a'
    pins={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}
    archive=HERE.parent/'bin/dungeon-readiness-20261106-v1.tar.gz'
    with tarfile.open(archive,'x:gz') as tar:
        for name,data in payload.items():
            entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o755 if name=='bin/zone' else 0o600
            tar.addfile(entry,io.BytesIO(data))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    code=f'''import fcntl,hashlib,json,os,tarfile
from pathlib import Path
root=Path('/opt/nightcap/deploy/production');stage=Path({STAGE!r});upload=Path({UPLOAD!r});pins={pins!r}
prior=Path('/opt/nightcap/releases/character-stats-window-20261106-v1');os.umask(0o077)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not stage.exists(),'Inspect existing release before reuse'
 assert hashlib.sha256(upload.read_bytes()).hexdigest()=={digest!r}
 deployed=json.loads((prior/'evidence/activation/deployed.json').read_text());pm=json.loads((prior/'manifest.json').read_text())
 assert deployed['gateway_open'] and pm['zone_sha256']=='ea6ad5324fbfd976210d060ad3efd29616c9da53a73f36f5d4fd7cfbd8743d6a'
 stage.mkdir(mode=0o700)
 with tarfile.open(upload,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==len(pins) and {{x.name for x in members}}==set(pins)
  for member in members:
   assert member.isfile();path=stage/member.name;assert path.resolve().is_relative_to(stage)
   data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==pins[member.name]
   path.parent.mkdir(parents=True,exist_ok=True)
   with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
   path.chmod(0o755 if member.name=='bin/zone' else 0o600)
 manifest={{'release':'dungeon-readiness-20261106-v1','source_revision':{revision!r},'base_image_id':deployed['runtime']['image_id'],
   'base_hashes':{{**pm['base_hashes'],'bin/zone':pm['zone_sha256']}},'prior_rollout_sha256':hashlib.sha256((prior/'rollout.py').read_bytes()).hexdigest(),
   'zone_sha256':pins['bin/zone'],'files':pins,'owner_deploy_authorized':'2026-11-06 chat: Yes, merge to main and deploy to OVH for live QA.','owner_gameplay_accepted':False}}
 with (stage/'manifest.json').open('x') as stream:json.dump(manifest,stream,indent=2);stream.write('\\n');stream.flush();os.fsync(stream.fileno())
 upload.unlink();print(json.dumps({{'stage':str(stage),'base_image':manifest['base_image_id'],'payload_files':len(pins),'zone_sha256':pins['bin/zone'],'source_revision':{revision!r}}}))
'''
    subprocess.run(SSH+['test ! -e '+UPLOAD],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(archive),SSH[-1]+':'+UPLOAD],check=True,timeout=600)
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr[-2500:])
    (HERE/'staged.json').write_text(result.stdout)
    print(result.stdout)


if __name__=='__main__':main(sys.argv[1])
