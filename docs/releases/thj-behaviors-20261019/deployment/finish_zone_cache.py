"""Finish the fully committed release after authenticating native cache expiry."""
import argparse,datetime,fcntl,importlib.util,json,os,shutil,time
from pathlib import Path
S=Path('/opt/nightcap/releases/thj-behaviors-live-20261019');sp=importlib.util.spec_from_file_location('paired',S/'rollout.py');op=importlib.util.module_from_spec(sp);sp.loader.exec_module(op);op.initialize();r=op.r;F=S/'finish-evidence'

def finish():
 assert not F.exists() and not r.state('game')['State']['Running'] and not r.state('gateway')['State']['Running']
 assert r.state('game')['State']['ExitCode']==0
 p=op.load(S/'resume-evidence/preflight.json');old=op.load(S/'resume-evidence/stopped-state.json');now=op.saved_state()
 original_cache=old['player'].pop('zone_state_spawns');new_cache=now['player'].pop('zone_state_spawns');assert now==old
 old['player']['zone_state_spawns']=original_cache;now['player']['zone_state_spawns']=new_cache
 assert original_cache['rows']==5775 and new_cache['rows']==4662
 assert all((S/'resume-evidence'/(n+'-committed.json')).exists() for n in ('01-aa-spells','02-items','03-rule'))
 assert not (S/'resume-evidence/opening.json').exists()
 assert op.sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:StateSaveClearDays';").strip()=='7'
 started=r.state('game')['State']['StartedAt'];stamp=datetime.datetime.fromisoformat(started.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M:%S')
 scratch='nightcap_thj_state_hold_20261019.zone_state_spawns'
 fields=[line.split('\t') for line in op.sql('SHOW COLUMNS FROM zone_state_spawns;').splitlines()]
 predicates=[]
 for name,kind,*_ in fields:
  assert name.replace('_','').isalnum()
  if kind.startswith(('float','double')):predicates.append(f'BINARY CAST(o.`{name}` AS CHAR)<=>BINARY CAST(n.`{name}` AS CHAR)')
  else:predicates.append(f'o.`{name}`<=>n.`{name}`')
 assert op.sql('SELECT COUNT(*) FROM '+scratch+' o JOIN peq.zone_state_spawns n ON n.id=o.id WHERE NOT ('+' AND '.join('('+x+')' for x in predicates)+');').strip()=='0'
 assert op.sql('SELECT COUNT(*) FROM peq.zone_state_spawns n LEFT JOIN '+scratch+' o ON n.id=o.id WHERE o.id IS NULL;').strip()=='0'
 expired=op.sql("SELECT COUNT(*) FROM "+scratch+" o LEFT JOIN peq.zone_state_spawns n ON n.id=o.id WHERE n.id IS NULL AND o.is_corpse=0 AND o.is_zone=0 AND o.instance_id=0 AND o.zone_id IN (13,25,30,73) AND o.created_at<DATE_SUB('"+stamp+"',INTERVAL 7 DAY);").strip();assert expired=='1113'
 assert op.sql("SELECT COUNT(*) FROM peq.zone_state_spawns WHERE created_at<DATE_SUB('"+stamp+"',INTERVAL 7 DAY);").strip()=='0'
 first_rotation=op.b.verify_market(op.load(S/'resume-evidence/market-before.json'),started)
 op.untouched(p,True);caches=op.load(S/'resume-evidence/generated-caches.json');assert all(op.sha(op.ROOT/'data/server/shared'/n)==v['sha256'] for n,v in caches.items())
 assert shutil.disk_usage(op.ROOT).free>=1024**3+128*1024**2
 F.mkdir(mode=0o700);op.EVIDENCE=F;r.EVIDENCE=F;r.STAGE=F
 op.save(F/'preflight.json',p);op.save(F/'stopped-state.json',now);market=op.b.market();op.save(F/'market-before.json',market)
 op.save(F/'cache-expiry.json',{'removed':1113,'zones':[13,25,30,73],'instance':0,'corpses':0,'rule_days':7,'added':0,'survivors_match':True,'float_comparison':'Canonical stored text due dump FLOAT representation','first_market_rotation':first_rotation,'other_player_and_custom_state_unchanged':True,'source_files_match_native_manifest':True})
 try:
  op.save(F/'backup.json',r.database_backup());assert op.saved_state()==now;op.untouched(p,True)
  assert r.image_hashes(p['new_image_id'])=={**op.manifest()['base_hashes'],**{'bin/'+n:h for n,h in op.binaries().items()}}
  r.select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game');first=r.running(p['new_image_id'],op.binaries());op.health();time.sleep(8)
  current=r.running(p['new_image_id'],op.binaries());assert current['started_at']==first['started_at']
  rotation=op.b.verify_market(market,current['started_at']);assert op.saved_state()==now;op.untouched(p,True)
  assert op.sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')==p['rules_after']
  assert all(op.sha(op.ROOT/'data/server/shared'/n)==v['sha256'] for n,v in caches.items());op.health();r.closed_ports()
  closed={'game':r.compact('game'),'runtime':current,'market':rotation,'caches':caches,'player_tables':len(now['player']),'custom_tables':len(now['custom'])}
  op.save(F/'activated-closed.json',closed);op.save(S/'evidence/activated-closed.json',closed);print('Verified final runtime with authenticated native cache expiry.',flush=True)
 except BaseException:op.hold();raise

if __name__=='__main__':
 assert __debug__;os.umask(0o077);a=argparse.ArgumentParser();a.add_argument('action',choices=['finish','open']);action=a.parse_args().action
 with (op.ROOT/'.deployment.lock').open('a') as l,open('/var/lock/nightcap-gm.lock','a') as gm:
  fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
  if action=='finish':finish()
  else:op.EVIDENCE=F;r.EVIDENCE=F;r.STAGE=F;op.open_access()
