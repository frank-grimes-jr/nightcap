"""Owner-authorized Combined October24 live QA. Paired content/runtime; fail closed.

Reuse the reviewed Classic deployment primitives and current AA startup guards.
No player restoration or automatic down-migration. Retain earned receipts/runs.
"""
import argparse,fcntl,hashlib,importlib.util,json,mmap,os,re,shutil,struct,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/october-24-coordinated-20261024')
EVIDENCE=STAGE/'evidence'
PRIOR=Path('/opt/nightcap/releases/aa-level-progression-20261023-v3/rollout.py')
NEW_ITEMS=set(range(960420,960426))|set(range(961020,961024))|set(range(961030,961033))|{990510}

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def manifest():
 m=json.loads((STAGE/'manifest.json').read_text())
 assert sha(PRIOR)==m['prior_operator_sha256']
 for name,digest in m['files'].items():
  p=STAGE/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts
  assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==digest,name
 return m


NEW_TABLES=('nightcap_ashen_state','nightcap_ashen_characters','nightcap_highkeep_state','nightcap_highkeep_runs')
def storage(database='peq'):
 for table in NEW_TABLES:
  assert base.sql("SELECT ENGINE FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='"+table+"';",database).strip()=='InnoDB'
  assert not base.sql("SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table='"+table+"';",database).strip()
 return {t:base.sql('SHOW CREATE TABLE `'+t+'`;',database).strip() for t in NEW_TABLES}

def check_new_storage():
 assert storage()==base.load('new-storage.json'),'New campaign schema differs from fresh rehearsal'


def contract(database='peq'):
 result={}
 for family,checks in json.loads((STAGE/'runtime-contract.json').read_text()).items():
  values=base.sql(';\n'.join(c['sql'] for c in checks)+';',database).splitlines()
  assert len(values)==len(checks),(family,len(values))
  failures=[c['label'] for c,v in zip(checks,values) if v!=c['expected']]
  assert not failures,(family,failures)
  result[family]=len(checks)
 assert result=={'schema':51,'content':565}
 if database!='peq': base.save('new-storage.json',storage(database))
 return result

def records(path):
 result={}
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
  payload,count,maximum,current=struct.unpack_from('<IIII',data)
  assert maximum==current and len(data)==payload+8==20+4*count+1332*maximum
  start=16+4*count
  for item in range(count):
   index=struct.unpack_from('<I',data,16+item*4)[0]
   if index<current:
    value=data[start+index*1332:start+(index+1)*1332]
    assert struct.unpack_from('<I',value,440)[0]==item
    result[item]=hashlib.sha256(value).hexdigest()
 assert len(result)==current
 return result

def compare_cache(before,after):
 assert set(after)-set(before)==NEW_ITEMS and set(before)<=set(after)
 assert all(after[i]==v for i,v in before.items()),'Existing item cache changed'
 return {'preserved_items':len(before),'new_items':len(NEW_ITEMS),'existing_changed':0}

def cache_contract(image,path):
 result=json.loads(r.out('docker','run','--rm','--network','none','--memory','1024m','--user','0',
  '-v',str(STAGE)+':/stage:ro','-v',str(path)+':/items:ro','--entrypoint','/stage/cache_check',image,'/items'))
 assert result=={'items':441,'drift_rejections':882,'item_bytes':1332}
 return result

