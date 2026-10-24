"""Stage the verified zone candidate and run preflight only; never activate."""
import hashlib,io,json,os,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ART=Path('E:/EQ_Local_Dev/artifacts/rogue-tome-release-20261024')
STAGE='/opt/nightcap/releases/rogue-tomes-20261024'
UPLOAD='/home/ubuntu/rogue-tomes-20261024.tar.gz'
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',os.environ['NIGHTCAP_DEPLOY_SSH_TARGET']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def remote(code):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code.encode(),capture_output=True,timeout=900)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-6000:])
    return json.loads(p.stdout)

def main():
    build=json.loads((HERE/'native-build-manifest.json').read_text())
    assert build['baseline_reproduced'] and build['status']=='complete zone build passed; not installed'
    base=json.loads((HERE/'production-before.json').read_text())
    assert build['baseline_zone_sha256']==base['base_hashes']['bin/zone']
    ART.mkdir(exist_ok=True);binary=ART/'zone'
    assert not binary.exists(),'Inspect existing packaging result'
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-rogue-tomes-20261024-v1/build/bin/zone',str(binary)],check=True)
    assert sha(binary)==build['zone_sha256']
    m={k:base[k] for k in ('base_image_id','base_hashes','helpers','client_channel_sha256','contract')}
    m.update(zone_sha256=sha(binary),files={'bin/zone':sha(binary),'rollout.py':sha(HERE/'rollout.py')})
    (HERE/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    package=ART/'rogue-tomes-20261024.tar.gz'
    with tarfile.open(package,'x:gz') as tar:
        for name,p in [('bin/zone',binary),('rollout.py',HERE/'rollout.py'),('manifest.json',HERE/'manifest.json')]:
            data=p.read_bytes();entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o755 if name=='bin/zone' else 0o600;tar.addfile(entry,io.BytesIO(data))
    guard=remote(f"""from pathlib import Path
import json
assert not Path({STAGE!r}).exists() and not Path({UPLOAD!r}).exists(),'Existing staging attempt; inspect'
print(json.dumps({{'ready':True}}))
""")
    assert guard['ready']
    subprocess.run(['scp',*SSH[1:-1],str(package),SSH[-1]+':'+UPLOAD],check=True,timeout=180)
    result=remote(f"""from pathlib import Path
import hashlib,json,tarfile,subprocess,shutil
upload=Path({UPLOAD!r});stage=Path({STAGE!r})
assert hashlib.sha256(upload.read_bytes()).hexdigest()=={sha(package)!r}
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
with tarfile.open(upload,'r:gz') as tar:
 members=tar.getmembers();assert {{m.name for m in members}}=={{'bin/zone','rollout.py','manifest.json'}} and len(members)==3
 for member in members:
  assert member.isfile()
  dest=stage/member.name;assert dest.resolve().is_relative_to(stage)
  dest.parent.mkdir(mode=0o700,exist_ok=True);dest.write_bytes(tar.extractfile(member).read());dest.chmod(member.mode)
manifest=json.loads((stage/'manifest.json').read_text())
for n,h in manifest['files'].items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()=={sha(HERE/'manifest.json')!r}
# This exact task upload has a verified local package and verified extracted copy.
assert upload.resolve()==Path({UPLOAD!r});upload.unlink()
with (stage/'preflight.log').open('x') as log:r=subprocess.run(['python3',str(stage/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
if r.returncode:raise RuntimeError((stage/'preflight.log').read_text()[-5000:])
p=json.loads((stage/'evidence/preflight.json').read_text())
print(json.dumps({{'result':'PASS','stage':str(stage),'image':p['image'],'checks':p['checks'],'manifest_sha256':p['manifest_sha256'],'free_bytes':shutil.disk_usage(stage).free,'production_activated':False}}))
""")
    (HERE/'preflight-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
