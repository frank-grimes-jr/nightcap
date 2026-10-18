"""Cooldown identity rollout. Hold access on failure; never restore player SQL."""
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,re,shutil,subprocess,time
from pathlib import Path,PurePosixPath
import capture
import cooldown_identity_migration as migration

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/cooldown-identities-20261018')
EVIDENCE=STAGE/'evidence'
PRIVATE=STAGE/'private-state'
HELPER=Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
SCRATCH='nightcap_cooldown_release_20261018'
MARKET={'nightcap_market_state','nightcap_market_offers'}
NEW_TABLES={'nightcap_cooldown_schema','nightcap_cooldown_backup_v1','nightcap_cooldown_rollback_v1'}
r=None

def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(name,value,private=False):
    with ((PRIVATE if private else EVIDENCE)/name).open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
def load(name,private=False):return json.loads(((PRIVATE if private else EVIDENCE)/name).read_text())
def sql(statement,db='peq',headers=False):
    assert db in {'peq',SCRATCH}
    args=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick']
    if not headers:args.append('--skip-column-names')
    process=subprocess.run(args+[db],cwd=ROOT,input='SET SESSION max_session_mem_used=134217728;\n'+statement,text=True,capture_output=True,timeout=600)
    if process.returncode:raise RuntimeError('Database command failed; inspect private receipts. '+process.stderr[-1200:])
    return process.stdout
def manifest():
    value=json.loads((STAGE/'manifest.json').read_text())
    assert {'bin/zone','rollout.py','capture.py','cooldown_identity_migration.py'}<=set(value['files']),'Missing executable input fingerprint'
    assert sha(HELPER)==value['runtime_helper_sha256']
    for name,digest in value['files'].items():
        rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name
        p=STAGE/name;assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==digest,name
    assert value['files']['bin/zone']==value['zone_sha256']=='d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a'
    assert value['previous_zone']=='3c1d74926cb7cff032a3ee8c48c210e37740156e7e36cc0eeddd07f847e88d1a'
    return value
def health():r.call('docker','exec',r.state('game')['Id'],'python3','/opt/nightcap/start.py','--health')
def binaries(p):return {**{n:p['old_hashes']['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')},'zone':manifest()['zone_sha256']}
def checksums(names):
    assert all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',name) for name in names)
    result={name:sql('CHECKSUM TABLE `'+name+'` EXTENDED;').strip().split('\t')[-1] for name in names}
    assert all(v.isdigit() for v in result.values());return result
def content():return checksums(['items','spells_new','aa_ability','aa_ranks','aa_rank_effects','npc_types','spawn2','spawngroup','spawnentry','merchantlist','doors','zone','content_flags','rule_values'])
def custom():
    names=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND (TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('completed_tasks','instance_list','instance_list_player','respawn_times')) ORDER BY TABLE_NAME;").splitlines()
    return checksums([name for name in names if name not in NEW_TABLES|MARKET])
def timers(db='peq',table='timers'):
    assert table in {'timers','nightcap_cooldown_backup_v1'}
    return [list(map(int,row.split('\t'))) for row in sql('SELECT char_id,type,start,duration,enable FROM '+table+' ORDER BY char_id,type;',db).splitlines()]
def item_recasts(db='peq'):return [list(map(int,row.split('\t'))) for row in sql('SELECT id,recast_type,timestamp FROM character_item_recast ORDER BY id,recast_type;',db).splitlines()]
def receipt(db='peq'):return sql('SELECT id,version,catalog_sha256 FROM nightcap_cooldown_schema ORDER BY id;',db).strip()
def validate_timers(before,after,item_rows,pairs,items,now):
    old={(row[0],row[1]):row for row in before};new={(row[0],row[1]):row for row in after}
    assert len(old)==len(before) and len(new)==len(after)
    assert all(key[1]<migration.AA for key in old),'Preexisting new namespace'
    assert {key:row for key,row in new.items() if key[1]<migration.AA}==old,'Legacy timer changed'
    bounds={};required={}
    for row in before:
        char,key,start,duration,enabled=row
        if not enabled:continue
        for previous,target in pairs:
            if key==previous:
                k=(char,target);bounds[k]=max(bounds.get(k,0),start+duration)
                if start+duration>now:required[k]=max(required.get(k,0),start+duration)
    for char,item,stamp in item_rows:
        if item in items:
            k=(char,migration.ITEM+item);bounds[k]=max(bounds.get(k,0),stamp)
            if stamp>now:required[k]=max(required.get(k,0),stamp)
    for key,deadline in required.items():
        assert key in new and new[key][4]==1 and new[key][2]+new[key][3]>=deadline,'Deadline shortened/missing'
    for key,row in new.items():
        if key[1]>=migration.AA:
            assert key in bounds and row[4]==1 and row[2]+row[3]<=bounds[key],'Unexpected successor/deadline'
    return len(new)-len(old)
