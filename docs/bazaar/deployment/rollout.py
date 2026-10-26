"""Owner-authorized persistent bazaar. Additive escrow plus one zone layer.

Immutable attempts, fresh stopped backup, preserved prior state, separate opening.
Recovery disables new trading while retaining the compatible code and all ownership.
"""
import argparse,hashlib,importlib.util,json,os,shutil,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/commonlands-bazaar-20261026')
EVIDENCE=STAGE/'evidence'
NAMES={'world','zone','shared_memory','loginserver','ucs'}
RESERVE=672*1024**2

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert set(m['files'])=={'bin/zone','rollout.py','migration.sql'}
    assert set(m['helpers'])=={'runtime','state','startup','market'}
    for name,digest in m['files'].items():
        p=STAGE/name
        assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==digest,name
    for entry in [*m['helpers'].values(),m['contract']]:
        p=Path(entry['path']);assert p.is_absolute() and sha(p)==entry['sha256'],p
    assert m['files']['bin/zone']==m['zone_sha256']!=m['base_hashes']['bin/zone']
    return m

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def initialize():
    global r,base,startup,market_ops,sql
    m=manifest()
    r=module('tome_runtime',m['helpers']['runtime']['path'])
    base=module('tome_saved_state',m['helpers']['state']['path'])
    startup=module('tome_startup',m['helpers']['startup']['path'])
    market_ops=module('tome_market',m['helpers']['market']['path'])
    sql=base.sql;r.sql=sql;startup.sql=sql;market_ops.sql=sql
    base.r=r;r.STAGE=STAGE;r.EVIDENCE=EVIDENCE
    base.STAGE=STAGE;base.EVIDENCE=EVIDENCE
    original_tables=base.state_tables
    base.state_tables=lambda:[t for t in original_tables() if t not in NEW_TABLES]
    base.PUBLIC |= {'nightcap_waypoints','zone_points','ground_spawns','fishing','forage','traps','object'}

