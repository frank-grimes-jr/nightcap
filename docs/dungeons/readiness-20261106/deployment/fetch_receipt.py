"""Read-only current native/content/cache/backup verification after access opens."""
import json
from pathlib import Path
import subprocess
from probe import SSH

HERE=Path(__file__).resolve().parent
CODE='''from pathlib import Path
import importlib.util,json
stage=Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1')
for action in ('preflight','activate','open'):
 result=json.loads((stage/'jobs'/action/'result.json').read_text());assert result['returncode']==0
spec=importlib.util.spec_from_file_location('keeper',stage/'rollout.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o);o.initialize()
before=o.read(stage/'evidence/preflight.json');deployed=o.read(stage/'evidence/activation/deployed.json')
assert deployed['gateway_open'] and deployed['zone_only'] and not deployed['database_restored']
runtime=o.p.r.running(before['image'],o.binaries());assert runtime['started_at']==deployed['runtime']['started_at']
o.p.base.health();o.p.r.closed_ports();o.p.command_state(True);checks=o.contract()
assert o.p.r.state('gateway')['State']['Running']
assert o.p.content()==before['content'] and o.p.rules()==before['rules'] and o.p.h.caches()==before['caches']
backup=o.read(stage/'evidence/activation/backup.json')
logs=o.p.r.out('docker','compose','logs','--no-color','--since',runtime['started_at'],'game')
assert not any(s in logs for s in ('MySQL Error','Orphaned Rule','Dungeon content drift','Dungeon schema drift','Dungeon item cache drift','Chapterhouse cache drift','Unknown column'))
print(json.dumps({'status':'deployed for live QA','source_revision':o.m['source_revision'],'runtime':runtime,'gateway_open':True,
 'database_restored':False,'zone_only':True,'item_definitions_changed':False,'cache_changed':False,'client_update_required':False,
 'owner_gameplay_accepted':False,'checks':checks,'backup':{k:backup[k] for k in ('sha256','compressed_bytes','uncompressed_bytes','gzip_integrity')},
 'saved_state_model':'verified before reopening; subsequent player progress is never compared to old snapshots',
 'saved_state_tables':len(o.read(stage/'evidence/activation/stopped-state.json')),
 'command_scope':'all settings retained; automatic Stats snapshots and augstats access0 preserved','native_log_errors':0}))
'''
if __name__=='__main__':
    result=subprocess.run(SSH+['sudo -n python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True,timeout=300)
    if result.returncode:raise RuntimeError(result.stderr[-2500:])
    report=json.loads(result.stdout);(HERE/'deployed.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','gateway_open','checks','backup','saved_state_tables','native_log_errors')}))
