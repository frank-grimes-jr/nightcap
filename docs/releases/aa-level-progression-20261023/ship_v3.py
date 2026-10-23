"""Fresh attempt using verified immutable binary hardlinks; preflight only."""
from pathlib import Path
import base64,hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=HERE/'package-v3';p.mkdir();(p/'bin').mkdir()
m=json.loads((HERE/'package/manifest.json').read_text())
m['prebuilt_image']='sha256:5e501da82b8eae0d461f7f32d54539ae59d4b57e477bcb9e34f20bbd09146cf2'
for name,digest in m['replacement_binaries'].items():
 old=HERE/'package/bin'/name;assert sha(old)==digest
 (p/'bin'/name).hardlink_to(old)
for name in ('rollout.py','runtime-contract.json'):shutil.copyfile(HERE/name,p/name)
m['files']={q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file()}
m['source_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
small={name:base64.b64encode((p/name).read_bytes()).decode() for name in ('rollout.py','runtime-contract.json','manifest.json')}
remote=r'''
from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
os.umask(0o077)
old=Path('/opt/nightcap/releases/aa-level-progression-20261023')
new=Path('/opt/nightcap/releases/aa-level-progression-20261023-v3')
small=SMALL
pins=PINS
assert not new.exists() and old.is_dir() and not (old/'evidence').exists()
assert shutil.disk_usage(old).free>=672*1024**2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in pins.items():
 p=old/'bin'/name;assert p.is_file() and not p.is_symlink() and sha(p)==digest
new.mkdir(mode=0o700);(new/'bin').mkdir()
for name in pins:
 (new/'bin'/name).hardlink_to(old/'bin'/name)
 assert (new/'bin'/name).stat().st_ino==(old/'bin'/name).stat().st_ino
for name,data in small.items():
 p=new/name;p.write_bytes(base64.b64decode(data));p.chmod(0o644)
assert sha(new/'manifest.json')==MANIFEST_SHA
with (new/'preflight.log').open('x') as log:
 result=subprocess.run(['python3',str(new/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,'Preflight stopped; inspect private preflight.log'
p=json.loads((new/'evidence/preflight.json').read_text())
print(json.dumps({'status':'production preflight passed; game unchanged','stage':str(new),'image':p['image'],'base_image':p['services']['game']['image_id'],'rules_before':len(p['before']),'rules_after':len(p['after']),'free_bytes':shutil.disk_usage(new).free,'manifest_sha256':p['manifest_sha256']}))
'''
for key,value in [('SMALL',small),('PINS',m['replacement_binaries']),('MANIFEST_SHA',sha(p/'manifest.json'))]:remote=remote.replace(key,repr(value))
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
r=subprocess.run(ssh,input=remote.encode(),capture_output=True)
(HERE/'staging-v3-output.txt').write_bytes(r.stdout+r.stderr)
if r.returncode:raise RuntimeError((r.stdout+r.stderr).decode()[-1800:])
receipt=json.loads(r.stdout);receipt['source_revision']=m['source_revision']
(HERE/'preflight-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
