"""Read only redacted release receipts and current health from production."""
import json,subprocess
from pathlib import Path
from ship import SSH,STAGE
HERE=Path(__file__).resolve().parent
source=f'''
import hashlib,importlib.util,json
from pathlib import Path
stage=Path({STAGE!r});spec=importlib.util.spec_from_file_location('keeper_release',stage/'rollout.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.initialize()
deployed=m.read('deployed.json');closed=m.read('verified-closed.json');before=m.read('preflight.json')
runtime=m.r.running(before['image'],m.binaries());m.old.health();m.r.closed_ports();m.untouched(before)
assert m.r.state('gateway')['State']['Running']
assert runtime['started_at']==deployed['runtime']['started_at']
rows=m.capture();assert rows['rows']['spawn2'][0]['zone']=='ecommons'
assert rows['rows']['zone'][0]['min_status']=='0' and rows['rows']['zone'][0]['min_level']=='46'
assert len(rows['rows']['nightcap_dungeon_spawns'])==1
backup=m.read('backup.json')
report={{'source_revision':m.manifest()['source_revision'],'deployed':deployed,'current_runtime':runtime,
 'contract':m.contract(),'services':{{s:m.r.compact(s) for s in ('game','gateway','db','web','tunnel')}},
 'state_tables_preserved':closed['state_tables'],'caches':closed['caches'],
 'backup':{{k:backup[k] for k in ('path','sha256','compressed_bytes','uncompressed_bytes','gzip_integrity')}},
 'public_keeper':{{k:rows['rows']['spawn2'][0][k] for k in ('id','zone','version','x','y','z','heading')}},
 'hate_access':{{k:rows['rows']['zone'][0][k] for k in ('zoneidnumber','short_name','min_status','min_level')}},
 'private_keeper':rows['rows']['nightcap_dungeon_spawns'],
 'native_expiry':{{k:v for k,v in m.read('native-expiry.json').items() if k!='expired_hashes'}},
 'owner_gameplay_accepted':False,'gateway_open':True,'database_restored':False}}
print(json.dumps(report))
'''
result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,check=True)
report=json.loads(result.stdout)
(HERE/'deployment.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('source_revision','contract','state_tables_preserved','public_keeper','hate_access','gateway_open')}))
