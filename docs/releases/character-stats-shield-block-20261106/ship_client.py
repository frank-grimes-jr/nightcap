"""Stage/publish exact signed Stats font XML; never upload signing material."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from stage import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SIGNED=ROOT/'artifacts/character-stats-shield-block/signed'
STAGE='/opt/nightcap/releases/character-stats-shield-block-client-2026110604'


def remote(code):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError(p.stderr[-2500:]+p.stdout[-1200:])
    return json.loads(p.stdout)


def main(action):
    receipt=json.loads((SIGNED/'verification.json').read_text())
    assert receipt['release']==2026110604 and receipt['changed_assets']==1
    files={n:(SIGNED/n).read_bytes() for n in ('channel.json','previous-channel.json','uifiles/nightcap/equi_inventory.xml')}
    for n in ('publish.py','test_publish.py'):files[n]=(HERE/n).read_bytes()
    pins={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}
    if action=='stage':
        encoded={n:base64.b64encode(v).decode() for n,v in files.items()}
        result=remote(f'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
stage=Path({STAGE!r});assert not stage.exists()
assert shutil.disk_usage('/opt/nightcap').free>2*{sum(map(len,files.values()))}+350*1024**2
os.umask(0o077);stage.mkdir(mode=0o700);files={encoded!r};pins={pins!r}
for n,raw in files.items():
 data=base64.b64decode(raw,validate=True);assert hashlib.sha256(data).hexdigest()==pins[n]
 (stage/n).parent.mkdir(parents=True,exist_ok=True)
 with (stage/n).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
p=subprocess.run(['python3','-B','-m','unittest','test_publish'],cwd=stage,capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr[-2200:]
print(json.dumps(dict(status='staged_not_published',files=len(pins),linux_tests=p.stderr.strip().splitlines()[-1],pins=pins)))
''')
    else:
        result=remote(f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json,subprocess
stage=Path({STAGE!r});pins={pins!r}
for n,pin in pins.items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==pin
root=Path('/opt/nightcap/deploy/production')
deployed=json.loads((Path('/opt/nightcap/releases/character-stats-window-20261106-v1/evidence/activation/deployed.json')).read_text())
assert deployed['gateway_open'] and not deployed['database_restored']
def guard():
 for name in ('game','gateway'):
  cid=subprocess.check_output(['docker','compose','ps','-q',name],cwd=root,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled']
  if name=='game':
   assert row['Image']==deployed['runtime']['image_id'] and row['State']['StartedAt']==deployed['runtime']['started_at']
   assert row['State']['Health']['Status']=='healthy'
spec=importlib.util.spec_from_file_location('publisher',stage/'publish.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 result=p.publish(stage,root/'data/public');guard()
 p.replace((json.dumps(result,indent=2)+'\\n').encode(),stage/'published.json')
print(json.dumps(result))
''')
    (HERE/('client-staged.json' if action=='stage' else 'client-published.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'action':action,'release':2026110604,'status':result.get('status','published'),'files':len(pins)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('stage','publish'))
    main(parser.parse_args().action)
