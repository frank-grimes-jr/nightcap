"""Combined Classic dungeon release. Owner-authorized live QA; fail closed.

No automatic player restoration or down-migration. After new runs/rewards exist,
recovery must retain this compatible catalog. Receipts are private on the host.
"""
import argparse, datetime, fcntl, hashlib, importlib.util, json, mmap, os
from pathlib import Path, PurePosixPath
import re, secrets, shutil, struct, subprocess, time, uuid

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/classic-dungeons-rewards-20261022')
EVIDENCE = STAGE/'evidence'
HELPER = Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
PUBLIC = {'items','spells_new','npc_types','spawn2','spawngroup','spawnentry','tasks',
          'task_activities','tasksets','nightcap_dungeon_spawns','doors','merchantlist',
          'zone','content_flags','faction_list','aa_ability','aa_ranks','aa_rank_effects',
          'rule_sets','rule_values','variables','logsys_categories'}
EXTRA_STATE = {'account','inventory','sharedbank','guild_bank','keyring','quest_globals',
               'timers','completed_tasks','instance_list','instance_list_player',
               'respawn_times','zone_state_spawns','guilds','guild_members','pets',
               'dynamic_zones','dynamic_zone_members','dynamic_zone_lockouts','data_buckets','spawn_condition_values','spawn2_disabled'}