def save(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def read(path):return json.loads(path.read_text())
def binaries(recovery=False):
    m=manifest();out={n:m['base_hashes']['bin/'+n] for n in NAMES}
    if not recovery:out['zone']=m['zone_sha256']
    return out
def caches():return {n:sha(ROOT/'data/server/shared'/n) for n in ('items','spells')}
def content():return base.hashes(base.PUBLIC|{'nightcap_dungeon_state'})
def publication():
    return {'channels':r.public(),'wiki':os.readlink(ROOT/'data/public/wiki/current')}

def contract():
    data=read(Path(manifest()['contract']['path']));result={}
    for family,checks in data.items():
        values=sql(';\n'.join(c['sql'] for c in checks)+';').splitlines()
        assert len(values)==len(checks)
        failures=[c['label'] for c,v in zip(checks,values) if v!=c['expected']]
        assert not failures,(family,failures);result[family]=len(checks)
    return result

def unchanged(p):
    for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
    assert r.runtime()==p['runtime'],'Quest/plugin drift'
    assert publication()==p['publication'],'Publication drift'
    assert caches()==p['caches'],'Cache drift'
    assert content()==p['content'],'Content/rule drift'

def build_image(m):
    old='nightcap-game:commonlands-bazaar-20261026-base';new='nightcap-game:commonlands-bazaar-20261026'
    inspect=lambda x:r.out('docker','image','inspect','--format','{{.Id}}',x).strip()
    r.call('docker','tag',m['base_image_id'],old);assert inspect(old)==m['base_image_id']
    (STAGE/'Dockerfile').write_text('FROM '+old+'\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--pull=false','--network','none','-t',new,str(STAGE))
    image=inspect(new);assert inspect(old)==m['base_image_id']
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    assert r.image_hashes(image)=={**m['base_hashes'],'bin/zone':m['zone_sha256']}
    for candidate in (image,m['base_image_id']):
        assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',candidate,'/opt/nightcap/bin/zone')
        r.call('docker','run','--rm','--network','none','--entrypoint','python3',candidate,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',candidate,'--nightcap-crypto-self-test')
    return image

NEW_TABLES=('nightcap_bazaar_state','nightcap_bazaar_listings','nightcap_bazaar_items','nightcap_bazaar_credits','nightcap_bazaar_receipts')

def absent_storage():
    names=','.join("'"+t+"'" for t in NEW_TABLES)
    assert sql('SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('+names+');').strip()=='','Existing/partial market schema; inspect, never replay'

def storage(database='peq'):
    names=','.join("'"+t+"'" for t in (*NEW_TABLES,'inventory','character_currency'))
    assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ("+names+');',database).strip()=='7'
    assert sql('SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('+names+');',database).strip()=='0'
    inventory=[line.split('\t') for line in sql('SHOW COLUMNS FROM inventory;',database).splitlines()]
    escrow=[line.split('\t') for line in sql('SHOW COLUMNS FROM nightcap_bazaar_items;',database).splitlines()]
    expected=['character_id','slot_id','item_id','charges','color','augment_one','augment_two','augment_three','augment_four','augment_five','augment_six','instnodrop','custom_data','ornament_icon','ornament_idfile','ornament_hero_model','guid']
    assert [r[0] for r in inventory]==expected
    assert len(escrow)==18 and escrow[0][:3]==['listing_id','int(10) unsigned','NO']
    assert [r[:3] for r in inventory]==[r[:3] for r in escrow[1:]]
    return {t:sql('SHOW CREATE TABLE `'+t+'`;',database).strip() for t in NEW_TABLES}

def market_flag(enabled,database='peq',pristine=False):
    assert sql('SELECT id,version,enabled FROM nightcap_bazaar_state;',database).strip()==f'1\t1\t{enabled}'
    if pristine:
        for table in NEW_TABLES[1:]:assert sql('SELECT COUNT(*) FROM '+table+';',database).strip()=='0',table

def rehearse_storage():
    import secrets,re
    absent_storage();database='nightcap_classic_stage_'+secrets.token_hex(6)
    assert re.fullmatch('nightcap_classic_stage_[0-9a-f]{12}',database)
    # Fresh schema only; no private player rows are copied or mutated.
    sql('CREATE DATABASE `'+database+'`;')
    try:
        for table in ('inventory','character_currency'):sql('CREATE TABLE `'+table+'` LIKE peq.`'+table+'`;',database)
        sql((STAGE/'migration.sql').read_text(),database)
        expected=storage(database);market_flag(0,database,True)
        return expected
    finally:
        sql('DROP DATABASE `'+database+'`;')

def install_storage(folder,expected):
    absent_storage();save(folder/'migration-attempted.json',{'sha256':manifest()['files']['migration.sql']})
    sql((STAGE/'migration.sql').read_text())
    assert storage()==expected;market_flag(0,pristine=True)
    save(folder/'migration-committed.json',{'verified':True})

def enable_market(folder,expected):
    assert storage()==expected;market_flag(0,pristine=True)
    save(folder/'enable-attempted.json',{'authorized_live_qa':True})
    sql("START TRANSACTION; CREATE TEMPORARY TABLE bazaar_flag_guard(ok INT CHECK(ok=1)); UPDATE nightcap_bazaar_state SET enabled=1 WHERE id=1 AND version=1 AND enabled=0; INSERT INTO bazaar_flag_guard VALUES(ROW_COUNT()); COMMIT;")
    market_flag(1,pristine=True);save(folder/'enable-committed.json',{'verified':True})

def disable_market():
    # One attempt per release. Never replay an uncertain disable.
    folder=EVIDENCE/'disable';assert not folder.exists(),'Inspect the existing disable attempt'
    folder.mkdir(mode=0o700);save(folder/'started.json',{'compatible_code_retained':True})
    try:
        storage()
        flag=sql('SELECT id,version,enabled FROM nightcap_bazaar_state;').strip()
        assert flag in ('1\t1\t0','1\t1\t1')
        if flag=='1\t1\t1':
            save(folder/'update-attempted.json',{'from':1,'to':0})
            sql("START TRANSACTION; CREATE TEMPORARY TABLE bazaar_flag_guard(ok INT CHECK(ok=1)); UPDATE nightcap_bazaar_state SET enabled=0 WHERE id=1 AND version=1 AND enabled=1; INSERT INTO bazaar_flag_guard VALUES(ROW_COUNT()); COMMIT;")
        market_flag(0);save(folder/'disabled.json',{'verified':True,'ownership_preserved':True,'compatible_code_retained':True})
        print('New market trading disabled; ownership and recovery retained.',flush=True)
    except BaseException:
        hold(folder);raise


def preflight():
    m=manifest();assert not EVIDENCE.exists(),'Existing attempt; inspect receipts'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert sha(ROOT/'data/public/channel.json')==m['client_channel_sha256']
    r.running(m['base_image_id'],binaries(True),services['game']['restarts'])
    base.health();startup.startup_guards();r.closed_ports();checks=contract()
    assert shutil.disk_usage(ROOT).free>=2*(STAGE/'bin/zone').stat().st_size+RESERVE
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
       'publication':publication(),'caches':caches(),'content':content(),'checks':checks}
    EVIDENCE.mkdir(mode=0o700);save(EVIDENCE/'preflight-started.json',p)
    p['new_storage']=rehearse_storage()
    p['image']=build_image(m);unchanged(p)
    assert all(r.compact(s)==v for s,v in services.items())
    assert shutil.disk_usage(ROOT).free>=RESERVE
    save(EVIDENCE/'preflight.json',p);print('Preflight passed; gameplay and access unchanged.',flush=True)

def hold(folder):
    errors=[]
    for args in [('stop','gateway'),('stop','-t','90','game')]:
        try:r.compose(*args)
        except BaseException as e:errors.append(type(e).__name__)
    save(folder/('held-'+str(time.time_ns())+'.json'),{'errors':errors,'database_restored':False})

def transition(recovery=False):
    assert not recovery,'Retain compatible code and disable trading; no binary down-migration'
    m=manifest();p=read(EVIDENCE/'preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    folder=EVIDENCE/('recovery' if recovery else 'activation')
    assert not folder.exists(),'Never replay an uncertain transition'
    unchanged(p);startup.startup_guards()
    assert all(r.compact(s)==v for s,v in p['services'].items())
    image=m['base_image_id'] if recovery else p['image']
    expected_hashes={**m['base_hashes'],**{'bin/'+n:h for n,h in binaries(recovery).items()}}
    assert r.image_hashes(image)==expected_hashes
    assert shutil.disk_usage(ROOT).free>=RESERVE
    folder.mkdir(mode=0o700);save(folder/'started.json',{'recovery':recovery,'image':image})
    try:
        r.compose('stop','gateway');stop_started=time.monotonic();r.compose('stop','-t','90','game')
        assert time.monotonic()-stop_started<70,'Shutdown approached supervisor force-kill deadline'
        old=r.state('game')['State']
        assert not old['Running'] and not old['OOMKilled'] and old['ExitCode']==0
        assert not r.state('gateway')['State']['Running']
        startup.startup_guards();unchanged(p)
        data=base.saved_state();before_market=market_ops.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',before_market)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        install_storage(folder,p['new_storage']);assert base.saved_state()==data
        expected=base.boot_state(data);unchanged(p)
        assert shutil.disk_usage(ROOT).free>=512*1024**2
        r.select(image);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(image,binaries(recovery));base.health();time.sleep(8)
        current=r.running(image,binaries(recovery));assert first['started_at']==current['started_at']
        rotation=market_ops.verify_market(before_market,current['started_at'])
        assert base.saved_state()==expected,'Saved state drift; inspect exact rows'
        checks=contract();unchanged(p);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        enable_market(folder,p['new_storage'])
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'state_tables':len(data),'checks':checks,'recovery':recovery})
        print('Verified runtime and saved state; access closed.',flush=True)
    except BaseException:hold(folder);raise

def open_access(recovery=False):
    assert not recovery,'Binary down-migration is unsupported after escrow installation'
    m=manifest();p=read(EVIDENCE/'preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    folder=EVIDENCE/('recovery' if recovery else 'activation');a=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        assert base.saved_state()==read(folder/'expected-boot-state.json')
        assert market_ops.verify_market(read(folder/'market-before.json'),a['runtime']['started_at'])==a['market']
        assert storage()==p['new_storage'];market_flag(1,pristine=True)
        unchanged(p);contract();base.health();r.closed_ports()
        assert shutil.disk_usage(ROOT).free>=512*1024**2
        save(folder/'opening.json',{'authorized':True,'recovery':recovery})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(a['runtime']['image_id'],binaries(recovery));base.health();r.closed_ports();unchanged(p)
        assert current['started_at']==a['runtime']['started_at'] and r.state('gateway')['State']['Running']
        save(folder/'deployed.json',{**a,'runtime':current,'gateway_open':True,'database_restored':False,
             'owner_gameplay_accepted':False,'client_update_required':False})
        print('Commonlands bazaar verified; access restored.',flush=True)
    except BaseException:hold(folder);raise

def main():
    import fcntl
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','open','disable'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':transition,'open':open_access,
         'disable':disable_market}[action]()

if __name__=='__main__':main()
