"""Explicit operations for the user-authorized passive-AA deployment."""
import argparse,json,subprocess
from pathlib import Path
r=Path(__file__).parent
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/passive-aa-20261004'
p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','upload','preflight','activate','report','evidence']);a=p.parse_args()
if a.action=='inspect':
    result=subprocess.run(SSH+['sudo -n python3 -'],input=(r/'inspect_host.py').read_text(),text=True,capture_output=True,check=True,timeout=120)
    with (r/'hosted-before.json').open('x') as f:f.write(result.stdout)
    d=json.loads(result.stdout);print(json.dumps({'image':d['image'],'services':d['services'],'rules':d['rules'],'client_release':d['public']['channel.json']['signed']['release']}))
elif a.action=='upload':
    name='passive-aa-server-20261004.tar.gz'
    subprocess.run(['scp','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',str(r/name),'ubuntu@135.148.47.202:/home/ubuntu/'+name],check=True,timeout=600)
    result=subprocess.run(SSH+['sudo -n python3 -'],input=(r/'stage-server.py').read_text(),text=True,capture_output=True,check=True,timeout=180)
    print(result.stdout)
elif a.action=='evidence':
    code="import json;from pathlib import Path;p=Path('"+STAGE+"/evidence');print(json.dumps({n.name:json.loads(n.read_text()) for n in p.glob('*.json')}))"
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,check=True,timeout=60)
    (r/'deployment-evidence.json').write_text(result.stdout);print('Saved deployment evidence')
else:
    result=subprocess.run(SSH+['sudo -n python3 '+STAGE+'/rollout.py '+a.action],text=True,capture_output=True,timeout=1200)
    (r/('server-'+a.action+'.log')).write_text(result.stdout+result.stderr)
    print(result.stdout);print(result.stderr);result.check_returncode()
