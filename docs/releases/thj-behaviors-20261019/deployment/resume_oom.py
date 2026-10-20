"""Resume only the diagnosed pre-write DB OOM; retain original receipts and data."""
import argparse,fcntl,importlib.util,json,os,shutil,time
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/thj-behaviors-live-20261019')
spec=importlib.util.spec_from_file_location('paired',STAGE/'rollout.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
ORIGINAL=op.EVIDENCE;RESUME=STAGE/'resume-evidence';r=op.r

def activate():
 assert not RESUME.exists()
 p=op.load(ORIGINAL/'preflight.json');before=op.load(ORIGINAL/'stopped-state.json');market=op.load(ORIGINAL/'market-before.json')
 assert (ORIGINAL/'01-aa-spells-attempted.json').exists() and not (ORIGINAL/'01-aa-spells-committed.json').exists()
 assert not (ORIGINAL/'opening.json').exists() and not (ORIGINAL/'generated-caches.json').exists()
 assert op.checksums(op.TABLES)==p['before'] and op.saved_state()==before and op.b.market()==market
 op.guards()
 assert all(r.compact(n)==p['services'][n] for n in ('web','tunnel'))
 db=r.compact('db');old=p['services']['db']
 assert db['id']==old['id'] and db['image_id']==old['image_id'] and db['restarts']==old['restarts']+1 and db['health']=='healthy' and db['running'] and not db['oom_killed']
 for n in ('game','gateway'):
  current=r.compact(n);prior=p['services'][n]
  assert not current['running'] and all(current[k]==prior[k] for k in ('id','image_id','started_at','restarts'))
 assert r.state('game')['State']['ExitCode']==0
 assert shutil.disk_usage(op.ROOT).free>=1024**3+128*1024**2
 # No uncertain writes: exact original content, earned state, market and absent routines proved above.
 RESUME.mkdir(mode=0o700);op.EVIDENCE=RESUME;r.EVIDENCE=RESUME;r.STAGE=RESUME
 p['services']['db']=db
 op.save(RESUME/'preflight.json',p);op.save(RESUME/'stopped-state.json',before);op.save(RESUME/'market-before.json',market)
 op.save(RESUME/'diagnosis.json',{'cause':'Kernel-confirmed database cgroup OOM during CREATE PROCEDURE; cold database recovered','old_db':old,'recovered_db':db,'content_and_owned_state_unchanged':True,'original_receipts_retained':True})
 try:
  op.save(RESUME/'backup.json',r.database_backup());assert op.saved_state()==before;op.untouched(p)
  for component in op.manifest()['components']:
   name=Path(component).stem;op.save(RESUME/(name+'-attempted.json'),{'sha256':op.manifest()['files'][component]})
   op.sql((STAGE/component).read_text());op.save(RESUME/(name+'-committed.json'),{'status':'success'})
  assert op.saved_state()==before;op.untouched(p,True)
  r.select(p['new_image_id']);r.compose('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')
  caches={n:{'bytes':(op.ROOT/'data/server/shared'/n).stat().st_size,'sha256':op.sha(op.ROOT/'data/server/shared'/n)} for n in ('items','spells')};op.save(RESUME/'generated-caches.json',caches)
  r.compose('up','-d','--wait','--wait-timeout','240','game');first=r.running(p['new_image_id'],op.binaries());op.health();time.sleep(8)
  current=r.running(p['new_image_id'],op.binaries());assert current['started_at']==first['started_at']
  rotation=op.b.verify_market(market,current['started_at']);assert op.saved_state()==before;op.untouched(p,True)
  assert op.sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')==p['rules_after']
  assert all(v['bytes']>1000000 and op.sha(op.ROOT/'data/server/shared'/n)==v['sha256'] for n,v in caches.items())
  op.health();r.closed_ports();assert not r.state('gateway')['State']['Running']
  closed={'game':r.compact('game'),'runtime':current,'market':rotation,'caches':caches,'player_tables':len(before['player']),'custom_tables':len(before['custom'])}
  op.save(RESUME/'activated-closed.json',closed)
  # The unchanged client baseline reader consumes this verified closed-state receipt.
  op.save(ORIGINAL/'activated-closed.json',closed)
  print('Recovered release verified; access closed for client publication.',flush=True)
 except BaseException:op.hold();raise

def open_access():
 op.EVIDENCE=RESUME;r.EVIDENCE=RESUME;r.STAGE=RESUME;op.open_access()

if __name__=='__main__':
 assert __debug__;os.umask(0o077)
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['activate','open']);a=parser.parse_args()
 with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
  {'activate':activate,'open':open_access}[a.action]()
