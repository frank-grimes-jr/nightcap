"""Execute one explicitly authorized rollout phase and retain aggregate receipts."""
import json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
action=sys.argv[1];assert action in ('activate','open','rollback','open-rollback')
source=r'''
from pathlib import Path
import json,subprocess,shutil,datetime
stage=Path('/opt/nightcap/releases/rogue-tomes-20261024');action=ACTION
with (stage/(action+'.log')).open('x') as log:
 p=subprocess.run(['python3',str(stage/'rollout.py'),action],stdout=log,stderr=subprocess.STDOUT)
if p.returncode:raise RuntimeError('Action held: '+(stage/(action+'.log')).read_text()[-5000:])
folder=stage/'evidence'/('recovery' if action in ('rollback','open-rollback') else 'activation')
opened=action in ('open','open-rollback')
a=json.loads((folder/('deployed.json' if opened else 'verified-closed.json')).read_text())
backup=json.loads((folder/'backup.json').read_text());expiry=json.loads((folder/'native-expiry.json').read_text())
print(json.dumps({'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':action,'result':'PASS','stage':str(stage),'runtime':a['runtime'],'state_tables':a['state_tables'],'checks':a['checks'],'market':a['market'],'backup':backup,'expired_noncorpse_cache_rows':expiry['expired_noncorpse_rows'],'free_bytes':shutil.disk_usage(stage).free,'gateway_open':opened,'owner_gameplay_accepted':False,'database_restored':False,'client_update_required':False}))
'''.replace('ACTION',repr(action))
ssh=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',os.environ['NIGHTCAP_DEPLOY_SSH_TARGET'],'sudo -n python3 -']
p=subprocess.run(ssh,input=source.encode(),capture_output=True,timeout=900)
if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-6000:])
result=json.loads(p.stdout);(HERE/(action+'-receipt.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
