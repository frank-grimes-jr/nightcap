"""Read back bounded deployment evidence and fresh augment state; no writes."""
import json
from pathlib import Path
import subprocess
from probe import SSH

HERE=Path(__file__).resolve().parent
CODE='''from pathlib import Path
import importlib.util,json,hashlib
stage=Path('/opt/nightcap/releases/augment-audit-20261106-v1')
spec=importlib.util.spec_from_file_location('augments',stage/'rollout.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
deployed=op.read(stage/'evidence/activation/deployed.json');before=op.read(stage/'evidence/preflight.json')
current=op.r.running(before['image'],op.binaries());op.base.health();op.r.closed_ports();op.owned(True)
assert current['started_at']==deployed['runtime']['started_at'] and op.r.state('gateway')['State']['Running']
cache=op.compare_cache(op.records(stage/'rehearsal/before-items'),op.records(op.ROOT/'data/server/shared/items'))
assert cache==before['rehearsal']['cache']
checks=op.contract(before['rehearsal']['contract_overrides'])
counts=op.sql('SELECT enabled,augment_chance,gear_chance,COUNT(*) FROM nightcap_zone_hunt_zones GROUP BY 1,2,3;').splitlines()
backup=op.read(stage/'evidence/activation/backup.json')
report={'status':'deployed for live QA','source_revision':op.m['source_revision'],'runtime':current,'cache':cache,'checks':checks,
 'backup':{k:backup[k] for k in ('sha256','compressed_bytes','uncompressed_bytes','gzip_integrity')},'zone_rate_groups':counts,
 'gateway_open':True,'client_update_required':False,'database_restored':False,'capacity_activated':False,'owner_gameplay_accepted':False,
 'owner_artwork_accepted':True,'changed_items':232,'changed_zone_enable_flags':[48,186],
 'contract_overrides':before['rehearsal']['contract_overrides'],'manifest_sha256':op.sha(stage/'manifest.json')}
print(json.dumps(report))
'''
result=subprocess.run(SSH+['sudo -n python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True,timeout=240)
if result.returncode:raise RuntimeError(result.stderr[-2000:])
data=json.loads(result.stdout);(HERE/'deployed.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ('status','changed_items','changed_zone_enable_flags','zone_rate_groups','gateway_open','cache','backup')}))
