"""Power Source item XP: paired world/zone/shared_memory plus one enabled rule. Explicit actions; immutable receipts.

Reuses the deployed Hunt-rates release's guards (and through it SSF, placeholder loot and
Hate boss). rule_values leaves the generic content hash and is checked exactly instead,
as in aa-level-progression-20261023-v3. Never replay an uncertain action or restore a
database snapshot. `rollback` exists only for a held activation before access reopens;
once players have trained items, keep the new readers (old binaries misread XP metadata).
"""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,tempfile,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/power-source-xp-20261103-v1')
EVIDENCE=STAGE/'evidence'
PRIOR=Path('/opt/nightcap/releases/zone-hunt-rates-20261101-v1')
NAMES=('world','zone','shared_memory')
RULE='Items:PowerSourceItemXP'
NOTES=('Enable combat item training in the Power Source slot. Requires paired native builds and supported '
       'RoF2 slot projection; does not replace the Reforging Box.')
RESERVE=672*1024**2
TAG='nightcap-game:power-source-xp-20261103-v1'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def save(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def read(path):return json.loads(path.read_text())

def initialize():
    global m,pl,h,r,base,startup,market_ops,sql
    m=read(STAGE/'manifest.json')
    for name,digest in m['files'].items():
        p=STAGE/name;assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==digest,name
    assert set(m['files'])=={'bin/'+n for n in NAMES}|{'rollout.py'}
    assert {p.name for p in (STAGE/'bin').iterdir()}==set(NAMES)
    assert m['replacement_binaries']=={n:m['files']['bin/'+n] for n in NAMES}
    assert sha(PRIOR/'rollout.py')==m['prior_rollout_sha256'],'Prior guard drift'
    spec=importlib.util.spec_from_file_location('prior_release',PRIOR/'rollout.py')
    pl=importlib.util.module_from_spec(spec);spec.loader.exec_module(pl);pl.initialize()
    h,r,base,startup,market_ops,sql=pl.h,pl.r,pl.base,pl.startup,pl.market_ops,pl.sql
    deployed=read(PRIOR/'evidence/activation/deployed.json')
    assert deployed['runtime']['image_id']==m['base_image_id']
    assert {**pl.m['base_hashes'],'bin/zone':pl.m['zone_sha256']}==m['base_hashes'],'Base is not the deployed release'
    assert all(m['replacement_binaries'][n]!=m['base_hashes']['bin/'+n] for n in NAMES)

def binaries(candidate=True):
    return {**pl.binaries(True),**(m['replacement_binaries'] if candidate else {})}

def candidate_hashes():
    return {**m['base_hashes'],**{'bin/'+n:v for n,v in m['replacement_binaries'].items()}}

def free():return shutil.disk_usage(ROOT).free

def rules():
    return sorted(json.loads(line) for line in sql('SELECT JSON_ARRAY(ruleset_id,rule_name,rule_value,notes) FROM rule_values ORDER BY ruleset_id,rule_name;').splitlines())

def desired(before):
    assert all(row[1]!=RULE for row in before),'Rule already exists; reconcile before proceeding'
    return sorted(before+[[1,RULE,'true',NOTES]])

def forward_sql():
    # A CHECK violation aborts this session before COMMIT; closing rolls back InnoDB.
    return ("START TRANSACTION; CREATE TEMPORARY TABLE item_xp_release_guard (ok INT CHECK(ok=1));\n"
            "INSERT INTO item_xp_release_guard SELECT COUNT(*)=0 FROM rule_values WHERE rule_name='"+RULE+"';\n"
            "INSERT INTO rule_values(ruleset_id,rule_name,rule_value,notes) VALUES(1,'"+RULE+"','true',CONVERT(0x"+NOTES.encode().hex()+" USING utf8mb4));\n"
            "INSERT INTO item_xp_release_guard SELECT ROW_COUNT()=1; COMMIT;")

def content():
    return {k:v for k,v in h.content().items() if k!='rule_values'}

def unchanged(p,installed=False):
    for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
    assert r.runtime()==p['runtime'],'Quest/plugin drift'
    assert h.publication()==p['publication'],'Publication drift'
    assert h.caches()==p['caches'],'Cache drift'
    assert content()==p['content'],'Content drift'
    assert rules()==p['after' if installed else 'before'],'Exact rule catalog drift'

def build_image():
    old=TAG+'-base';inspect=lambda x:r.out('docker','image','inspect','--format','{{.Id}}',x).strip()
    r.call('docker','tag',m['base_image_id'],old);assert inspect(old)==m['base_image_id']
    (STAGE/'Dockerfile').write_text('FROM '+old+'\nCOPY bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n'+''.join('!bin/'+n+'\n' for n in NAMES))
    r.call('docker','build','--pull=false','--network','none','-t',TAG,str(STAGE))
    image=inspect(TAG);assert inspect(old)==m['base_image_id']
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    assert r.image_hashes(image)==candidate_hashes()
    for n in NAMES:
        assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+n)
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return image