def verify_migration(catalog,digest,before,item_rows,db='peq'):
    assert receipt(db)=='1\t1\t'+digest,'Receipt mismatch'
    assert timers(db,'nightcap_cooldown_backup_v1')==before,'Migration backup mismatch'
    assert item_recasts(db)==item_rows,'Item timestamp records changed'
    pairs,items=migration.mappings(catalog)
    return validate_timers(before,timers(db),item_rows,pairs,set(items),int(sql('SELECT UNIX_TIMESTAMP();',db)))
def stopped():
    assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
def untouched(p):
    for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
    assert r.runtime()==p['runtime'] and r.public()==p['public'],'Quest/client publication drift'
    assert content()==p['content'],'Unrelated catalog/rule drift'
    assert sha(ROOT/'data/server/shared/items')==p['cache_sha256'],'Item cache changed'
def preserved(data):
    assert r.player_data()==data['player'],'Player data drift while access closed'
    assert custom()==data['custom'],'Unrelated custom state drift'
def market_state():return sql('SELECT id,enabled,epoch,expansion,loot_multiplier,buy_cost_mod,rotated_at FROM nightcap_market_state;').strip().split('\t')
def validate_market_state(before,after,started):
    assert len(before)==len(after)==7 and before[:2]==after[:2]==['1','1']
    assert int(after[2])==int(before[2])+1 and before[3:6]==after[3:6]
    stamp=datetime.datetime.fromisoformat(after[6]).replace(tzinfo=datetime.timezone.utc)
    start=datetime.datetime.fromisoformat(started.replace('Z','+00:00'))
    assert 0<=(stamp-start).total_seconds()<=60,'Unexpected market rotation time'
def verify_market(before,started):
    after=market_state();validate_market_state(before,after,started)
    epoch=int(after[2])
    expected=int(sql("SELECT SUM(IF(kind='find',1,2)) FROM nightcap_market_actors;"))
    assert sql('SELECT epoch,COUNT(*) FROM nightcap_market_offers GROUP BY epoch;').strip()==f'{epoch}\t{expected}'
    invalid=sql(f"""SELECT COUNT(*) FROM nightcap_market_offers o
LEFT JOIN nightcap_market_actors a ON a.npc_id=o.npc_id LEFT JOIN nightcap_market_catalog c ON c.item_id=o.item_id LEFT JOIN items i ON i.id=o.item_id
WHERE a.npc_id IS NULL OR c.item_id IS NULL OR i.id IS NULL OR o.epoch<>{epoch} OR o.remaining<>1
OR o.zone_id<>a.zone_id OR o.kind<>a.kind OR o.price_cp<=0
OR o.price_cp<>CASE o.kind WHEN 'find' THEN c.find_cp WHEN 'sell' THEN c.sell_cp ELSE c.buy_cp END
OR c.pool<>IF(o.kind='find','find','tunnel') OR c.min_expansion>{int(after[3])} OR (c.max_expansion>=0 AND c.max_expansion<{int(after[3])})
OR i.nodrop=0 OR i.norent=0 OR i.stackable<>0 OR i.maxcharges<>0 OR i.itemclass<>0 OR i.questitemflag<>0 OR i.attuneable<>0
OR c.buy_cp>=c.sell_cp OR c.buy_cp>=c.find_cp
OR EXISTS(SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid WHERE m.item=o.item_id AND n.id=o.npc_id);
SELECT COUNT(*) FROM (SELECT npc_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY npc_id,kind HAVING n<>IF(kind='find',1,2)) x;
SELECT COUNT(*) FROM (SELECT item_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY item_id,kind HAVING n>IF(kind='sell',3,2)) x;""").splitlines()
    assert invalid==['0','0','0'];return {'before':before,'after':after,'offers':expected}
