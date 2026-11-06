"""Fresh read-only verification and redacted runtime/backup receipt after opening."""
import json
from pathlib import Path
import subprocess
from stage import SSH

HERE=Path(__file__).resolve().parent
CODE='''from pathlib import Path
import importlib.util,json
stage=Path('/opt/nightcap/releases/character-stats-window-20261106-v1')
for action in ('preflight','activate','open'):
 result=json.loads((stage/'jobs'/action/'result.json').read_text());assert result['returncode']==0
spec=importlib.util.spec_from_file_location('report',stage/'rollout.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o);o.initialize()
p=o.read(stage/'evidence/preflight.json');d=o.read(stage/'evidence/activation/deployed.json')
assert d['gateway_open'] and not d['database_restored']
runtime=o.r.running(p['image'],o.binaries());assert runtime['started_at']==d['runtime']['started_at']
o.base.health();o.r.closed_ports();o.command_state(True);assert o.r.state('gateway')['State']['Running']
assert o.content()==p['content'] and o.rules()==p['rules'] and o.h.caches()==p['caches']
backup=o.read(stage/'evidence/activation/backup.json')
print(json.dumps({'status':'deployed for live QA','source_revision':o.m['source_revision'],'runtime':runtime,'gateway_open':True,
 'database_restored':False,'item_definitions_changed':False,'cache_changed':False,'command_access':0,'client_update_required':True,
 'owner_native_visual_accepted':False,'owner_gameplay_accepted':False,'checks':d['checks'],
 'backup':{k:backup[k] for k in ('sha256','compressed_bytes','uncompressed_bytes','gzip_integrity')},
 'saved_state_model':'verified before reopening; live player progress is not compared to an old snapshot',
 'command_scope':'all command settings preserved; existing augstats fallback retained'}))
'''
if __name__=='__main__':
    p=subprocess.run(SSH+['sudo -n python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    d=json.loads(p.stdout);(HERE/'deployed.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({k:d[k] for k in ('status','gateway_open','cache_changed','command_access','backup')}))
