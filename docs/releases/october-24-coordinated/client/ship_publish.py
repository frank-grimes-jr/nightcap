"""Ship only the signed public AA client assets and run the reviewed publisher."""
from pathlib import Path
import base64,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
names=('channel.json','previous-channel.json','global_chr.s3d','global4_chr.s3d')
files={n:base64.b64encode((HERE.parent/'private/client-signed-v2'/n).read_bytes()).decode() for n in names}
files['publish.py']=base64.b64encode((HERE/'publish.py').read_bytes()).decode()
pins={n:hashlib.sha256(base64.b64decode(v)).hexdigest() for n,v in files.items()}
source=r'''
from pathlib import Path
import base64,hashlib,json,os,subprocess
os.umask(0o077)
s=Path('/opt/nightcap/releases/oct24-helmet-client-20261024-v2')
assert not s.exists()
files=FILES;pins=PINS
s.mkdir(mode=0o700)
for n,v in files.items():
 p=s/n;p.write_bytes(base64.b64decode(v));assert hashlib.sha256(p.read_bytes()).hexdigest()==pins[n]
p=subprocess.run(['python3',str(s/'publish.py'),'--stage',str(s),'--publish'],capture_output=True,text=True)
(s/'publication.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,'Client publication stopped; inspect receipt before retry'
result=json.loads((s/'published.json').read_text());print(json.dumps(result))
'''.replace('FILES',repr(files)).replace('PINS',repr(pins))
import importlib.util
spec=importlib.util.spec_from_file_location('release_remote',HERE.parents[2]/'quests/camil-chapterhouse/deployment/remote.py')
remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
ssh=remote.SSH+['sudo -n python3 -']
p=subprocess.run(ssh,input=source.encode(),capture_output=True)
if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-2000:])
result=json.loads(p.stdout);(HERE.parent/'private/client-published-v2.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'release':result['release'],'changed_assets':result['changed_assets'],'preserved_assets':result['preserved_assets'],'services_unchanged':result['services_before']==result['services_after']}))
