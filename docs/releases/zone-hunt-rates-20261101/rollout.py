"""Per-zone Hunt rates: zone binary plus two additive columns. Explicit actions; immutable receipts.

Reuses the deployed SSF release's guards (and through it placeholder-loot and
Hate boss). Never replay an uncertain action or restore a database snapshot.
Recovery is `rollback`: base image; the columns stay (the base binary ignores them).
"""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,tempfile,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/zone-hunt-rates-20261101-v1')
EVIDENCE=STAGE/'evidence'
PRIOR=Path('/opt/nightcap/releases/ssf-mode-20261101-v1')
TABLE='nightcap_zone_hunt_zones'
ZONES=56
RESERVE=672*1024**2
TAG='nightcap-game:zone-hunt-rates-20261101-v1'

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
    assert set(m['files'])=={'bin/zone','rollout.py','rates.sql'}
    assert {p.name for p in (STAGE/'bin').iterdir()}=={'zone'} and m['files']['bin/zone']==m['zone_sha256']
    assert sha(PRIOR/'rollout.py')==m['prior_rollout_sha256'],'Prior guard drift'
    spec=importlib.util.spec_from_file_location('prior_release',PRIOR/'rollout.py')
    pl=importlib.util.module_from_spec(spec);spec.loader.exec_module(pl);pl.initialize()
    h,r,base,startup,market_ops,sql=pl.h,pl.r,pl.base,pl.startup,pl.market_ops,pl.sql
    deployed=read(PRIOR/'evidence/activation/deployed.json')
    assert deployed['runtime']['image_id']==m['base_image_id']
    assert {**pl.m['base_hashes'],'bin/zone':pl.m['zone_sha256']}==m['base_hashes'],'Base is not the deployed release'
    assert m['zone_sha256']!=m['base_hashes']['bin/zone']

def binaries(candidate=True):
    return {**pl.binaries(True),**({'zone':m['zone_sha256']} if candidate else {})}

def free():return shutil.disk_usage(ROOT).free

def columns():
    return sql(f"SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='{TABLE}' "
               "AND COLUMN_NAME IN ('augment_chance','gear_chance') ORDER BY COLUMN_NAME;").split()

def rates():
    return sql(f'SELECT augment_chance,gear_chance,COUNT(*) FROM {TABLE} GROUP BY 1,2;').strip()

def unchanged(p):
    # The SSF guard with its quest exception closed: this release changes no runtime file.
    for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
    assert r.runtime()==p['runtime'],'Quest/plugin drift'
    assert h.publication()==p['publication'],'Publication drift'
    assert h.caches()==p['caches'],'Cache drift'
    assert h.content()==p['content'],'Content/rule drift'

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
    assert columns()==[],'Rate columns already exist; inspect before installing'
    assert sql(f'SELECT COUNT(*) FROM {TABLE};').strip()==str(ZONES)
    base.health();startup.startup_guards();r.closed_ports();checks=h.contract()
    assert free()>=2*(STAGE/'bin/zone').stat().st_size+RESERVE,'Insufficient disk reserve'
    with tempfile.TemporaryDirectory() as dry:
        base.EVIDENCE=Path(dry);base.boot_state(base.saved_state())
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
       'publication':h.publication(),'caches':h.caches(),'content':h.content(),'checks':checks}
    EVIDENCE.mkdir(mode=0o700);save(EVIDENCE/'preflight-started.json',p)
    p['image']=build_image();unchanged(p)
    assert all(r.compact(s)==v for s,v in services.items()) and free()>=RESERVE
    save(EVIDENCE/'preflight.json',p);print('Preflight passed; gameplay and access unchanged.',flush=True)

def activate():
    p=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not folder.exists(),'Never replay an uncertain transition'
    unchanged(p);startup.startup_guards();assert columns()==[]
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
        startup.startup_guards();unchanged(p)
        data=base.saved_state();before_market=market_ops.market()
        save(folder/'stopped-state.json',data);save(folder/'market-before.json',before_market)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        unchanged(p);assert free()>=512*1024**2,'Disk reserve after backup'
        save(folder/'sql-started.json',{'rates_sha256':m['files']['rates.sql']})
        sql((STAGE/'rates.sql').read_text())
        assert columns()==['augment_chance','gear_chance'] and rates()==f'150\t50\t{ZONES}',rates()
        after=base.saved_state()
        assert {k:v for k,v in after.items() if k!=TABLE}=={k:v for k,v in data.items() if k!=TABLE},'Unexpected state change'
        assert after[TABLE]!=data[TABLE]
        save(folder/'sql-installed.json',{'rates':rates(),'state_tables':len(after)});unchanged(p)
        expected=base.boot_state(after)
        r.select(image);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(image,binaries());base.health();time.sleep(8)
        current=r.running(image,binaries());assert first['started_at']==current['started_at']
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        # Zones boot on demand, so a Hunt load line is recorded, not required; a failed config query logs MySQL Error.
        hunt=logs.count('Zone hunt [');assert 'MySQL Error' not in logs and 'Unknown column' not in logs,'Database error after boot'
        rotation=market_ops.verify_market(before_market,current['started_at'])
        assert base.saved_state()==expected,'Saved state drift; inspect exact rows'
        checks=h.contract();unchanged(p);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'market':rotation,
             'hunt_zones_logged':hunt,'rates':rates(),'checks':checks})
        print('Verified runtime, rates and saved state; access closed.',flush=True)
    except BaseException:h.hold(folder);raise

def rollback():
    # Only after a held activation. The columns stay; the base binary never reads them.
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
        if candidate:assert base.saved_state()==read(folder/'expected-boot-state.json')
        unchanged(p);h.contract();base.health();r.closed_ports()
        assert free()>=512*1024**2
        save(folder/'opening.json',{'authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(image,binaries(candidate));base.health();r.closed_ports();unchanged(p)
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
