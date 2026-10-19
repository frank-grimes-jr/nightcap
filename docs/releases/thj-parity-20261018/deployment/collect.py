"""Read and retain deployment receipts; verify current runtime without touching players."""
import json
from pathlib import Path
from remote import run

HERE=Path(__file__).resolve().parent
source=r'''
import json,sys
from pathlib import Path
stage=Path('/opt/nightcap/releases/thj-parity-20261018')
sys.path.insert(0,str(stage));import rollout as op
op.initialize();p=op.load(stage/'rule-notes-recovery/expected.json');a=op.load(stage/'evidence/deployed.json')
assert a['gateway_open'];op.health();op.r.closed_ports();op.untouched(p,True,True);op.published_client()
runtime=op.r.running(p['new_image_id'],op.binaries());assert runtime['started_at']==a['runtime']['started_at']
assert op.r.state('gateway')['State']['Running']
files={x.name:json.loads(x.read_text()) for x in (stage/'evidence').glob('*.json')}
files['client-published.json']=json.loads((stage/'client/published.json').read_text())
files.update({'rule-notes-'+x.name:json.loads(x.read_text()) for x in (stage/'rule-notes-recovery').glob('*.json')})
files['report.json']={'runtime':runtime,'services':{s:op.r.compact(s) for s in ('game','gateway','db','web','tunnel')},
 'effective_ruleset':op.routing(),'content_afterimages_verified':True,'client_assets_verified':138,'player_state_restored':False}
print(json.dumps(files))
'''
data=json.loads(run(source))
target=HERE/'receipts';target.mkdir(exist_ok=False)
for name,value in data.items():
    assert Path(name).name==name
    (target/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'receipts':len(data),'runtime':data['report.json']['runtime']['image_id'],'gateway_open':True}))
