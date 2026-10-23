"""Ship only the signed public AA client assets and run the reviewed publisher."""
from pathlib import Path
import base64,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
names=('channel.json','previous-channel.json','dinput8.dll','nightcap-patch-sites.json')
files={n:base64.b64encode((HERE/'stage'/n).read_bytes()).decode() for n in names}
files['publish.py']=base64.b64encode((HERE/'publish.py').read_bytes()).decode()
pins={n:hashlib.sha256(base64.b64decode(v)).hexdigest() for n,v in files.items()}
source=r'''
from pathlib import Path
import base64,hashlib,json,os,subprocess
os.umask(0o077)
s=Path('/opt/nightcap/releases/aa-level-progression-20261023-v3/client')
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
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
p=subprocess.run(ssh,input=source.encode(),capture_output=True)
if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-2000:])
result=json.loads(p.stdout);(HERE/'published.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'release':result['release'],'changed_assets':result['changed_assets'],'preserved_assets':result['preserved_assets'],'services_unchanged':result['services_before']==result['services_after']}))