def preflight():
    assert not EVIDENCE.exists(),'Existing attempt; inspect receipts'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    r.running(m['base_image_id'],binaries(False),services['game']['restarts'])
    startup.database_guards();before=rules();after=desired(before)
    base.health();startup.startup_guards();r.closed_ports();checks=h.contract()
    size=sum((STAGE/'bin'/n).stat().st_size for n in NAMES)
    assert free()>=2*size+RESERVE,'Insufficient disk reserve'
    with tempfile.TemporaryDirectory() as dry:
        base.EVIDENCE=Path(dry);base.boot_state(base.saved_state())
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
       'publication':h.publication(),'caches':h.caches(),'content':content(),'before':before,'after':after,'checks':checks}
    EVIDENCE.mkdir(mode=0o700);save(EVIDENCE/'preflight-started.json',p)
    p['image']=build_image();unchanged(p)
    assert all(r.compact(s)==v for s,v in services.items()) and free()>=RESERVE
    save(EVIDENCE/'preflight.json',p);print('Preflight passed; gameplay and access unchanged.',flush=True)

def activate():
    p=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not folder.exists(),'Never replay an uncertain transition'
    unchanged(p);startup.startup_guards();startup.database_guards()
    assert all(r.compact(s)==v for s,v in p['services'].items())
    image=p['image'];assert r.image_hashes(image)==candidate_hashes()
    assert free()>=RESERVE
    folder.mkdir(mode=0o700);save(folder/'started.json',{'image':image})
    try:
        r.compose('stop','gateway');stop_started=time.monotonic();r.compose('stop','-t','90','game')
        assert time.monotonic()-stop_started<70,'Shutdown approached supervisor force-kill deadline'
        old=r.state('game')['State']
        assert not old['Running'] and not old['OOMKilled'] and old['ExitCode']==0
        assert not r.state('gateway')['State']['Running']
        startup.startup_guards();startup.database_guards();unchanged(p)
        data=base.saved_state();before_market=market_ops.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',before_market)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        unchanged(p);assert free()>=512*1024**2,'Disk reserve after backup'
        save(folder/'sql-started.json',{'rule':RULE,'value':'true'})
        sql(forward_sql())
        unchanged(p,True);assert base.saved_state()==data,'Unexpected state change'
        save(folder/'rule-committed.json',{'rule':RULE,'ruleset_id':1,'value':'true'})
        expected=base.boot_state(data)
        r.select(image);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(image,binaries());base.health();time.sleep(8)
        current=r.running(image,binaries());assert first['started_at']==current['started_at']
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        assert 'MySQL Error' not in logs and 'Unknown column' not in logs,'Database error after boot'
        assert 'Orphaned Rule' not in logs,'World deleted a rule'
        rotation=market_ops.verify_market(before_market,current['started_at'])
        assert base.saved_state()==expected,'Saved state drift; inspect exact rows'
        checks=h.contract();unchanged(p,True);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'rule':sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='"+RULE+"';").strip(),'checks':checks})
        print('Verified paired runtime, enabled rule and saved state; access closed.',flush=True)
    except BaseException:h.hold(folder);raise

def rollback():
    # Only after a held activation, before any player could train an item. Old world deletes the rule as orphaned.
    folder=EVIDENCE/'activation';out=EVIDENCE/'rollback'
    assert list(folder.glob('held-*.json')) and not (folder/'opening.json').exists() and not out.exists()
    assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
    out.mkdir(mode=0o700);save(out/'started.json',{'image':m['base_image_id']})
    try:
        r.select(m['base_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        current=r.running(m['base_image_id'],binaries(False));base.health();r.closed_ports()
        save(out/'verified-closed.json',{'runtime':current,'game':r.compact('game')})
        print('Base runtime restored; access closed.',flush=True)
    except BaseException:h.hold(out);raise

def open_access():
    p=read(EVIDENCE/'preflight.json')
    folder=EVIDENCE/('rollback' if (EVIDENCE/'rollback').exists() else 'activation')
    candidate=folder.name=='activation'
    a=read(folder/'verified-closed.json');image=a['runtime']['image_id']
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        if candidate:assert base.saved_state()==read(folder/'expected-boot-state.json');unchanged(p,True)
        h.contract();base.health();r.closed_ports()
        assert free()>=512*1024**2
        save(folder/'opening.json',{'authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(image,binaries(candidate));base.health();r.closed_ports()
        if candidate:unchanged(p,True)
        assert current['started_at']==a['runtime']['started_at'] and r.state('gateway')['State']['Running']
        save(folder/'deployed.json',{**a,'runtime':current,'gateway_open':True,'database_restored':False,
             'owner_gameplay_accepted':False,'client_update_required':False})
        print('Runtime verified; access restored. No client update.',flush=True)
    except BaseException:h.hold(folder);raise

def main():
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','rollback','open'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'rollback':rollback,'open':open_access}[action]()

if __name__=='__main__':main()
