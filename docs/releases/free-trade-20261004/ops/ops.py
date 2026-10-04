"""Explicit operations for the approved universal-trading release."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).parent
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/free-trade-20261004'
p=argparse.ArgumentParser();p.add_argument('action',choices=['before','inspect','upload','preflight','activate','report','evidence']);a=p.parse_args()
if a.action=='before':
    for source,name in [('blessing-lifetime-20261004/inspect_server.py','server-before-approval.json'),('classic-models-20260930/inspect-production.py','production-before-approval.json')]:
        result=subprocess.run(SSH+['sudo -n python3 -'],input=(ROOT.parent/source).read_text(),text=True,capture_output=True,check=True,timeout=120)
        data=json.loads(result.stdout)
        with (ROOT/name).open('x') as f:json.dump(data,f,indent=2)
    print(json.dumps({'services':data['services'],'client_release':data['public']['channel.json']['signed']['release']}))
elif a.action=='inspect':
    result=subprocess.run(SSH+['sudo -n python3 -'],input=(ROOT/'inspect_host.py').read_text(),text=True,capture_output=True,check=True,timeout=120)
    (ROOT/'host-inspection.json').write_text(result.stdout);print(result.stdout)
elif a.action=='upload':
    name='free-trade-server-20261004.tar.gz'
    subprocess.run(['scp','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',str(ROOT/name),'ubuntu@135.148.47.202:/home/ubuntu/'+name],check=True,timeout=600)
    result=subprocess.run(SSH+['sudo -n python3 -'],input=(ROOT/'stage-server.py').read_text(),text=True,capture_output=True,check=True,timeout=180)
    print(result.stdout)
elif a.action=='evidence':
    code="import json;from pathlib import Path;p=Path('"+STAGE+"/evidence');print(json.dumps({n.name:json.loads(n.read_text()) for n in p.glob('*.json')}))"
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,check=True,timeout=60)
    (ROOT/'deployment-evidence.json').write_text(result.stdout);print('Saved deployment evidence')
else:
    result=subprocess.run(SSH+['sudo -n python3 '+STAGE+'/rollout.py '+a.action],text=True,capture_output=True,timeout=900)
    (ROOT/('server-'+a.action+'.log')).write_text(result.stdout+result.stderr)
    print(result.stdout);print(result.stderr);result.check_returncode()
