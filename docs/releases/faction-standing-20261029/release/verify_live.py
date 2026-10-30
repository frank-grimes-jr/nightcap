"""Read-only final verification after acknowledged opening; no player state snapshot."""
from pathlib import Path
import hashlib,json,subprocess
from stage_release import SSH,STAGE
HERE=Path(__file__).resolve().parent
resume_pin=hashlib.sha256((HERE/'resume_normalization.py').read_bytes()).hexdigest()
pin=hashlib.sha256((HERE/'rollout.py').read_bytes()).hexdigest()
code=f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json,datetime,shutil
root=Path('/opt/nightcap/deploy/production');stage=Path({STAGE!r})
assert hashlib.sha256((stage/'rollout.py').read_bytes()).hexdigest()=={pin!r}
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 spec=importlib.util.spec_from_file_location('verified_faction_release',stage/'rollout.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
 resume=stage/'resume_normalization.py'
 if (stage/'evidence/preflight-resumed.json').exists():
  assert hashlib.sha256(resume.read_bytes()).hexdigest()=={resume_pin!r}
  spec2=importlib.util.spec_from_file_location('faction_resume',resume);cont=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(cont)
  original=op.read(stage/'evidence/preflight.json');proof=op.read(stage/'zone-normalization-proof.json')
  assert op.read(stage/'evidence/preflight-resumed.json')==cont.reconcile(original,op.content(),proof)
  op.read=cont.original_preflight_read(op)
 p=op.read(stage/'evidence/preflight.json');a=op.read(stage/'evidence/activation/deployed.json')
 assert a['gateway_open'] and a['database_restored'] is False
 assert not list((stage/'evidence/activation').glob('held-*.json'))
 runtime=op.r.running(a['runtime']['image_id'],op.binaries(),a['runtime']['restart_count'])
 assert runtime['started_at']==a['runtime']['started_at']
 assert op.r.compact('game')==a['game'] and op.r.state('gateway')['State']['Running']
 op.unchanged(p);op.verify_commands(p['commands'],installed=True)
 checks=op.contract();op.base.health();op.r.closed_ports()
 result={{'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed','image_id':runtime['image_id'],'started_at':runtime['started_at'],'restart_count':runtime['restart_count'],'zone_workers':sum(n=='zone' for n,h in runtime['processes']),'errors':runtime['errors'],'checks':checks,'gateway_open':True,'factions_access':0,'legacy_faction_access_preserved':True,'other_command_settings_preserved':True,'retained_binaries_quests_cache_content_client_verified':True,'changed_native_binaries':['zone'],'saved_state_tables_at_open':a['state_tables'],'free_bytes':shutil.disk_usage(root).free,'owner_gameplay_accepted':False,'private_metadata_exported':False}}
 print(json.dumps(result))
'''
p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=300)
if p.returncode:raise RuntimeError(p.stderr[-2500:])
result=json.loads(p.stdout);(HERE/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
