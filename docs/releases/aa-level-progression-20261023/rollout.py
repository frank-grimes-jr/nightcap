"""Scoped AA activation; paired binaries, one rule, separate access reopening.

The approved release preserves player data and saved AA fractions. Recovery holds
access closed. Never restore player snapshots or silently revert percentage support.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/aa-level-progression-20261023-v2')
EVIDENCE=STAGE/'evidence'
PRIOR=Path('/opt/nightcap/releases/hate-keeper-commonlands-20261022/rollout.py')
RULE='AA:LevelBasedPointsPerLevel'
NOTES='Full-focus AA points per current level of normal XP; 0 disables level scaling. PassiveExpPercent applies to retained leveling XP. Clamp 0-1000; fixed ExpPerPoint storage units preserve saved AA fractions.'
NAMES={'world','zone','shared_memory','loginserver','ucs'}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((EVIDENCE/n).read_text())
def manifest():
 m=json.loads((STAGE/'manifest.json').read_text())
 assert sha(PRIOR)==m['prior_operator_sha256']
 assert set(m['binaries'])==NAMES and set(m['replacement_binaries'])=={'world','zone','shared_memory'}
 for n,h in m['files'].items():
  p=STAGE/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts
  assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==h,n
 return m
def initialize():
 global keeper,base,r,sql,save
 manifest();spec=importlib.util.spec_from_file_location('retained_keeper',PRIOR)
 keeper=importlib.util.module_from_spec(spec);spec.loader.exec_module(keeper);keeper.initialize()
 base=keeper.old;r=keeper.r;sql=base.sql;save=base.save
 for obj in (keeper,base,r):obj.STAGE=STAGE;obj.EVIDENCE=EVIDENCE

def rules():
 return sorted(json.loads(line) for line in sql('SELECT JSON_ARRAY(ruleset_id,rule_name,rule_value,notes) FROM rule_values ORDER BY ruleset_id,rule_name;').splitlines())
def desired(before):
 assert all(row[1]!=RULE for row in before),'New rule already exists; reconcile before proceeding'
 return sorted(before+[[1,RULE,'20',NOTES]])
def check_policy(rows):
 values={name:value for ruleset,name,value,notes in rows if ruleset==1}
 required={'AA:ExpPerPoint':'1000000','AA:PassiveExpPercent':'10','Character:AAExpMinLevel':'1','Character:MaxLevel':'50'}
 assert all(values.get(k)==v for k,v in required.items()),'AA/era baseline changed'

def database_guards():
 assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';").strip()=='InnoDB'
 assert not sql("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE EVENT_OBJECT_SCHEMA='peq' AND EVENT_OBJECT_TABLE='rule_values';").strip()
 assert sql("SELECT name FROM rule_sets WHERE ruleset_id=1;").strip()=='default'
 assert not sql("SELECT value FROM variables WHERE varname='RuleSet' AND value<>'default';").strip()
 # RuleSet is absent on the live baseline: world uses its default ruleset1.

def startup_guards():
    # These native systems are unused by the custom dungeon service. Do not silently
    # accept startup cleanup; a nonempty case requires its own scoped reconciliation.
    tables=('shared_tasks','dynamic_zones','dynamic_zone_members','dynamic_zone_lockouts')
    counts={t:int(sql('SELECT COUNT(*) FROM `'+t+'`;')) for t in tables}
    assert not any(counts.values()),('Native shared/dynamic systems need audit',counts)
    for table in ('character_expedition_lockouts','character_task_timers'):
        counts[table]=int(sql('SELECT COUNT(*) FROM '+table+' WHERE expire_time<=NOW()+INTERVAL 10 MINUTE;'))
        assert counts[table]==0,'Upcoming native cleanup: '+table
    # Audit native startup cleanup against the authenticated current schema.
    # Match the exact retained world purge predicate, including its one-hour
    # offset. Gameplay expiry alone does not delete the membership on startup.
    offset=int(sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Instances:ExpireOffsetTimeSeconds';"))
    assert offset==3600,'Native instance purge offset drift'
    counts['expiring_instances']=int(sql(f'SELECT COUNT(*) FROM instance_list WHERE never_expires=0 AND expire_at<>0 AND expire_at<=UNIX_TIMESTAMP()+600-{offset};'))
    assert counts['expiring_instances']==0,'Upcoming instance expiry needs audit'
    decay=int(sql("SELECT COALESCE((SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:CorpseDecayTime'),604800000);"))//1000
    shadow=sql("SELECT LOWER(COALESCE((SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:EnableShadowrest'),'true'));").strip() in ('true','1')
    predicate=f'time_of_death<>0 AND UNIX_TIMESTAMP()+600-UNIX_TIMESTAMP(time_of_death)>{decay}'
    if shadow:predicate+=' AND is_buried=0'
    counts['decaying_corpses']=int(sql('SELECT COUNT(*) FROM character_corpses WHERE '+predicate+';'))
    counts['instance_corpses']=int(sql('SELECT COUNT(*) FROM character_corpses c JOIN instance_list i ON i.id=c.instance_id WHERE i.never_expires=0;'))
    assert counts['decaying_corpses']==counts['instance_corpses']==0,'Upcoming native corpse cleanup needs audit'
    return counts


def forward_sql():
 # A CHECK violation aborts this session before COMMIT; closing rolls back InnoDB.
 return "START TRANSACTION; CREATE TEMPORARY TABLE aa_release_guard (ok INT CHECK(ok=1));\n"+\
  "INSERT INTO aa_release_guard SELECT COUNT(*)=0 FROM rule_values WHERE rule_name='"+RULE+"';\n"+\
  "INSERT INTO rule_values(ruleset_id,rule_name,rule_value,notes) VALUES(1,'"+RULE+"','20',CONVERT(0x"+NOTES.encode().hex()+" USING utf8mb4));\n"+\
  "INSERT INTO aa_release_guard SELECT ROW_COUNT()=1; COMMIT;"

def caches():return {n:sha(ROOT/'data/server/shared'/n) for n in ('items','spells')}
def contract():return keeper.contract()
def unchanged(p,installed=False):
 for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
 assert r.runtime()==p['runtime'] and r.public()==p['public'],'Script/client publication drift'
 assert caches()==p['caches']
 assert base.hashes((base.PUBLIC-{'rule_values'})|{'nightcap_dungeon_state'})==p['content'],'Unrelated public content drift'
 assert rules()==p['after' if installed else 'before'],'Exact rule catalog drift'
 assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'

def build_image(m):
 tag='nightcap-game:aa-level-progression-20261023-v2'
 base_tag=tag+'-base'
 r.call('docker','tag',m['base_image_id'],base_tag)
 assert r.out('docker','image','inspect','--format','{{.Id}}',base_tag).strip()==m['base_image_id']
 (STAGE/'Dockerfile').write_text('FROM '+base_tag+'\nCOPY bin/ /opt/nightcap/bin/\n')
 (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/*\n')
 assert {p.name for p in (STAGE/'bin').iterdir()}==set(m['replacement_binaries'])
 r.call('docker','build','--pull=false','--network','none','-t',tag,str(STAGE))
 assert r.out('docker','image','inspect','--format','{{.Id}}',base_tag).strip()==m['base_image_id']
 image=r.out('docker','image','inspect','--format','{{.Id}}',tag).strip()
 expected={**m['base_hashes'],**{'bin/'+n:h for n,h in m['replacement_binaries'].items()}}
 assert r.image_hashes(image)==expected
 layers=lambda v:json.loads(r.out('docker','image','inspect',v))[0]['RootFS']['Layers']
 assert layers(image)[:-1]==layers(m['base_image_id'])
 for name in m['replacement_binaries']:
  assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+name)
 r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
 return image

def preflight():
 m=manifest();assert not EVIDENCE.exists(),'Never replay an attempt'
 services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
 assert all(s['running'] and not s['oom_killed'] for s in services.values())
 assert services['game']['health']==services['db']['health']=='healthy'
 assert services['game']['image_id']==m['base_image_id']
 assert r.image_hashes(m['base_image_id'])==m['base_hashes']
 assert sha(ROOT/'data/public/channel.json')==m['client_channel_sha256'],'Signed client baseline changed'
 assert m['binaries']=={**{n:m['base_hashes']['bin/'+n] for n in NAMES},**m['replacement_binaries']}
 r.running(m['base_image_id'],{n:m['base_hashes']['bin/'+n] for n in NAMES},services['game']['restarts'])
 base.health();startup_guards();r.closed_ports();contract()
 database_guards();before=rules();check_policy(before);after=desired(before)
 assert before==m['rules_before'],'Rules changed after packaging'
 assert shutil.disk_usage(ROOT).free>=m['replacement_bytes']+750*1024**2,'Insufficient image/backup reserve'
 p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),'public':r.public(),'caches':caches(),'content':base.hashes((base.PUBLIC-{'rule_values'})|{'nightcap_dungeon_state'}),'before':before,'after':after}
 EVIDENCE.mkdir(mode=0o700);save('preflight-started.json',p)
 p['image']=build_image(m);unchanged(p)
 assert all(r.compact(s)==v for s,v in services.items())
 assert shutil.disk_usage(ROOT).free>=750*1024**2
 save('preflight.json',p);print('Paired runtime preflight passed; live gameplay unchanged.',flush=True)

def activate():
 p=read('preflight.json');m=manifest();assert p['manifest_sha256']==sha(STAGE/'manifest.json')
 assert not (EVIDENCE/'activation-started.json').exists()
 unchanged(p);startup_guards()
 assert all(r.compact(s)==v for s,v in p['services'].items())
 assert shutil.disk_usage(ROOT).free>=750*1024**2
 save('activation-started.json',{'owner_authorized_live_testing':True})
 try:
  r.compose('stop','gateway');r.compose('stop','-t','90','game')
  state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
  assert not r.state('gateway')['State']['Running']
  startup_guards();database_guards();unchanged(p)
  data=base.saved_state();save('stopped-state.json',data);save('market-before.json',base.market())
  save('backup.json',r.database_backup());assert base.saved_state()==data
  assert shutil.disk_usage(ROOT).free>=512*1024**2
  database_guards();unchanged(p)
  sql(forward_sql());save('rule-committed.json',{'rule':RULE,'ruleset_id':1,'value':'20'})
  unchanged(p,True);assert base.saved_state()==data
  expected=base.boot_state(data)
  r.select(p['image']);r.compose('up','-d','--wait','--wait-timeout','240','game')
  first=r.running(p['image'],m['binaries']);base.health();time.sleep(8)
  current=r.running(p['image'],m['binaries']);assert first['started_at']==current['started_at']
  market=base.verify_market(read('market-before.json'),current['started_at'])
  assert base.saved_state()==expected,'Closed-access player/custom state drift'
  checks=contract();unchanged(p,True);r.closed_ports()
  assert not r.state('gateway')['State']['Running']
  save('verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':market,'checks':checks,'state_tables':len(data),'caches':caches()})
  print('AA runtime and exact rule catalog verified; access remains closed.',flush=True)
 except BaseException:base.hold();raise

def open_access():
 p=read('preflight.json');a=read('verified-closed.json');m=manifest()
 assert p['manifest_sha256']==sha(STAGE/'manifest.json')
 assert not list(EVIDENCE.glob('held-*.json')) and not (EVIDENCE/'opening.json').exists()
 try:
  assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
  assert base.saved_state()==read('expected-boot-state.json')
  assert base.verify_market(read('market-before.json'),a['runtime']['started_at'])==a['market']
  unchanged(p,True);contract();base.health();r.closed_ports()
  assert shutil.disk_usage(ROOT).free>=512*1024**2
  save('opening.json',{'authorized':True})
  r.compose('up','-d','--wait','--wait-timeout','60','gateway')
  current=r.running(p['image'],m['binaries']);base.health();r.closed_ports();unchanged(p,True)
  assert current['started_at']==a['runtime']['started_at'] and r.state('gateway')['State']['Running']
  save('deployed.json',{**a,'runtime':current,'gateway_open':True,'database_restored':False,'owner_gameplay_accepted':False,'client_update_required':True})
  print('Two passive AA per level enabled; normal access restored.',flush=True)
 except BaseException:base.hold();raise

if __name__=='__main__':
 assert __debug__;os.umask(0o077);initialize()
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','open'))
 action=parser.parse_args().action
 with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (ROOT/'private/gm-maintenance.json').exists()
  assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
  {'preflight':preflight,'activate':activate,'open':open_access}[action]()
