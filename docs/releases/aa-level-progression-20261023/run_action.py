"""Execute one reviewed release action; persist only aggregate local receipts."""
from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parent
action=sys.argv[1];assert action in ('activate','open')
source=r'''
from pathlib import Path
import json,subprocess,shutil
s=Path('/opt/nightcap/releases/aa-level-progression-20261023-v3')
action=ACTION
with (s/(action+'.log')).open('x') as log:
 p=subprocess.run(['python3',str(s/'rollout.py'),action],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'Action stopped; inspect private '+action+'.log before continuing'
a=json.loads((s/'evidence'/('verified-closed.json' if action=='activate' else 'deployed.json')).read_text())
backup=json.loads((s/'evidence/backup.json').read_text())
result={'action':action,'result':'PASS','stage':str(s),'runtime':a['runtime'],'state_tables':a['state_tables'],'checks':a['checks'],'caches':a['caches'],'market':a['market'],'backup':backup,'free_bytes':shutil.disk_usage(s).free,'gateway_open':action=='open','owner_gameplay_accepted':False,'database_restored':False}
print(json.dumps(result))
'''.replace('ACTION',repr(action))
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
p=subprocess.run(ssh,input=source.encode(),capture_output=True)
if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-2000:])
result=json.loads(p.stdout);(HERE/(action+'-receipt.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
