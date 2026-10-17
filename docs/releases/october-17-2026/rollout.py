"""One-shot paired October release. Fail closed; never restore player SQL."""
import argparse,fcntl,hashlib,importlib.util,json,mmap,os,re,shutil,struct,subprocess,sys,time
from pathlib import Path,PurePosixPath

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/october-17-2026')
EVIDENCE=STAGE/'evidence'
QUEST='quests/ecommons/999820.pl'
HELPER=Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
r=None

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value):
    with (EVIDENCE/name).open('x') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def load(name):return json.loads((EVIDENCE/name).read_text())
def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert sha(HELPER)==m['runtime_helper_sha256']
    for n,h in m['files'].items():
        rel=PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in n
        p=STAGE/n;assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==h,n
    assert m['files']['bin/zone']==m['zone_sha256']
    assert m['previous_zone']=='023cb1e991de849860b1387c0a0d8db5c596fb2744e791d5a92fb9e32b6b83cd'
    return m
def sql(statement):
    args=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names','peq']
    p=subprocess.run(args,cwd=ROOT,input='SET SESSION max_session_mem_used=134217728;\n'+statement,text=True,capture_output=True,timeout=600)
    if p.returncode:raise RuntimeError('Database operation failed: '+p.stderr[-1800:])
    return p.stdout
def rules():return sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')
def expected_rules(before):
    old='1\tCharacter:DeathExpLossLevel\t10\n';assert before.count(old)==1
    assert [x for x in before.splitlines() if '\tCharacter:DeathExpLossLevel\t' in x]==[old.strip()]
    assert '1\tAA:PassiveExpPercent\t10\n' in before and '1\tZone:KillProcessOnDynamicShutdown\tfalse\n' in before
    return before.replace(old,'1\tCharacter:DeathExpLossLevel\t256\n')
