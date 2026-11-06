"""Zone-only placeholder-loot fix. Explicit actions; immutable receipts; no SQL writes.

Reuses the deployed Hate boss release's audited guards and helpers unchanged.
Never replay an uncertain action or restore a database snapshot. The only
recovery is `rollback`, which reselects the unchanged base image.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,tempfile,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/npc-placeholder-loot-20261101-v1')
EVIDENCE=STAGE/'evidence'
PRIOR=Path('/opt/nightcap/releases/hate-boss-placement-20261030-v1')
NAMES={'world','zone','shared_memory','loginserver','ucs'}
RESERVE=672*1024**2
TAG='nightcap-game:npc-placeholder-loot-20261101-v1'

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
    global m,h,r,base,startup,market_ops,sql
    m=read(STAGE/'manifest.json')
    assert sha(PRIOR/'rollout.py')==m['prior_rollout_sha256'],'Prior guard drift'
    assert {p.name for p in (STAGE/'bin').iterdir()}=={'zone'} and sha(STAGE/'bin/zone')==m['zone_sha256']
    spec=importlib.util.spec_from_file_location('prior_release',PRIOR/'rollout.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);h.initialize()
    r,base,startup,market_ops,sql=h.r,h.base,h.startup,h.market_ops,h.sql
    prior=h.manifest()
    assert {**prior['base_hashes'],**prior['candidate_hashes']}==m['base_hashes'],'Base is not the deployed release'
    assert m['zone_sha256']!=m['base_hashes']['bin/zone']

def binaries(candidate=True):
    out={n:m['base_hashes']['bin/'+n] for n in NAMES}
    if candidate:out['zone']=m['zone_sha256']
    return out

def free():return shutil.disk_usage(ROOT).free

def build_image():
    old=TAG+'-base';inspect=lambda x:r.out('docker','image','inspect','--format','{{.Id}}',x).strip()
    r.call('docker','tag',m['base_image_id'],old);assert inspect(old)==m['base_image_id']
    (STAGE/'Dockerfile').write_text('FROM '+old+'\nCOPY bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--pull=false','--network','none','-t',TAG,str(STAGE))
    image=inspect(TAG);assert inspect(old)==m['base_image_id']
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    assert r.image_hashes(image)=={**m['base_hashes'],'bin/zone':m['zone_sha256']}
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
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
    # h.contract() is the installed-state gate; the prior public_preflight is its
    # pre-install snapshot and correctly fails once its three boss rows moved.
    base.health();startup.startup_guards();r.closed_ports();checks=h.contract()
    assert free()>=2*(STAGE/'bin/zone').stat().st_size+RESERVE,'Insufficient disk reserve'
    # Dry-run the boot model now so a structural refusal cannot happen mid-outage.
    with tempfile.TemporaryDirectory() as dry:
        base.EVIDENCE=Path(dry);base.boot_state(base.saved_state())
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
       'publication':h.publication(),'caches':h.caches(),'content':h.content(),'checks':checks}
    EVIDENCE.mkdir(mode=0o700);save(EVIDENCE/'preflight-started.json',p)
    p['image']=build_image();h.unchanged(p)
    assert all(r.compact(s)==v for s,v in services.items()) and free()>=RESERVE
    save(EVIDENCE/'preflight.json',p);print('Preflight passed; gameplay and access unchanged.',flush=True)

def activate():
    p=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not folder.exists(),'Never replay an uncertain transition'
    h.unchanged(p);startup.startup_guards()
    assert all(r.compact(s)==v for s,v in p['services'].items())
    image=p['image'];assert r.image_hashes(image)=={**m['base_hashes'],'bin/zone':m['zone_sha256']}
    assert free()>=RESERVE
    folder.mkdir(mode=0o700);save(folder/'started.json',{'image':image})
    try:
        r.compose('stop','gateway');stop_started=time.monotonic();r.compose('stop','-t','90','game')
        assert time.monotonic()-stop_started<70,'Shutdown approached supervisor force-kill deadline'
        old=r.state('game')['State']
        assert not old['Running'] and not old['OOMKilled'] and old['ExitCode']==0
        assert not r.state('gateway')['State']['Running']
        startup.startup_guards();h.unchanged(p)
        data=base.saved_state();before_market=market_ops.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',before_market)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        h.unchanged(p);assert free()>=512*1024**2,'Disk reserve after backup'
        expected=base.boot_state(data)
        r.select(image);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(image,binaries());base.health();time.sleep(8)
        current=r.running(image,binaries());assert first['started_at']==current['started_at']
        rotation=market_ops.verify_market(before_market,current['started_at'])
        assert base.saved_state()==expected,'Saved state drift; inspect exact rows'
        checks=h.contract();h.unchanged(p);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'state_tables':len(data),'checks':checks})
        print('Verified runtime and saved state; access closed.',flush=True)
    except BaseException:h.hold(folder);raise

def rollback():
    # Only after a held activation: the base image needs no schema or data change.
    folder=EVIDENCE/'activation';out=EVIDENCE/'rollback'
    assert list(folder.glob('held-*.json')) and not (folder/'opening.json').exists() and not out.exists()
    assert not r.state('gateway')['State']['Running']
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
    a=read(folder/'verified-closed.json');image=a['runtime']['image_id']
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        if folder.name=='activation':assert base.saved_state()==read(folder/'expected-boot-state.json')
        h.unchanged(p);h.contract();base.health();r.closed_ports()
        assert free()>=512*1024**2
        save(folder/'opening.json',{'authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(image,binaries(folder.name=='activation'));base.health();r.closed_ports();h.unchanged(p)
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