def build_image(m):
 base_tag='nightcap-game:october-24-coordinated-20261024-base';target='nightcap-game:october-24-coordinated-20261024'
 r.call('docker','tag',m['base_image_id'],base_tag)
 (STAGE/'Dockerfile').write_text('FROM '+base_tag+'\nCOPY bin/ /opt/nightcap/bin/\n')
 (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/*\n')
 assert {p.name for p in (STAGE/'bin').iterdir()}=={'world','zone','shared_memory'}
 r.call('docker','build','--pull=false','--network','none','-t',target,str(STAGE))
 image=r.out('docker','image','inspect','--format','{{.Id}}',target).strip()
 assert r.image_hashes(image)=={**m['base_hashes'],**{'bin/'+n:h for n,h in m['binaries'].items()}}
 layers=lambda v:json.loads(r.out('docker','image','inspect',v))[0]['RootFS']['Layers']
 assert layers(image)[:-1]==layers(m['base_image_id'])
 for name in ('world','zone','shared_memory'):
  assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+name)
 r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',
  'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
 r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
 return image

def script_guards(m):
 live=ROOT/'data/server'
 for name,before in m['script_preimages'].items():
  path=live/name;assert (sha(path) if path.exists() else None)==before,name
  assert not path.with_suffix('.lua').exists(),'Competing Lua script: '+name
 for name in m['absent_quest_shadows']:assert not (live/name).exists(),name

def install_scripts(m):
 previous=STAGE/'previous-scripts';previous.mkdir(mode=0o700)
 script_guards(m)
 live=ROOT/'data/server';owner=(live/'quests').stat()
 for name in m['scripts']:
  path=live/name;source=STAGE/name
  if path.exists():
   backup=previous/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
   stat=path.stat();mode,uid,gid=stat.st_mode,stat.st_uid,stat.st_gid
  else:
   path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
   os.chown(path.parent,owner.st_uid,owner.st_gid);os.chmod(path.parent,0o755)
   mode,uid,gid=0o644,owner.st_uid,owner.st_gid
  tmp=path.with_name(path.name+'.chapterhouse-'+str(time.time_ns()))
  with tmp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
  os.chmod(tmp,mode);os.chown(tmp,uid,gid);os.replace(tmp,path)

def campaign(enabled):
 for table in ('nightcap_ashen_state','nightcap_highkeep_state'):
  assert base.sql('SELECT revision,enabled FROM '+table+';').strip()==f'2026102401\t{enabled}',table
 for table in ('nightcap_ashen_characters','nightcap_highkeep_runs'):
  assert base.sql('SELECT COUNT(*) FROM '+table+';').strip()=='0','Unexpected enrollment: '+table

def activate_campaigns():
 # Both admission flags commit together. Uncertainty holds the whole release.
 query="START TRANSACTION; CREATE TEMPORARY TABLE release_flags_guard(ok INT CHECK(ok=1));"
 for table in ('nightcap_ashen_state','nightcap_highkeep_state'):
  query+='UPDATE '+table+' SET enabled=1 WHERE id=1 AND revision=2026102401 AND enabled=0; INSERT INTO release_flags_guard VALUES(ROW_COUNT());'
 base.sql(query+'COMMIT;')
 campaign(1)


def preflight():
 # The production capture showed no public saved spawns. Refuse new ones instead
 # of deleting any state implicitly. A later nonempty case needs a scoped audit.
 assert base.sql('SELECT COUNT(*) FROM zone_state_spawns WHERE zone_id=113;').strip()=='0'
 assert base.sql('SELECT COUNT(*) FROM instance_list WHERE zone=113;').strip()=='0'
 assert not base.sql("SHOW TABLES WHERE Tables_in_peq LIKE 'nightcap_ashen_%' OR Tables_in_peq LIKE 'nightcap_highkeep_%';").strip()
 original_preflight()
 p=base.load('preflight.json');assert p['services']['game']['image_id']==manifest()['base_image_id']

def activate():
 m=manifest();p=base.load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
 assert not (EVIDENCE/'activation-started.json').exists()
 base.unchanged(p);script_guards(m);prior.startup_guards()
 assert all(r.compact(s)==v for s,v in p['services'].items())
 assert shutil.disk_usage(ROOT).free>=800*1024**2
 base.save('activation-started.json',{'owner_authorized_live_testing':True})
 try:
  r.compose('stop','gateway')
  stop_started=time.monotonic()
  r.compose('stop','-t','90','game')
  stop_elapsed=time.monotonic()-stop_started
  assert stop_elapsed<70,'Shutdown approached the supervisor 75-second forced-kill deadline; inspect before continuing'
  state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
  assert not r.state('gateway')['State']['Running']
  base.save('native-shutdown.json',{'seconds':stop_elapsed,'supervisor_force_kill_deadline':75,'game_exit_code':state['ExitCode'],'oom_killed':False,'deadline_not_reached':True})
  base.save('startup-cleanup-guards.json',prior.startup_guards())
  data=base.saved_state();base.save('stopped-state.json',data);base.save('market-before.json',base.market())
  base.save('backup.json',r.database_backup());assert base.saved_state()==data; base.unchanged(p)
  assert base.sql('SELECT COUNT(*) FROM zone_state_spawns WHERE zone_id=113;').strip()=='0'
  assert base.sql('SELECT COUNT(*) FROM instance_list WHERE zone=113;').strip()=='0'
  before_cache=records(ROOT/'data/server/shared/items');spell_sha=sha(ROOT/'data/server/shared/spells')
  base.toggle(1,0)
  for component in m['components']:
   name=Path(component).stem;base.save(name+'-attempted.json',{'sha256':m['files'][component]})
   base.sql((STAGE/component).read_text());base.save(name+'-committed.json',{'success':True})
  checks=contract();campaign(0);check_new_storage()
  assert base.hashes(base.PUBLIC)==p['after'] and base.saved_state()==data
  install_scripts(m);base.unchanged(p,True);r.select(p['new_image_id'])
  r.compose('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')
  cache=cache_contract(p['new_image_id'],ROOT/'data/server/shared/items')
  comparison=compare_cache(before_cache,records(ROOT/'data/server/shared/items'))
  caches={n:sha(ROOT/'data/server/shared'/n) for n in ('items','spells')};assert caches['spells']==spell_sha
  base.save('generated-cache.json',{'hashes':caches,'contract':cache,'comparison':comparison})
  assert base.saved_state()==data;expected=base.boot_state(data);base.toggle(0,1)
  activate_campaigns()
  r.compose('up','-d','--wait','--wait-timeout','240','game')
  first=r.running(p['new_image_id'],m['binaries']);base.health();time.sleep(8)
  current=r.running(p['new_image_id'],m['binaries']);assert first['started_at']==current['started_at']
  rotation=base.verify_market(base.load('market-before.json'),current['started_at'])
  current_state=base.saved_state();base.save('boot-state.json',current_state)
  assert current_state==expected,'Closed-access state drift outside authenticated native expiry'
  base.unchanged(p,True);contract();campaign(1);check_new_storage();r.closed_ports()
  assert {n:sha(ROOT/'data/server/shared'/n) for n in caches}==caches
  assert not r.state('gateway')['State']['Running'] and shutil.disk_usage(ROOT).free>=512*1024**2
  base.save('verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
   'checks':checks,'cache':cache,'state_tables':len(data),'caches':caches,'campaign_enabled':True})
  print('Combined October24 runtime/content verified; access remains closed.',flush=True)
 except BaseException:base.hold();raise

def open_access():
 try:
  campaign(1);check_new_storage()
 except BaseException:
  base.hold();raise
 original_open()

def initialize():
 global prior,base,r,original_preflight,original_open
 manifest();spec=importlib.util.spec_from_file_location('retained_aa',PRIOR)
 prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior);prior.initialize()
 base=prior.base;r=prior.r
 original_preflight=base.preflight;original_open=base.open_access
 for module in (prior,prior.keeper,base,r):module.STAGE=STAGE;module.EVIDENCE=EVIDENCE
 original_tables=base.state_tables
 base.state_tables=lambda:[t for t in original_tables() if t not in {'nightcap_ashen_state','nightcap_ashen_characters','nightcap_highkeep_state','nightcap_highkeep_runs','nightcap_waypoints'}]
 base.PUBLIC|={'nightcap_waypoints','zone_points','ground_spawns','fishing','forage','traps','object'}
 base.manifest=manifest;base.contract=contract;base.records=records;base.compare_cache=compare_cache
 base.build_image=build_image
 base.cache_contract=cache_contract;base.script_guards=script_guards;base.install_scripts=install_scripts
 base.startup_guards=prior.startup_guards

if __name__=='__main__':
 assert __debug__;os.umask(0o077);initialize()
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','open'));action=parser.parse_args().action
 with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (ROOT/'private/gm-maintenance.json').exists()
  assert base.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
  {'preflight':preflight,'activate':activate,'open':open_access}[action]()