NAMES = {'world','zone','shared_memory','loginserver','ucs'}
r = None

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def save(name, value):
    with (EVIDENCE/name).open('x') as f:
        json.dump(value,f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    fd=os.open(EVIDENCE,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def load(name): return json.loads((EVIDENCE/name).read_text())

def sql(statement, database='peq'):
    assert database=='peq' or re.fullmatch('nightcap_classic_stage_[0-9a-f]{12}',database)
    result=subprocess.run(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick',
        '--skip-column-names','--default-character-set=utf8mb4',database],cwd=ROOT,
        input='SET SESSION max_session_mem_used=134217728;\n'+statement,
        text=True,capture_output=True,timeout=900)
    if result.returncode:
        detail='Private credentials withheld' if 'IDENTIFIED BY' in statement else result.stderr[-1600:]
        raise RuntimeError('Database operation failed: '+detail)
    return result.stdout

def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert sha(HELPER)==m['runtime_helper_sha256']
    assert set(m['binaries'])==NAMES
    for name,digest in m['files'].items():
        p=PurePosixPath(name); target=STAGE/name
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
        assert target.resolve().is_relative_to(STAGE) and not target.is_symlink()
        assert sha(target)==digest,name
    return m

def hashes(tables,database='peq'):
    assert all(re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*',t) for t in tables)
    result={t:sql('CHECKSUM TABLE `'+t+'` EXTENDED;',database).strip().split('\t')[-1] for t in sorted(tables)}
    assert all(v.isdigit() for v in result.values())
    return result

def state_tables():
    tables=sql('SHOW TABLES;').splitlines()
    return sorted(t for t in tables if (t.startswith(('character_','nightcap_','shared_task','completed_shared_task')) or t in EXTRA_STATE)
                  and t not in {'nightcap_market_state','nightcap_market_offers','nightcap_dungeon_state','nightcap_dungeon_spawns'})

def zone_rows(where=''):
    columns=[line.split('\t')[0] for line in sql('SHOW COLUMNS FROM zone_state_spawns;').splitlines()]
    assert all(re.fullmatch('[a-z_][a-z_0-9]*',c) for c in columns)
    expression='JSON_ARRAY('+','.join('`'+c+'`' for c in columns)+')'
    return sorted(sql('SELECT SHA2('+expression+',256) FROM zone_state_spawns '+where+';').splitlines())

def row_fingerprint(rows):
    return {'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}

def saved_state():
    return {**hashes(set(state_tables())-{'zone_state_spawns'}),'zone_state_spawns':row_fingerprint(zone_rows())}

def boot_state(before):
    # Model the exact retained world TTL deletion. Reject other cleanup candidates
    # and near-boundary timestamps rather than broadly ignoring cache/instance drift.
    assert sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:StateSaveClearDays';").strip()=='7'
    invalid=sql("SELECT zone_id,instance_id FROM zone_state_spawns GROUP BY zone_id,instance_id HAVING COUNT(*)=SUM(CASE WHEN hp=0 AND mana=0 AND endurance=0 AND (loot_data IS NULL OR loot_data='') AND (entity_variables IS NULL OR entity_variables='') AND (buffs IS NULL OR buffs='') THEN 1 ELSE 0 END);")
    assert not invalid.strip(),'Invalid saved-state groups require explicit audit before boot'
    cutoff=int(sql('SELECT UNIX_TIMESTAMP(NOW() - INTERVAL 7 DAY);'))
    assert sql(f'SELECT COUNT(*) FROM zone_state_spawns WHERE UNIX_TIMESTAMP(created_at) BETWEEN {cutoff} AND {cutoff+600};').strip()=='0'
    where=f'WHERE UNIX_TIMESTAMP(created_at)<{cutoff}'
    assert sql('SELECT COUNT(*) FROM zone_state_spawns '+where+' AND is_corpse<>0;').strip()=='0','Expired corpse cache requires explicit audit'
    expired=zone_rows(where)
    retained=zone_rows(f'WHERE UNIX_TIMESTAMP(created_at)>={cutoff} OR created_at IS NULL')
    assert row_fingerprint(sorted(expired+retained))==before['zone_state_spawns']
    expected={**before,'zone_state_spawns':row_fingerprint(retained)}
    save('native-expiry.json',{'cutoff_epoch':cutoff,'expired_noncorpse_rows':len(expired),
         'expired_hashes':expired,'native_rule_days':7,'boundary_window_seconds':600})
    save('expected-boot-state.json',expected)
    return expected

def contract(database='peq'):
    result={}
    for family,checks in json.loads((STAGE/'runtime-contract.json').read_text()).items():
        values=sql(';\n'.join(c['sql'] for c in checks)+';',database).splitlines()
        assert len(values)==len(checks),(family,len(values))
        failures=[c['label'] for c,v in zip(checks,values) if v!=c['expected']]
        assert not failures,(family,failures)
        result[family]=len(checks)
    assert result=={'schema':39,'content':497}
    return result

def health(): r.call('docker','exec',r.state('game')['Id'],'python3','/opt/nightcap/start.py','--health')

def startup_guards():
    # These native systems are unused by the custom dungeon service. Do not silently
    # accept startup cleanup; a nonempty case requires its own scoped reconciliation.
    tables=('shared_tasks','dynamic_zones','dynamic_zone_members','dynamic_zone_lockouts')
    counts={t:int(sql('SELECT COUNT(*) FROM `'+t+'`;')) for t in tables}
    assert not any(counts.values()),('Native shared/dynamic systems need audit',counts)
    for table in ('character_expedition_lockouts','character_task_timers'):
        counts[table]=int(sql('SELECT COUNT(*) FROM '+table+' WHERE expire_time<=NOW()+INTERVAL 10 MINUTE;'))
        assert counts[table]==0,'Upcoming native cleanup: '+table
    # Bound both native instance expiry conventions without assuming a newer schema.
    counts['expiring_instances']=int(sql('SELECT COUNT(*) FROM instance_list WHERE never_expires=0 AND start_time+duration<=UNIX_TIMESTAMP()+600;'))
    assert counts['expiring_instances']==0,'Upcoming instance expiry needs audit'
    decay=int(sql("SELECT COALESCE((SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:CorpseDecayTime'),604800000);"))//1000
    shadow=sql("SELECT LOWER(COALESCE((SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:EnableShadowrest'),'true'));").strip() in ('true','1')
    predicate=f'time_of_death<>0 AND UNIX_TIMESTAMP()+600-UNIX_TIMESTAMP(time_of_death)>{decay}'
    if shadow:predicate+=' AND is_buried=0'
    counts['decaying_corpses']=int(sql('SELECT COUNT(*) FROM character_corpses WHERE '+predicate+';'))
    counts['instance_corpses']=int(sql('SELECT COUNT(*) FROM character_corpses c JOIN instance_list i ON i.id=c.instance_id WHERE i.never_expires=0;'))
    assert counts['decaying_corpses']==counts['instance_corpses']==0,'Upcoming native corpse cleanup needs audit'
    return counts

def unchanged(p,installed=False):
    for service in ('db','web','tunnel'): assert r.compact(service)==p['services'][service],service
    runtime=dict(p['runtime'])
    if installed: runtime.update({name:manifest()['files'][name] for name in manifest()['scripts']})
    assert r.runtime()==runtime,'Unrelated script drift'
    assert r.public()==p['public'],'Client/publication drift'
    assert hashes(PUBLIC)==p['after' if installed else 'before'],'Full content drift'

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
                result[item]=value if 960000<=item<960330 else hashlib.sha256(value).hexdigest()
    assert len(result)==current
    return result

def compare_cache(before,after):
    assert set(after)-set(before)==set(range(960330,960414)) and set(before)<=set(after)
    expected=set(json.loads((STAGE/'magic-only-ids.json').read_text())); changed=set()
    for item,value in before.items():
        if value==after[item]: continue
        assert item in expected,item
        differences=[(i,a,b) for i,(a,b) in enumerate(zip(value,after[item])) if a!=b]
        assert len(differences)==1 and differences[0][1:]==(0,1),(item,differences)
        changed.add(item)
    assert changed==expected and len(changed)==220
    return {'existing_records':len(before),'unchanged':len(before)-220,'magic_only':220,'added':84}

def cache_contract(image,path):
    result=json.loads(r.out('docker','run','--rm','--network','none','--user','0',
        '-v',str(STAGE)+':/stage:ro','-v',str(path)+':/items:ro',
        '--entrypoint','/stage/cache_check',image,'/items'))
    assert result=={'items':414,'clicks':6,'drift_rejections':888,'item_bytes':1332}
    return result

def build_image(m):
    base='nightcap-game:classic-dungeons-rewards-20261022-base'; target='nightcap-game:classic-dungeons-rewards-20261022'
    r.call('docker','tag',m['base_image_id'],base)
    (STAGE/'Dockerfile').write_text('FROM '+base+'\nCOPY bin/ /opt/nightcap/bin/\n')
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

def rehearsal(p):
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    assert available>=3*1024**3,'Insufficient memory for capped isolated rehearsal'
    size=int(sql("SELECT COALESCE(SUM(data_length+index_length),0) FROM information_schema.tables WHERE table_schema='peq' AND table_name IN ("+','.join("'"+n+"'" for n in PUBLIC)+');'))
    needed=int(size*1.3)+(ROOT/'data/server/shared/items').stat().st_size+512*1024**2
    assert shutil.disk_usage(ROOT).free>=needed,'Insufficient measured clone/cache reserve'
    database='nightcap_classic_stage_'+uuid.uuid4().hex[:12]
    username='ncr_'+uuid.uuid4().hex[:12]; password=secrets.token_hex(24)
    runtime=STAGE/'rehearsal-runtime'; runtime.mkdir(mode=0o700)
    (runtime/'shared').mkdir(); (runtime/'logs').mkdir(); cfg=runtime/'eqemu_config.json'
    created_user=False; created_db=False
    try:
        sql('CREATE DATABASE `'+database+'`;'); created_db=True
        # Preserve all actual schemas, but copy only public definitions. Live migrations
        # independently reject references in private tables while all writers are stopped.
        names=sql('SHOW TABLES;').splitlines()
        for t in names:
            assert re.fullmatch('[a-zA-Z_][a-zA-Z_0-9]*',t)
            sql(f'CREATE TABLE `{database}`.`{t}` LIKE peq.`{t}`;')
        copy=PUBLIC|{'nightcap_dungeon_state'}
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(
            f'INSERT INTO `{t}` SELECT * FROM peq.`{t}`;' for t in sorted(copy))+'\nCOMMIT;',database)
        assert hashes(PUBLIC,database)==p['before']
        sql(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}';"); created_user=True
        sql(f"GRANT ALL ON `{database}`.* TO '{username}'@'%';")
        config=json.loads((ROOT/'private/eqemu_config.json').read_text())
        connection=config['server']['database']; connection.update(db=database,username=username,password=password)
        config['server']['content_database']=dict(connection)
        config['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(config));cfg.chmod(0o600)
        networks=list(r.state('db')['NetworkSettings']['Networks']);assert len(networks)==1
        def loader(image,name):
            assert shutil.disk_usage(ROOT).free>=512*1024**2+(0 if (runtime/'shared/items').exists() else (ROOT/'data/server/shared/items').stat().st_size)
            with (runtime/(name+'.log')).open('w') as log:
                result=subprocess.run(['docker','run','--rm','--memory','1536m','--memory-swap','1536m',
                    '--network',networks[0],'--user','0',
                    '-v',str(runtime)+':/runtime','--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',
                    image,'items'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=240)
            assert result.returncode==0,'Isolated loader failed; inspect private log'
            assert not re.search(r'Unknown column|SQL syntax|Unable to connect|doesn.t exist',(runtime/(name+'.log')).read_text())
        loader(manifest()['base_image_id'],'before')
        before=records(runtime/'shared/items')
        assert before==records(ROOT/'data/server/shared/items'),'Live cache differs from baseline fresh loader'
        sql('UPDATE nightcap_dungeon_state SET enabled=0 WHERE id=1;',database)
        for component in manifest()['components']: sql((STAGE/component).read_text(),database)
        checks=contract(database);p['after']=hashes(PUBLIC,database)
        loader(p['new_image_id'],'after')
        cache=cache_contract(p['new_image_id'],runtime/'shared/items')
        comparison=compare_cache(before,records(runtime/'shared/items'))
        save('rehearsal.json',{'checks':checks,'cache':cache,'comparison':comparison,'database':database,
             'public_content_only':True,'player_references_checked_by_stopped_live_migrations':True})
    finally:
        cfg.unlink(missing_ok=True)
        if created_user: sql(f"DROP USER '{username}'@'%';")
        if created_db: sql('DROP DATABASE `'+database+'`;')
        (runtime/'shared/items').unlink(missing_ok=True)

def script_guards(m):
    live=ROOT/'data/server'
    for name,before in m['script_preimages'].items():
        path=live/name
        assert (sha(path) if path.exists() else None)==before,name
        if name.startswith('quests/'):
            assert not path.with_suffix('.pl').exists(),'Competing Perl NPC script: '+name
    for name in m['absent_quest_shadows']: assert not (live/name).exists(),name

def preflight():
    m=manifest();assert not EVIDENCE.exists(),'Never replay an existing attempt'
    assert shutil.disk_usage(ROOT).free>=2300*1024**2,'Insufficient image/rehearsal headroom'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert sha(ROOT/'data/public/channel.json')==m['client_channel_sha256']
    script_guards(m);startup_guards();health();r.closed_ports()
    r.running(m['base_image_id'],{n:m['base_hashes']['bin/'+n] for n in NAMES},services['game']['restarts'])
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
       'public':r.public(),'before':hashes(PUBLIC)}
    EVIDENCE.mkdir(mode=0o700);save('preflight-started.json',p)
    p['new_image_id']=build_image(m);save('candidate-image.json',{'image':p['new_image_id']})
    assert shutil.disk_usage(ROOT).free>=1400*1024**2,'Insufficient clone/cache headroom'
    rehearsal(p);unchanged(p)
    assert all(r.compact(s)==v for s,v in services.items())
    assert shutil.disk_usage(ROOT).free>=800*1024**2
    save('preflight.json',p);print('Preflight and fresh production-content rehearsal passed.',flush=True)

def hold():
    errors=[]
    for args in [('stop','gateway'),('stop','-t','90','game')]:
        try:r.compose(*args)
        except BaseException as e:errors.append(type(e).__name__)
    save('held-'+str(time.time_ns())+'.json',{'errors':errors,'database_restored':False})

def install_scripts(m):
    previous=STAGE/'previous-scripts';previous.mkdir(mode=0o700)
    script_guards(m)
    for name in m['scripts']:
        path=ROOT/'data/server'/name; source=STAGE/name
        if path.exists():
            backup=previous/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
            stat=path.stat(); mode,uid,gid=stat.st_mode,stat.st_uid,stat.st_gid
        else:
            stat=path.parent.stat();mode,uid,gid=0o644,stat.st_uid,stat.st_gid
        tmp=path.with_name(path.name+'.dungeon-'+str(time.time_ns()))
        with tmp.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.chown(tmp,uid,gid);os.replace(tmp,path)

def toggle(before,after):
    assert (before,after) in ((1,0),(0,1))
    value=sql(f'UPDATE nightcap_dungeon_state SET enabled={after} WHERE id=1 AND revision=2026101601 AND enabled={before}; SELECT ROW_COUNT();').strip()
    assert value=='1','Unexpected dungeon activation state'

def activate():
    m=manifest();p=load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not (EVIDENCE/'activation-started.json').exists()
    unchanged(p);script_guards(m);startup_guards()
    assert all(r.compact(s)==v for s,v in p['services'].items())
    assert shutil.disk_usage(ROOT).free>=800*1024**2
    save('activation-started.json',{'owner_authorized_live_testing':True})
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
        assert not r.state('gateway')['State']['Running']
        save('startup-cleanup-guards.json',startup_guards())
        data=saved_state();save('stopped-state.json',data);save('market-before.json',market())
        save('backup.json',r.database_backup())
        assert saved_state()==data;unchanged(p)
        assert shutil.disk_usage(ROOT).free>=600*1024**2
        before_cache=records(ROOT/'data/server/shared/items');spell_sha=sha(ROOT/'data/server/shared/spells')
        toggle(1,0)
        for component in m['components']:
            name=Path(component).stem
            save(name+'-attempted.json',{'sha256':m['files'][component]})
            sql((STAGE/component).read_text());save(name+'-committed.json',{'success':True})
        checks=contract();assert hashes(PUBLIC)==p['after'];assert saved_state()==data
        install_scripts(m);unchanged(p,True)
        r.select(p['new_image_id'])
        r.compose('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')
        cache=cache_contract(p['new_image_id'],ROOT/'data/server/shared/items')
        comparison=compare_cache(before_cache,records(ROOT/'data/server/shared/items'))
        caches={n:sha(ROOT/'data/server/shared'/n) for n in ('items','spells')}
        assert caches['spells']==spell_sha
        save('generated-cache.json',{'hashes':caches,'contract':cache,'comparison':comparison})
        assert saved_state()==data;expected_state=boot_state(data);toggle(0,1)
        r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],m['binaries']);health();time.sleep(8)
        current=r.running(p['new_image_id'],m['binaries']);assert first['started_at']==current['started_at']
        rotation=verify_market(load('market-before.json'),current['started_at'])
        current_state=saved_state();save('boot-state.json',current_state)
        assert current_state==expected_state, 'Closed-access state drift outside authenticated native expiry'
        unchanged(p,True);contract();r.closed_ports()
        assert {n:sha(ROOT/'data/server/shared'/n) for n in caches}==caches
        assert not r.state('gateway')['State']['Running'] and shutil.disk_usage(ROOT).free>=512*1024**2
        save('verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'checks':checks,'cache':cache,'state_tables':len(data),'caches':caches})
        print('New runtime verified; gateway remains closed until final checks.',flush=True)
    except BaseException:hold();raise

def open_access():
    m=manifest();p=load('preflight.json');a=load('verified-closed.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not list(EVIDENCE.glob('held-*.json')) and not (EVIDENCE/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        assert saved_state()==load('expected-boot-state.json')
        assert verify_market(load('market-before.json'),a['runtime']['started_at'])==a['market']
        assert {n:sha(ROOT/'data/server/shared'/n) for n in a['caches']}==a['caches']
        unchanged(p,True);contract();health();r.closed_ports()
        assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
        assert shutil.disk_usage(ROOT).free>=512*1024**2
        save('opening.json',{'authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(p['new_image_id'],m['binaries']);health();r.closed_ports()
        assert current['started_at']==a['runtime']['started_at'] and r.state('gateway')['State']['Running']
        unchanged(p,True)
        save('deployed.json',{**a,'runtime':current,'gateway_open':True,'database_restored':False,
            'owner_gameplay_accepted':False,'client_channel_sha256':m['client_channel_sha256']})
        print('Dungeon options and rewards deployed; access open.',flush=True)
    except BaseException:hold();raise

def initialize():
    global r
    manifest();spec=importlib.util.spec_from_file_location('retained_runtime',HELPER)
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
    r.STAGE=STAGE;r.EVIDENCE=EVIDENCE;r.sql=sql

# market()/verify_market() are copied exactly from the reviewed October21
# operator by prepare_local.py and pin the native once-per-startup rotation.

if __name__=='__main__':
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','open'])
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access}[action]()