def items_expected():
    columns=[line.split('\t') for line in sql("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='items' ORDER BY ordinal_position;").splitlines()]
    expressions=[]
    for name,kind in columns:
        assert re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',name)
        expressions.append('IF(stackable=1 AND stacksize<100,100,stacksize)' if name=='stacksize' else 'CAST(`'+name+'` AS DOUBLE)' if kind in ('float','double') else '`'+name+'`')
    rows=sorted(sql('SELECT SHA2(JSON_ARRAY('+','.join(expressions)+'),256) FROM items;').splitlines())
    assert len(rows)>300000 and all(re.fullmatch('[0-9a-f]{64}',v) for v in rows)
    return {'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
def content():
    tables=('spells_new','npc_types','spawn2','spawngroup','spawnentry','merchantlist','doors','zone','content_flags')
    return {t:sql('CHECKSUM TABLE `'+t+'` EXTENDED;').strip().split('\t')[-1] for t in tables}
def player():
    p=r.player_data();p.pop('rule_values');return p
def custom():
    names=sql("SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema=DATABASE() AND (TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('timers','completed_tasks','instance_list','instance_list_player','respawn_times')) ORDER BY TABLE_NAME;").splitlines()
    assert all(re.fullmatch('[A-Za-z0-9_]+',n) for n in names)
    return {n:sql('CHECKSUM TABLE `'+n+'` EXTENDED;').strip().split('\t')[-1] for n in names}
def health():r.call('docker','exec',r.state('game')['Id'],'python3','/opt/nightcap/start.py','--health')
def binaries(p):return {**{n:p['old_hashes']['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')},'zone':manifest()['zone_sha256']}
def preserved(data):
    assert player()==data['player'],'Player state drift while access closed'
    assert custom()==data['custom'],'Custom/timer state drift while access closed'
def untouched(p,installed=False,published=False):
    for s in ('db','web','tunnel'):assert r.compact(s)==p['services'][s],s
    expected=dict(p['runtime'])
    if installed:expected[QUEST]=manifest()['files'][QUEST]
    assert r.runtime()==expected,'Quest/plugin drift'
    expected=dict(p['public'])
    if published:expected['channel.json']=manifest()['client_channel_sha256']
    assert r.public()==expected,'Publication drift'
    assert rules()==(expected_rules(p['rules']) if installed else p['rules']),'Rule drift'
    assert content()==p['content'],'Unrelated content drift'
    assert items_expected()==p['items_expected'],'Unexpected item-column changes'
def expected_cache(path,plan):
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
        payload,count,maximum,current=struct.unpack_from('<IIII',b)
        assert maximum==current and len(b)==payload+8==20+4*count+1332*current
        patches=[]
        for item,old_size in plan:
            assert item<count
            index=struct.unpack_from('<I',b,16+4*item)[0];assert index<current
            start=16+4*count+1332*index
            assert struct.unpack_from('<I',b,start+440)[0]==item and b[start+799]==1
            assert struct.unpack_from('<h',b,start+802)[0]==old_size
            patches.append(start+802)
        digest=hashlib.sha256();at=0
        for pos in sorted(patches):
            digest.update(b[at:pos]);digest.update(struct.pack('<h',100));at=pos+2
        digest.update(b[at:])
        return {'sha256':digest.hexdigest(),'items':current,'changed_fields':len(patches),'item_size':1332,'stack_offset':802}
def preflight():
    m=manifest();assert not EVIDENCE.exists(),'Existing evidence: do not replay'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['health']==services['db']['health']=='healthy';health()
    old=services['game']['image_id'];hashes=r.image_hashes(old)
    assert hashes['bin/zone']==m['previous_zone'] and hashes==m['base_hashes']
    assert sha(ROOT/'data/public/channel.json')==m['previous_channel_sha256']
    before=rules();expected_rules(before)
    snapshot=sql('SELECT id,stackable,stacksize FROM items WHERE stackable=1 AND stacksize<100 ORDER BY id;')
    assert hashlib.sha256(snapshot.encode()).hexdigest()==m['stack_snapshot_sha256']
    plan=[(int(line.split('\t')[0]),int(line.split('\t')[2])) for line in snapshot.splitlines()]
    assert len(plan)==20490
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'old_image_id':old,'old_hashes':hashes,'services':services,'public':r.public(),'runtime':r.runtime(),'rules':before,'content':content(),'items_expected':items_expected(),'stack_plan':plan}
    cache=ROOT/'data/server/shared/items';p['old_cache_sha256']=sha(cache);p['expected_cache']=expected_cache(cache,plan)
    assert QUEST in p['runtime'];assert p['runtime'][QUEST]==m['previous_quest_sha256']
    r.call('docker','tag',old,'nightcap-game:oct17-base')
    (STAGE/'Dockerfile').write_text('FROM nightcap-game:oct17-base\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    r.call('docker','build','--network','none','-t','nightcap-game:october-17-2026',str(STAGE))
    image=r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:october-17-2026').strip();p['new_image_id']=image
    assert r.image_hashes(image)=={**hashes,'bin/zone':m['zone_sha256']}
    layers=lambda i:json.loads(r.out('docker','image','inspect',i))[0]['RootFS']['Layers']
    old_layers=layers(old);assert layers(image)[:-1]==old_layers
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
    untouched(p);assert all(r.compact(s)==v for s,v in services.items());health();r.closed_ports()
    EVIDENCE.mkdir(mode=0o700);save('preflight.json',p)
    print('Preflight passed; access unchanged.',flush=True)
def hold(reason):
    r.compose('stop','gateway');assert not r.state('gateway')['State']['Running']
    save('held-'+str(time.time_ns())+'.json',{'reason':reason,'database_restored':False,'gateway_open':False})
def apply_sql(p):
    # Rehearse death-loss forward/inverse in a transaction and require exact rules.
    s="UPDATE rule_values SET rule_value='256' WHERE ruleset_id=1 AND rule_name='Character:DeathExpLossLevel' AND rule_value='10';"
    t="UPDATE rule_values SET rule_value='10' WHERE ruleset_id=1 AND rule_name='Character:DeathExpLossLevel' AND rule_value='256';"
    assert sql('START TRANSACTION;'+s+'SELECT ROW_COUNT();'+t+'SELECT ROW_COUNT();ROLLBACK;').splitlines()==['1','1']
    assert rules()==p['rules']
    save('sql-attempted.json',{'stack_sql':manifest()['files']['forward-stacks.sql'],'normal_death_loss_level':256})
    sql((STAGE/'forward-stacks.sql').read_text())
    # Guard the affected count inside MariaDB before committing; no client-side
    # acknowledgment is treated as permission to replay an uncertain operation.
    sql("DELIMITER //\nBEGIN NOT ATOMIC\n DECLARE n INT; DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END; START TRANSACTION;\n"+s+" SET n=ROW_COUNT(); IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Death rule drift'; END IF; COMMIT; END //\nDELIMITER ;")
    assert sql('SELECT COUNT(*) FROM items WHERE stackable=1 AND stacksize<100;').strip()=='0'
    assert rules()==expected_rules(p['rules']) and items_expected()==p['items_expected']
    save('sql-applied.json',{'stack_definitions':20490,'normal_death_loss_level':256})
def activate():
    m=manifest();p=load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not (EVIDENCE/'activation-started.json').exists(),'Already attempted'
    assert all(r.compact(s)==v for s,v in p['services'].items());untouched(p)
    save('activation-started.json',{'authorized':True,'database_restored':False})
    try:
        r.compose('stop','gateway');start=time.monotonic();r.compose('stop','-t','90','game')
        state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state.get('OOMKilled')
        assert not r.state('gateway')['State']['Running']
        save('shutdown.json',{'seconds':time.monotonic()-start,'native_flush_confirmed':False})
        data={'player':player(),'custom':custom()};save('stopped-data.json',data)
        backup=r.database_backup();save('backup.json',backup)
        cache=ROOT/'data/server/shared/items';assert sha(cache)==p['old_cache_sha256']
        shutil.copyfile(cache,STAGE/'private-backup/items-before')
        quest=ROOT/'data/server'/QUEST;assert sha(quest)==p['runtime'][QUEST]
        shutil.copy2(quest,STAGE/'private-backup/999820.pl')
        apply_sql(p);preserved(data)
        mode=quest.stat();tmp=quest.with_name('999820.pl.oct17-pending')
        with tmp.open('xb') as f:f.write((STAGE/QUEST).read_bytes());f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode.st_mode&0o777);os.chown(tmp,mode.st_uid,mode.st_gid);os.replace(tmp,quest)
        r.select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],binaries(p));health();time.sleep(16);health()
        current=r.running(p['new_image_id'],binaries(p));assert current['started_at']==first['started_at']
        assert sha(cache)==p['expected_cache']['sha256'],'Cache differs outside planned StackSize fields'
        preserved(data);untouched(p,True);assert not r.state('gateway')['State']['Running']
        save('activated-closed.json',{'game':r.compact('game'),'runtime':current,'cache':p['expected_cache'],'backup':backup,'player_tables_preserved':len(data['player']),'custom_tables_preserved':len(data['custom'])})
        print('Server verified; gateway held for matching client publication.',flush=True)
    except BaseException:
        hold('Activation failed: preserve current state and inspect receipts before recovery');raise
