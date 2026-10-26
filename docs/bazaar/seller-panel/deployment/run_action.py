"""Run one owner-authorized activation/open; never automatically retry."""
import argparse,json,subprocess
from pathlib import Path
from ship import SSH,STAGE,ROOT
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['activate','open']);args=parser.parse_args()
local=ROOT/'docs/bazaar/private/seller-panel'/('runtime-'+args.action+'.json')
assert not local.exists(),'Inspect prior result; do not replay'
source="""
from pathlib import Path
import json,subprocess
stage=Path(STAGE)
log=stage/(ACTION+'-operator.log')
with log.open('x') as stream:
 result=subprocess.run(['python3',str(stage/'rollout.py'),ACTION],stdout=stream,stderr=subprocess.STDOUT)
assert result.returncode==0,log.read_text()[-5000:]
name='deployed.json' if ACTION=='open' else 'verified-closed.json'
receipt=json.loads((stage/'evidence/activation'/name).read_text())
state=json.loads((stage/'evidence/activation/stopped-state.json').read_text())
assert len([n for n in state if n.startswith('nightcap_bazaar_')])==5
print(json.dumps(receipt))
""".replace('STAGE',repr(STAGE)).replace('ACTION',repr(args.action))
result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=900)
if result.returncode:raise RuntimeError(result.stderr[-6000:])
receipt=json.loads(result.stdout);local.write_text(json.dumps(receipt,indent=2)+'\n')
if args.action=='open':
 (ROOT/'docs/bazaar/seller-panel/deployed.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'action':args.action,'image':receipt['runtime']['image_id'],'zone_workers':sum(p[0]=='zone' for p in receipt['runtime']['processes']),'errors':receipt['runtime']['errors'],'checks':receipt['checks'],'state_tables':receipt['state_tables'],'gateway_open':receipt.get('gateway_open',False)}))
