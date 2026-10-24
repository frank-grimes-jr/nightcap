"""Zone-only tome repair. Explicit activation; immutable receipts; no SQL writes.

Recovery selects the immediate prior image while retaining current player state.
Never replay an uncertain action or restore a database snapshot.
"""
import argparse,hashlib,importlib.util,json,os,shutil,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/rogue-tomes-20261024')
EVIDENCE=STAGE/'evidence'
NAMES={'world','zone','shared_memory','loginserver','ucs'}
RESERVE=672*1024**2

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert set(m['files'])=={'bin/zone','rollout.py'}
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
    old='nightcap-game:rogue-tomes-20261024-base';new='nightcap-game:rogue-tomes-20261024'
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
    m=manifest();p=read(EVIDENCE/'preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    folder=EVIDENCE/('recovery' if recovery else 'activation')
    assert not folder.exists(),'Never replay an uncertain transition'
    unchanged(p);startup.startup_guards()
    if recovery:
        assert (EVIDENCE/'activation').is_dir(),'Nothing activated to recover'
        assert r.state('game')['Image'] in (p['image'],m['base_image_id'])
        prior=EVIDENCE/'activation'
        if not (prior/'deployed.json').exists():
            # Never bless unexplained loss/rotation by calling it a new baseline.
            # An uncertain opening may have admitted players; it needs a scoped
            # reconciliation, not either a stale snapshot or a permissive reset.
            assert (prior/'verified-closed.json').exists() and not (prior/'opening.json').exists(), 'Unverified/uncertain activation requires audited recovery'
            verified=read(prior/'verified-closed.json')
            assert base.saved_state()==read(prior/'expected-boot-state.json'), 'Unreconciled activation state drift'
            assert market_ops.verify_market(read(prior/'market-before.json'),verified['runtime']['started_at'])==verified['market']
    else:
        assert all(r.compact(s)==v for s,v in p['services'].items())
    image=m['base_image_id'] if recovery else p['image']
    expected_hashes={**m['base_hashes'],**{'bin/'+n:h for n,h in binaries(recovery).items()}}
    assert r.image_hashes(image)==expected_hashes
    assert shutil.disk_usage(ROOT).free>=RESERVE
    folder.mkdir(mode=0o700);save(folder/'started.json',{'recovery':recovery,'image':image})
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        old=r.state('game')['State']
        assert not old['Running'] and not old['OOMKilled'] and old['ExitCode']==0
        assert not r.state('gateway')['State']['Running']
        startup.startup_guards();unchanged(p)
        data=base.saved_state();before_market=market_ops.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',before_market)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        expected=base.boot_state(data);unchanged(p)
        assert shutil.disk_usage(ROOT).free>=512*1024**2
        r.select(image);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(image,binaries(recovery));base.health();time.sleep(8)
        current=r.running(image,binaries(recovery));assert first['started_at']==current['started_at']
        rotation=market_ops.verify_market(before_market,current['started_at'])
        assert base.saved_state()==expected,'Saved state drift; inspect exact rows'
        checks=contract();unchanged(p);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'state_tables':len(data),'checks':checks,'recovery':recovery})
        print('Verified runtime and saved state; access closed.',flush=True)
    except BaseException:hold(folder);raise

def open_access(recovery=False):
    m=manifest();p=read(EVIDENCE/'preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    folder=EVIDENCE/('recovery' if recovery else 'activation');a=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        assert base.saved_state()==read(folder/'expected-boot-state.json')
        assert market_ops.verify_market(read(folder/'market-before.json'),a['runtime']['started_at'])==a['market']
        unchanged(p);contract();base.health();r.closed_ports()
        assert shutil.disk_usage(ROOT).free>=512*1024**2
        save(folder/'opening.json',{'authorized':True,'recovery':recovery})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(a['runtime']['image_id'],binaries(recovery));base.health();r.closed_ports();unchanged(p)
        assert current['started_at']==a['runtime']['started_at'] and r.state('gateway')['State']['Running']
        save(folder/'deployed.json',{**a,'runtime':current,'gateway_open':True,'database_restored':False,
             'owner_gameplay_accepted':False,'client_update_required':False})
        print('Tome runtime verified; access restored.',flush=True)
    except BaseException:hold(folder);raise

def main():
    import fcntl
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','open','rollback','open-rollback'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':transition,'open':open_access,
         'rollback':lambda:transition(True),'open-rollback':lambda:open_access(True)}[action]()

if __name__=='__main__':main()
