"""Resume the exact audited post-content/pre-runtime checkpoint, without replay.

The initial guard correctly held closed because the shared preservation list
also includes the public waypoint catalog. Only its rehearsed new checksum is
expected to change. Every other saved table remains exact; no snapshots restore.
Original held receipts and operator are retained unchanged.
"""
import argparse,fcntl,importlib.util,json,os,re,shutil,time
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/camil-chapterhouse-20261023')
OLD=STAGE/'evidence'
EVIDENCE=STAGE/'resume-evidence'

def expected_state(before,preflight):
 assert before['nightcap_waypoints']==preflight['before']['nightcap_waypoints']
 assert preflight['before']['nightcap_waypoints']!=preflight['after']['nightcap_waypoints']
 return {**before,'nightcap_waypoints':preflight['after']['nightcap_waypoints']}

def stopped(service,state):
 # Docker's gateway shell records SIGTERM as 143; native game must exit cleanly.
 assert service in ('game','gateway')
 assert not state['Running'] and not state['OOMKilled'] and not state.get('Error')
 assert state['ExitCode']==(0 if service=='game' else 143)

def initialize():
 global o,b,r
 spec=importlib.util.spec_from_file_location('reviewed_vigil',STAGE/'rollout.py')
 o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o);o.initialize();b=o.base;r=o.r
 o.manifest()
 for module in (o,o.prior,o.prior.keeper,b,r):module.EVIDENCE=EVIDENCE

def resume():
 assert not EVIDENCE.exists(),'Never replay this continuation'
 pre=json.loads((OLD/'preflight.json').read_text());m=o.manifest()
 assert pre['manifest_sha256']==o.sha(STAGE/'manifest.json')
 assert len(list(OLD.glob('held-*.json')))==1
 assert not (OLD/'verified-closed.json').exists() and not (OLD/'opening.json').exists()
 for name in ('20261023_chapterhouse_schema','20261023_chapterhouse_content'):
  assert json.loads((OLD/(name+'-committed.json')).read_text())=={'success':True}
 for service in ('game','gateway'):
  stopped(service,r.state(service)['State'])
 for service in ('db','web','tunnel'):assert r.compact(service)==pre['services'][service]
 assert r.compact('game')['image_id']==m['base_image_id']
 assert r.runtime()==pre['runtime'] and r.public()==pre['public']
 o.script_guards(m);o.prior.startup_guards();o.contract();o.campaign(0)
 assert b.sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t0'
 assert b.hashes(b.PUBLIC)==pre['after']
 before=json.loads((OLD/'stopped-state.json').read_text());expected=expected_state(before,pre)
 assert b.saved_state()==expected,'Unexpected drift beyond the rehearsed waypoint addition'
 assert shutil.disk_usage(o.ROOT).free>=800*1024**2
 EVIDENCE.mkdir(mode=0o700)
 b.save('preflight.json',pre)
 b.save('resume-authorized.json',{'checkpoint':'content committed, native/scripts/cache not installed','old_receipts_retained':True,
  'expected_waypoint_before':before['nightcap_waypoints'],'expected_waypoint_after':expected['nightcap_waypoints'],
  'all_other_saved_tables_preserved':True,'database_restore':False})
 shutil.copy2(OLD/'backup.json',EVIDENCE/'backup.json');shutil.copy2(OLD/'market-before.json',EVIDENCE/'market-before.json')
 try:
  old_cache=o.records(o.ROOT/'data/server/shared/items');spell_sha=o.sha(o.ROOT/'data/server/shared/spells')
  o.install_scripts(m);b.unchanged(pre,True);r.select(pre['new_image_id'])
  r.compose('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')
  cache=o.cache_contract(pre['new_image_id'],o.ROOT/'data/server/shared/items')
  comparison=o.compare_cache(old_cache,o.records(o.ROOT/'data/server/shared/items'))
  caches={n:o.sha(o.ROOT/'data/server/shared'/n) for n in ('items','spells')};assert caches['spells']==spell_sha
  b.save('generated-cache.json',{'hashes':caches,'contract':cache,'comparison':comparison})
  assert b.saved_state()==expected
  expected_boot=b.boot_state(expected);b.toggle(0,1)
  assert b.sql('UPDATE nightcap_vigil_state SET enabled=1 WHERE id=1 AND revision=2026102301 AND enabled=0; SELECT ROW_COUNT();').strip()=='1'
  r.compose('up','-d','--wait','--wait-timeout','240','game')
  first=r.running(pre['new_image_id'],m['binaries']);b.health();time.sleep(8)
  current=r.running(pre['new_image_id'],m['binaries']);assert first['started_at']==current['started_at']
  rotation=b.verify_market(b.load('market-before.json'),current['started_at'])
  now=b.saved_state();b.save('boot-state.json',now);assert now==expected_boot
  b.unchanged(pre,True);checks=o.contract();o.campaign(1);r.closed_ports()
  assert {n:o.sha(o.ROOT/'data/server/shared'/n) for n in caches}==caches
  assert not r.state('gateway')['State']['Running'] and shutil.disk_usage(o.ROOT).free>=512*1024**2
  b.save('verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
   'checks':checks,'cache':cache,'state_tables':len(expected),'caches':caches,'campaign_enabled':True,
   'waypoint_addition_reconciled':True})
  print('Chapterhouse runtime and exact saved-state preservation verified; access closed.',flush=True)
 except BaseException:b.hold();raise

if __name__=='__main__':
 assert __debug__;os.umask(0o077);initialize()
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('resume','open'));action=parser.parse_args().action
 with (o.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (o.ROOT/'private/gm-maintenance.json').exists() and b.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
  resume() if action=='resume' else o.open_access()