def open_access():
    manifest();p=load('preflight.json');a=load('activated-closed.json')
    assert not (EVIDENCE/'opening.json').exists() and not list(EVIDENCE.glob('held-*.json'))
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        preserved(load('stopped-data.json'));untouched(p,True,True);health()
        assert sha(ROOT/'data/server/shared/items')==a['cache']['sha256']
        save('opening.json',{'matching_client_sha256':manifest()['client_channel_sha256']})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running'];health();r.closed_ports()
        result=r.running(p['new_image_id'],binaries(p));assert result['started_at']==a['runtime']['started_at']
        # Never compare/restore saved player snapshots after requesting access.
        untouched(p,True,True)
        save('activated.json',{'status':'deployed','gateway_open':True,'runtime':result,'cache':a['cache'],'client_release':2026101702,'database_restored':False,'owner_gameplay_accepted':False})
        print('Release deployed; access open.',flush=True)
    except BaseException:
        hold('Open verification uncertain: preserve subsequent activity');raise
def report():
    manifest();p=load('preflight.json');a=load('activated.json');health()
    result=r.running(p['new_image_id'],binaries(p));assert result['started_at']==a['runtime']['started_at']
    assert r.state('gateway')['State']['Running'];r.closed_ports()
    assert rules()==expected_rules(p['rules']) and sha(ROOT/'data/server/shared/items')==a['cache']['sha256']
    print(json.dumps({**a,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}}),flush=True)
def initialize():
    global r
    m=manifest();spec=importlib.util.spec_from_file_location('retained_runtime',HELPER);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
    r.STAGE=STAGE;r.EVIDENCE=EVIDENCE
if __name__=='__main__':
    assert __debug__;os.umask(0o077);initialize()
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','activate','open','report']);action=p.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access,'report':report}[action]()
