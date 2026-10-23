from pathlib import Path
import base64,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
p=HERE/'package-v2'
small={n:base64.b64encode((p/n).read_bytes()).decode() for n in ('rollout.py','runtime-contract.json','manifest.json')}
remote=r'''
from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
os.umask(0o077)
s=Path('/opt/nightcap/releases/aa-level-progression-20261023-v2')
assert not (s/'evidence').exists() and not (s/'preflight.log').exists()
small=SMALL
for name,raw in small.items():
 expected=base64.b64decode(raw);current=(s/name).read_bytes()
 assert current==expected.replace(b'\r\n',b'\n'),name
for name,raw in small.items():(s/name).write_bytes(base64.b64decode(raw))
m=json.loads((s/'manifest.json').read_text())
for name,h in m['files'].items():assert hashlib.sha256((s/name).read_bytes()).hexdigest()==h,name
with (s/'preflight.log').open('x') as log:
 result=subprocess.run(['python3',str(s/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,'Preflight stopped; inspect private preflight.log'
p=json.loads((s/'evidence/preflight.json').read_text())
print(json.dumps({'status':'production preflight passed; game unchanged','stage':str(s),'image':p['image'],'base_image':p['services']['game']['image_id'],'rules_before':len(p['before']),'rules_after':len(p['after']),'free_bytes':shutil.disk_usage(s).free,'manifest_sha256':p['manifest_sha256']}))
'''.replace('SMALL',repr(small))
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
r=subprocess.run(ssh,input=remote.encode(),capture_output=True)
(HERE/'staging-v2-repaired-output.txt').write_bytes(r.stdout+r.stderr)
if r.returncode:raise RuntimeError((r.stdout+r.stderr).decode()[-1800:])
receipt=json.loads(r.stdout);receipt['source_revision']=json.loads((p/'manifest.json').read_text())['source_revision']
(HERE/'preflight-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