def rehearse(catalog,digest,before,item_rows,forward,reverse):
    assert sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='"+SCRATCH+"';").strip()=='0'
    sql('CREATE DATABASE '+SCRATCH+';');created=True
    try:
        for table,columns in [('aa_ability','id,first_rank_id'),('aa_ranks','id,spell,spell_type,next_id'),('items','id,recasttype,clickeffect,recastdelay'),('spells_new','id,IsDiscipline,EndurTimerIndex')]:
            sql(f'CREATE TABLE {SCRATCH}.{table} AS SELECT {columns} FROM peq.{table};')
        for table in ['timers','character_item_recast']:
            sql(f'CREATE TABLE {SCRATCH}.{table} LIKE peq.{table}; INSERT INTO {SCRATCH}.{table} SELECT * FROM peq.{table};')
        sql(forward,SCRATCH);added=verify_migration(catalog,digest,before,item_rows,SCRATCH)
        sql(reverse,SCRATCH)
        assert not receipt(SCRATCH) and all(row[1]<migration.AA for row in timers(SCRATCH))
        assert item_recasts(SCRATCH)==item_rows
        now=int(sql('SELECT UNIX_TIMESTAMP();',SCRATCH));after={(r[0],r[1]):r for r in timers(SCRATCH)}
        for row in before:
            key=(row[0],row[1]);assert key in after
            if row[4] and row[2]+row[3]>now:assert after[key][4] and after[key][2]+after[key][3]>=row[2]+row[3]
        save('stopped-migration-rehearsal.json',{'passed':True,'catalog_sha256':digest,'new_timer_rows':added,'live_sql_modified':False})
    finally:
        if created:sql('DROP DATABASE '+SCRATCH+';')
    assert sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='"+SCRATCH+"';").strip()=='0'
def hold(reason):
    errors={};states={}
    for service,args in [('gateway',('stop','gateway')),('game',('stop','-t','90','game'))]:
        try:r.compose(*args)
        except BaseException as error:errors[service]=type(error).__name__
    for service in ('gateway','game'):
        try:states[service]=r.state(service)['State']['Running']
        except BaseException as error:states[service]=None;errors[service+'-verification']=type(error).__name__
    save('held-'+str(time.time_ns())+'.json',{'reason':reason,'running':states,'both_stopped':all(v is False for v in states.values()),'stop_errors':errors,'database_restored':False})
def preflight():
    m=manifest();assert not EVIDENCE.exists(),'Existing attempt; inspect before proceeding'
    assert shutil.disk_usage(ROOT).free>=6*1024**3,'Insufficient release/backup headroom'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values());health();r.closed_ports()
    assert services['game']['health']==services['db']['health']=='healthy'
    assert sql("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME IN ('nightcap_cooldown_schema','nightcap_cooldown_backup_v1','nightcap_cooldown_rollback_v1');").strip()=='0'
    assert sql('SELECT COUNT(*) FROM timers WHERE type>=1048576;').strip()=='0'
    old=services['game']['image_id'];hashes=r.image_hashes(old)
    assert hashes['bin/zone']==m['previous_zone'] and hashes==m['base_hashes']
    assert sha(ROOT/'data/public/channel.json')==m['client_channel_sha256']
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'old_image_id':old,'old_hashes':hashes,'services':services,'public':r.public(),'runtime':r.runtime(),'content':content(),'cache_sha256':sha(ROOT/'data/server/shared/items')}
    r.running(old,{n:hashes['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')},expected_restarts=services['game']['restarts'])
    r.call('docker','tag',old,'nightcap-game:cooldown-identities-base')
    (STAGE/'Dockerfile').write_text('FROM nightcap-game:cooldown-identities-base\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--network','none','-t','nightcap-game:cooldown-identities-20261018',str(STAGE))
    image=r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:cooldown-identities-20261018').strip();p['new_image_id']=image
    assert r.image_hashes(image)=={**hashes,'bin/zone':m['zone_sha256']}
    layers=lambda i:json.loads(r.out('docker','image','inspect',i))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(old)
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    for checked in (image,old):
        r.call('docker','run','--rm','--network','none','--entrypoint','python3',checked,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',checked,'--nightcap-crypto-self-test')
    untouched(p);assert all(r.compact(s)==state for s,state in services.items())
    EVIDENCE.mkdir(mode=0o700);PRIVATE.mkdir(mode=0o700);save('preflight.json',p)
    print('Preflight passed; production access unchanged.',flush=True)
def activate():
    manifest();p=load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not (EVIDENCE/'activation-started.json').exists(),'Attempt cannot be replayed'
    assert all(r.compact(s)==state for s,state in p['services'].items());untouched(p)
    assert shutil.disk_usage(ROOT).free>=4*1024**3
    save('activation-started.json',{'owner_authorized':True,'database_restored':False})
    try:
        r.compose('stop','gateway');start=time.monotonic();r.compose('stop','-t','90','game');stopped()
        state=r.state('game')['State'];assert state['ExitCode']==0 and not state.get('OOMKilled')
        save('shutdown.json',{'seconds':time.monotonic()-start,'native_flush_confirmed':False})
        data={'player':r.player_data(),'custom':custom()};save('stopped-data.json',data,True)
        before=timers();item_rows=item_recasts();market=market_state()
        save('stopped-timers.json',before,True);save('stopped-item-recasts.json',item_rows,True);save('market-before.json',market)
        backup=r.database_backup();save('backup.json',backup)
        catalog=capture.capture(sql);save('catalog.json',catalog,True)
        digest=sha(PRIVATE/'catalog.json');forward=migration.sql(catalog,digest);reverse=migration.sql(catalog,digest,True)
        for name,source in [('forward.sql',forward),('rollback.sql',reverse)]:
            with (PRIVATE/name).open('x') as stream:stream.write(source)
        save('migration-inputs.json',{'catalog_sha256':digest,'forward_sha256':sha(PRIVATE/'forward.sql'),'rollback_sha256':sha(PRIVATE/'rollback.sql'),'mapping_pairs':len(migration.mappings(catalog)[0])})
        rehearse(catalog,digest,before,item_rows,forward,reverse);preserved(data);untouched(p);stopped()
        save('migration-attempted.json',load('migration-inputs.json'))
        sql(forward) # One invocation only; lost acknowledgment holds both services.
        added=verify_migration(catalog,digest,before,item_rows);preserved(data);untouched(p)
        save('migration-applied.json',{'catalog_sha256':digest,'legacy_rows_preserved':len(before),'new_timer_rows':added,'item_records_preserved':len(item_rows)})
        r.select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],binaries(p));health();time.sleep(16);health()
        current=r.running(p['new_image_id'],binaries(p));assert first['started_at']==current['started_at']
        rotation=verify_market(market,current['started_at']);preserved(data);untouched(p)
        verify_migration(catalog,digest,before,item_rows)
        assert not r.state('gateway')['State']['Running']
        save('verified-closed.json',{'runtime':current,'game':r.compact('game'),'market_rotation':rotation,'cache_sha256':p['cache_sha256'],'player_tables_preserved':len(data['player']),'custom_tables_preserved':len(data['custom'])})
        print('New server and migration verified; gateway remains closed.',flush=True)
    except BaseException:
        hold('Activation failed/uncertain. Inspect receipt; never replay SQL or start old uint16 code.');raise
