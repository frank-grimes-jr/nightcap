"""One-shot Last Lantern release. Private evidence; never restore player snapshots.

Preflight changes only an isolated public-content schema/image/cache. Activation
closes ingress, drains auth, stops cleanly, backs up, installs additive content,
and verifies the matching native/cache pair. Failures hold admissions closed.
After installation recover forward with this personal-item policy retained.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,re,shutil,subprocess,time
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/last-lantern-20261107-v4')
EVIDENCE=STAGE/'evidence'
TAG='nightcap-game:last-lantern-20261107-v4'
DATABASE='nightcap_dungeon_stage_1107a11ce003'
NEW_TABLES={'nightcap_epic05_control','nightcap_epic05_state','nightcap_lantern_control',
 'nightcap_lantern_slots','nightcap_lantern_refits','nightcap_lantern_runs',
 'nightcap_lantern_members','nightcap_lantern_memorials'}
SCOPES={'items':'id=900501 OR id BETWEEN 964000 AND 964127','spells_new':'id BETWEEN 42800 AND 42805',
 'tasks':'id BETWEEN 9500 AND 9515','task_activities':'taskid BETWEEN 9500 AND 9515',
 'npc_types':'id BETWEEN 998900 AND 998939','spawngroup':'id BETWEEN 998900 AND 998905',
 'spawnentry':'spawngroupID BETWEEN 998900 AND 998905','spawn2':'id BETWEEN 9113000 AND 9113005',
 'titles':'id=995501'}

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def read(path):return json.loads(path.read_text())

def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def initialize():
    global m,prior,p,r,base,startup,market,sql,h
    m=read(STAGE/'manifest.json')
    assert m['owner_authorization']=='Push it to server and main. Ensure this is posted in the client notes'
    for n,pin in m['files'].items():
        f=STAGE/n;assert not f.is_symlink() and f.resolve().is_relative_to(STAGE) and sha(f)==pin,n
    path=Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1/rollout.py')
    assert sha(path)==m['prior_operator_sha256']
    spec=importlib.util.spec_from_file_location('prior_dungeon',path)
    prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior);prior.initialize()
    p=prior.p;r=p.r;base=p.base;startup=p.startup;market=p.market_ops;sql=p.sql;h=p.h
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert read(STAGE/'native-build.json')['status']=='PASS'

def candidate_hashes():return {**m['base_hashes'],**{'bin/'+n:v for n,v in m['binaries'].items()}}
def binaries(candidate=True):return {n:v for n,v in ((k[4:],v) for k,v in (candidate_hashes() if candidate else m['base_hashes']).items()) if n in ('world','zone','shared_memory','ucs','loginserver')}
def players():return prior.player_count()
def saved():return {k:v for k,v in base.saved_state().items() if k not in NEW_TABLES}

def digest(table,where='1=1',database='peq'):
    columns=[l.split('\t')[0] for l in sql('SHOW COLUMNS FROM `'+table+'`;',database).splitlines()]
    assert columns and all(re.fullmatch('[A-Za-z0-9_]+',c) for c in columns)
    rows=sorted(sql('SELECT SHA2(JSON_ARRAY('+','.join('`'+c+'`' for c in columns)+'),256) FROM `'+table+'` WHERE '+where+';',database).splitlines())
    return {'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}

def content():
    # Keep every inherited public-content check, replacing only scopes we own.
    result={k:v for k,v in p.content().items() if k.split('/')[0] not in SCOPES}
    for table,scope in SCOPES.items():
        result[table+'/outside-lantern']=digest(table,'NOT ('+scope+')')
        result[table+'/schema']=hashlib.sha256(re.sub(r' AUTO_INCREMENT=[0-9]+','',sql('SHOW CREATE TABLE `'+table+'`;')).encode()).hexdigest()
    return result

def runtime(candidate=False):return {**m['runtime_before'],**(m['runtime_after'] if candidate else {})}
def unchanged(before,candidate=False):
    assert content()==before['content'],'Unrelated public content drift'
    assert p.rules()==before['rules'],'Rules drift'
    assert r.runtime()==runtime(candidate),'Quest/plugin runtime drift'
    assert h.publication()==before['publication'],'Public channel/wiki drift'
    if not candidate:assert h.caches()==before['caches'],'Cache drift'
    for name,state in before['services'].items():
        if name not in ('game','gateway'):assert r.compact(name)==state,'Service drift: '+name

def check_content(database='peq',enabled=0):
    catalog=read(STAGE/'last-lantern-catalog.json')
    result={}
    for table,key,rows in [('items','id',catalog['items']),('tasks','id',catalog['tasks']),
       ('task_activities','taskid',catalog['task_activities']),('npc_types','id',catalog['npc_types'])]:
        fields=list(rows[0]);actual=[json.loads(l) for l in sql('SELECT JSON_ARRAY('+','.join('`'+f+'`' for f in fields)+') FROM `'+table+'` WHERE '+SCOPES[table]+' ORDER BY '+('taskid,activityid' if table=='task_activities' else key)+';',database).splitlines()]
        expected=[[row[f] for f in fields] for row in sorted(rows,key=lambda x:(x[key],x.get('activityid',0)))]
        if table=='items':actual=[row for row in actual if row[fields.index('id')]!=900501]
        if table=='tasks':
            for row in expected:row[fields.index('enabled')]=enabled
        assert actual==expected,'Content afterimage: '+table
        result[table]=len(actual)
    tables=sorted(NEW_TABLES|{'tasks','task_activities','completed_tasks','character_tasks','character_activities','inventory','character_advloot_claims','instance_list','instance_list_player'})
    names=','.join("'"+t+"'" for t in tables)
    assert len(tables)==17
    assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ("+names+");",database).strip()=='17'
    assert sql("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ("+names+");",database).strip()=='0'
    refit_tables="'inventory','nightcap_lantern_control','nightcap_lantern_slots','nightcap_lantern_refits','completed_tasks','sharedbank','guild_bank','character_parcels','character_parcels_containers','character_corpse_items','character_corpses','character_pet_inventory','character_pet_armor','nightcap_bazaar_items','object_contents','trader'"
    assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ("+refit_tables+");",database).strip()=='16'
    assert sql("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ("+refit_tables+");",database).strip()=='0'
    assert sql('SELECT COUNT(*) FROM spells_new WHERE id BETWEEN 42800 AND 42805 AND typedescnum=0 AND effectdescnum=0;',database).strip()=='6'
    assert sql('SELECT COUNT(*) FROM spawn2 WHERE id BETWEEN 9113000 AND 9113005;',database).strip()=='6'
    assert sql('SELECT enabled FROM nightcap_lantern_control WHERE id=1 AND revision=2026110701;',database).strip()==str(enabled)
    assert sql('SELECT enabled FROM nightcap_epic05_control WHERE id=1 AND native_contract=1 AND catalog_version=1;',database).strip()==str(enabled)
    assert sql("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('inventory','completed_tasks','character_tasks','character_activities','instance_list','instance_list_player','character_advloot_claims','character_corpses');",database).strip()=='0'
    return result

def build_image():
    base_tag=TAG+'-base';r.call('docker','tag',m['base_image_id'],base_tag)
    (STAGE/'Dockerfile').write_text('FROM '+base_tag+'\nCOPY bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/world\n!bin/zone\n!bin/shared_memory\n')
    r.call('docker','build','--pull=false','--network','none','-t',TAG,str(STAGE))
    image=r.out('docker','image','inspect','--format','{{.Id}}',TAG).strip()
    assert r.image_hashes(image)==candidate_hashes()
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    for n in m['binaries']:assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+n)
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return image

def preflight():
    assert not EVIDENCE.exists(),'Existing attempt; inspect receipts instead of replaying'
    assert players()==0,'Players must fully exit'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    r.running(m['base_image_id'],binaries(False),services['game']['restarts'])
    startup.startup_guards();base.health();r.closed_ports();prior.contract()
    assert shutil.disk_usage(ROOT).free>4*1024**3,'Insufficient staging/backup reserve'
    EVIDENCE.mkdir(mode=0o700)
    before={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'content':content(),
      'rules':p.rules(),'caches':h.caches(),'publication':h.publication()}
    assert r.runtime()==runtime(False),'Quest preimages differ'
    save(EVIDENCE/'preflight-started.json',before)
    dry=EVIDENCE/'boot-preflight';dry.mkdir(mode=0o700)
    previous_evidence=base.EVIDENCE;base.EVIDENCE=dry
    try:base.boot_state(saved())
    finally:base.EVIDENCE=previous_evidence
    before['image']=build_image()
    assert sha(ROOT/'data/public/channel.json')==sha(STAGE/'client/previous-channel.json'),'Signed client baseline drift'
    spec=importlib.util.spec_from_file_location('rehearsal_publisher',STAGE/'client/publish.py')
    publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
    assert sha(ROOT/'data/public/channel.json')==publisher.OLD
    public=ROOT/'data/public';clone=EVIDENCE/'client-rehearsal';clone.mkdir()
    for path in public.iterdir():
        if path.is_file():shutil.copyfile(path,clone/path.name)
    manifest=json.loads(__import__('base64').b64decode(read(STAGE/'client/previous-channel.json')['manifest']))
    for file in manifest['files']:
        prefix='https://play.nightcapgame.org/';assert file['url'].startswith(prefix)
        relative=file['url'][len(prefix):];source=public/relative;target=clone/relative
        assert source.resolve().is_relative_to(public) and not source.is_symlink()
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():os.link(source,target)
    (clone/'release').mkdir(exist_ok=True)
    client_proof=publisher.publish(STAGE/'client',clone,lambda:{'isolated_rehearsal':True})
    assert sha(public/'channel.json')==publisher.OLD
    save(EVIDENCE/'client-rehearsal.json',client_proof)
    assert sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='World:FVNoDropFlag';").strip()=='0'
    assert sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='TaskSystem:RecordCompletedTasks';").strip()=='true'

    # Full rehearsal uses only public content; custody/task/player tables are empty.
    assert not sql("SELECT SCHEMA_NAME FROM information_schema.schemata WHERE schema_name='"+DATABASE+"';").strip()
    sql('CREATE DATABASE `'+DATABASE+'`;')
    for table in m['staging_tables']:
        assert re.fullmatch('[a-z0-9_]+',table)
        sql('CREATE TABLE `'+DATABASE+'`.`'+table+'` LIKE peq.`'+table+'`;')
        if table in m['public_clone_tables']:sql('INSERT INTO `'+DATABASE+'`.`'+table+'` SELECT * FROM peq.`'+table+'`;')
    sql((STAGE/'last-lantern-setup.sql').read_text(),DATABASE)
    checks=check_content(DATABASE,0)
    # Generate in a private isolated mount with a copied config; no live cache writes.
    before['cache_after']=prepare_cache(before['image'],DATABASE,EVIDENCE/'cache-staging')
    unchanged(before);assert all(r.compact(s)==v for s,v in services.items())
    before['checks']=checks
    save(EVIDENCE/'preflight.json',before)
    print('Preflight passed; production content, runtime, client and access unchanged.',flush=True)

def prepare_cache(image,database,folder):
    folder.mkdir(mode=0o700)
    # Read private configuration internally; never print credentials.
    cfg=json.loads(r.out('docker','exec',r.state('game')['Id'],'cat','/srv/nightcap/eqemu_config.json'))
    cfg['server']['database']['db']=database;cfg['server']['auto_database_updates']='false'
    cfg['server'].pop('content_database',None)
    (folder/'shared').mkdir();(folder/'logs').mkdir()
    (folder/'eqemu_config.json').write_text(json.dumps(cfg));(folder/'eqemu_config.json').chmod(0o600)
    user=cfg['server']['database']['username'];assert re.fullmatch('[A-Za-z0-9_]+',user)
    if database!= 'peq':sql("GRANT SELECT ON `"+database+"`.* TO '"+user+"'@'%';")
    command=['docker','run','--rm','--network',m['game_network'],'--user','0:0','-v',str(folder)+':/srv/nightcap','-w','/srv/nightcap','--entrypoint','/opt/nightcap/bin/shared_memory',image,'items','spells']
    with (folder/'loader.log').open('w') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    assert not re.search(r'MySQL Error|Unknown column|SQL syntax', (folder/'loader.log').read_text(),re.I),'Cache generator SQL error'
    live=ROOT/'data/server/shared'
    # Execute the small checker using the exact image's C++ runtime dependencies.
    cmd=['docker','run','--rm','--network','none','-v',str(STAGE)+':/release:ro','-v',str(live)+':/old:ro',
         '-v',str(folder/'shared')+':/new:ro','--user','0:0','--entrypoint','/release/cache_check',image,'/old/items','/new/items','/old/spells','/new/spells']
    output=subprocess.check_output(cmd,text=True,timeout=120)
    proof=json.loads(output);assert proof['status']=='PASS' and proof['added_items']==129
    save(folder/'verification.json',proof)
    # Retain protected config for stopped activation retries; never publish it.
    return {n:sha(folder/'shared'/n) for n in ('items','spells')}

def activate():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert not folder.exists(),'Never replay an uncertain activation'
    assert before['manifest_sha256']==sha(STAGE/'manifest.json')
    unchanged(before);assert all(r.compact(s)==v for s,v in before['services'].items())
    assert players()==0;startup.startup_guards();folder.mkdir(mode=0o700)
    save(folder/'started.json',{'image':before['image']})
    try:
        r.compose('stop','gateway')
        for elapsed in range(0,125,25):
            print(f'Draining native admissions {elapsed}/125 seconds.',flush=True);time.sleep(25)
        assert players()==0,'Client connected during admission drain'
        started=time.monotonic();r.compose('stop','-t','90','game')
        assert time.monotonic()-started<70
        state=r.state('game')['State'];assert not state['Running'] and not state['OOMKilled'] and state['ExitCode']==0
        assert not r.state('gateway')['State']['Running'];unchanged(before);startup.startup_guards()
        data=saved();market_before=market.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',market_before)
        r.STAGE=folder;base.EVIDENCE=folder;save(folder/'backup.json',r.database_backup());assert saved()==data
        expected=base.boot_state(data)
        sql((STAGE/'last-lantern-setup.sql').read_text());check_content(enabled=0)
        assert saved()==data,'Player-state drift during additive install'
        # Staging and production must generate byte-identical additive caches.
        staged=EVIDENCE/'cache-staging/shared'
        assert all(sha(ROOT/'data/server/shared'/n)==before['caches'][n] for n in ('items','spells'))
        for name,pin in m['runtime_after'].items():
            target=ROOT/'data/server'/name;source=STAGE/'runtime'/name
            assert sha(source)==pin and not target.is_symlink()
            target.parent.mkdir(parents=True,exist_ok=True)
            parent_owner=target.stat() if target.exists() else target.parent.stat()
            pending=target.with_name(target.name+'.last-lantern');assert not pending.exists()
            shutil.copyfile(source,pending);os.chmod(pending,0o644);os.chown(pending,parent_owner.st_uid,parent_owner.st_gid)
            with pending.open('rb') as handle:os.fsync(handle.fileno())
            os.replace(pending,target)
        for n in ('items','spells'):
            assert sha(staged/n)==before['cache_after'][n]
            pending=ROOT/'data/server/shared'/(n+'.last-lantern');assert not pending.exists()
            shutil.copyfile(staged/n,pending);os.chmod(pending,0o644)
            original=(ROOT/'data/server/shared'/n).stat();os.chown(pending,original.st_uid,original.st_gid)
            with pending.open('rb') as handle:os.fsync(handle.fileno())
            os.replace(pending,ROOT/'data/server/shared'/n)
        # Enable only the exact catalog that passed preflight. Native policy remains
        # active if a later forward-recovery disables the adventure gates.
        sql((STAGE/'last-lantern-enable.sql').read_text());checks=check_content(enabled=1)
        unchanged(before,True);prior.contract();r.select(before['image'])
        r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(before['image'],binaries());base.health();time.sleep(8)
        current=r.running(before['image'],binaries());assert first['started_at']==current['started_at']
        assert saved()==expected,'Saved-state boot differs from retained native model'
        rotation=market.verify_market(market_before,current['started_at'])
        unchanged(before,True);prior.contract();base.health();r.closed_ports()
        assert h.caches()==before['cache_after'],'Boot cache regeneration drift'
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,'checks':checks})
        print('Campaign runtime/content/cache verified. Admissions remain closed.',flush=True)
    except BaseException:h.hold(folder);raise

def open_access():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation';verified=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    assert r.compact('game')==verified['game'] and not r.state('gateway')['State']['Running']
    assert saved()==read(folder/'expected-boot-state.json')
    unchanged(before,True);check_content(enabled=1);prior.contract();base.health()
    assert h.caches()==before['cache_after']
    try:
        # The caller supplies a closed-gateway snapshot; publication must preserve it.
        spec=importlib.util.spec_from_file_location('client_publisher',STAGE/'client/publish.py')
        client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
        snapshot=lambda:{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
        result=client.publish(STAGE/'client',ROOT/'data/public',snapshot)
        save(folder/'client-published.json',result)
        save(folder/'opening.json',{'authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(before['image'],binaries());base.health();r.closed_ports()
        assert current['started_at']==verified['runtime']['started_at']
        assert r.state('gateway')['State']['Running']
        assert content()==before['content'] and p.rules()==before['rules'] and r.runtime()==runtime(True)
        assert sha(ROOT/'data/public/channel.json')==client.NEW
        save(folder/'deployed.json',{**verified,'runtime':current,'gateway_open':True,'client_release':2026110701,
            'owner_gameplay_accepted':False,'database_restored':False,'content_installed':True})
        print('Last Lantern and signed client notes published; admissions restored.',flush=True)
    except BaseException:h.hold(folder);raise

def main():
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','open'));action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access}[action]()

if __name__=='__main__':main()
