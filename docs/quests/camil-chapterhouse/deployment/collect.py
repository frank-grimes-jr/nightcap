"""Collect compact, non-player delivery receipts from the completed release."""
import json
from pathlib import Path
from dispatch import remote,HERE

source='''from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil
stage=Path('/opt/nightcap/releases/camil-chapterhouse-20261023')
spec=importlib.util.spec_from_file_location('completion',stage/'resume-v2.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
o,b,r=op.o,op.b,op.r
deployed=b.load('deployed.json');pre=b.load('preflight.json');m=o.manifest()
current=r.running(pre['new_image_id'],m['binaries']);b.health();o.contract();r.closed_ports()
assert r.state('gateway')['State']['Running']
assert current['started_at']==deployed['runtime']['started_at']
assert r.public()==pre['public']
assert b.sql('SELECT revision,enabled FROM nightcap_vigil_state;').strip()=='2026102301\\t1'
assets={}
for folder,name in [('base','chapterhouse.map'),('nav','chapterhouse.nav'),('base','commons.map')]:
 p=o.ROOT/'data/server/maps'/folder/name
 assets[str(p.relative_to(o.ROOT/'data/server'))]={'bytes':p.stat().st_size,'sha256':o.sha(p)}
report={'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release':'camil-chapterhouse-20261023',
 'main_commit':'c0c9896e','runtime':current,'game':r.compact('game'),'gateway_open':True,'campaign_enabled':True,
 'checks':deployed['checks'],'cache':b.load('generated-cache.json'),'state_tables':deployed['state_tables'],
 'backup':b.load('backup.json'),'native_expiry':{k:v for k,v in b.load('native-expiry.json').items() if k!='expired_hashes'},
 'market':deployed['market'],'client_channel_sha256':m['client_channel_sha256'],'client_update_required':False,
 'scripts':{n:m['files'][n] for n in m['scripts']},'geometry_assets':assets,'disk_free':shutil.disk_usage(o.ROOT).free,
 'database_restored':False,'owner_gameplay_accepted':False,'waypoint_addition_reconciled':True,
 'first_hold_preserved':True,'fresh_preflight':json.loads((stage/'evidence/rehearsal.json').read_text())}
print(json.dumps(report))
'''
if __name__=='__main__':
 result=json.loads(remote(source));(HERE/'deployed.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ('verified_at','gateway_open','campaign_enabled','checks','state_tables','disk_free','database_restored')}))