def open_access():
    manifest();p=load('preflight.json');a=load('verified-closed.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json'),'Release inputs changed after preflight'
    assert not (EVIDENCE/'opening.json').exists() and not list(EVIDENCE.glob('held-*.json'))
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        catalog=load('catalog.json',True);digest=load('migration-inputs.json')['catalog_sha256']
        verify_migration(catalog,digest,load('stopped-timers.json',True),load('stopped-item-recasts.json',True))
        preserved(load('stopped-data.json',True));untouched(p);health()
        assert verify_market(load('market-before.json'),a['runtime']['started_at'])==a['market_rotation']
        save('opening.json',{'catalog_sha256':digest,'client_channel_sha256':manifest()['client_channel_sha256']})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running'];health();r.closed_ports()
        current=r.running(p['new_image_id'],binaries(p));assert current['started_at']==a['runtime']['started_at']
        untouched(p) # No saved-player comparisons after access may have opened.
        save('activated.json',{'status':'deployed','gateway_open':True,'runtime':current,'migration':load('migration-applied.json'),'market_rotation':a['market_rotation'],'cache_sha256':p['cache_sha256'],'client_release':2026101702,'database_restored':False,'owner_gameplay_accepted':False,'player_tables_preserved':a['player_tables_preserved'],'custom_tables_preserved':a['custom_tables_preserved']})
        print('Cooldown correction deployed; access open.',flush=True)
    except BaseException:
        hold('Opening failed/uncertain. Preserve subsequent activity; inspect receipts.');raise
def report():
    manifest();p=load('preflight.json');a=load('activated.json');health()
    assert p['manifest_sha256']==sha(STAGE/'manifest.json'),'Release inputs changed after preflight'
    current=r.running(p['new_image_id'],binaries(p));assert current['started_at']==a['runtime']['started_at']
    assert r.state('gateway')['State']['Running'];r.closed_ports();untouched(p)
    assert receipt()=='1\t1\t'+a['migration']['catalog_sha256']
    print(json.dumps({**a,'runtime':current,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}}))
def initialize():
    global r
    manifest();spec=importlib.util.spec_from_file_location('retained_runtime',HELPER);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
    r.STAGE=STAGE;r.EVIDENCE=EVIDENCE;r.sql=sql
if __name__=='__main__':
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','open','report']);action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access,'report':report}[action]()
