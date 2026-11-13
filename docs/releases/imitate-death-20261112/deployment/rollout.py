"""One-shot zone-only release. No content writes or player snapshot restore."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/imitate-death-20261112-v1')
EVIDENCE=STAGE/'evidence'
TAG='nightcap-game:imitate-death-20261112-v1'
AUTHORIZATION='Implement on live'

def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()
def read(path):return json.loads(path.read_text())
def save(path,value):
    with path.open('x') as handle:
        json.dump(value,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def initialize():
    global m,a,r,h,base,startup,market
    m=read(STAGE/'manifest.json');assert m['owner_authorization']==AUTHORIZATION
    for name,pin in m['files'].items():
        path=STAGE/name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and sha(path)==pin,name
    path=Path('/opt/nightcap/releases/augment-icons-20261112-v1/rollout.py')
    assert sha(path)==m['prior_operator_sha256']
    spec=importlib.util.spec_from_file_location('icon_baseline',path)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.initialize()
    r,h,base,startup,market=a.r,a.h,a.base,a.startup,a.market
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    proof=read(STAGE/'native-build.json')
    assert proof['status']=='PASS' and proof['scope'].startswith('Deployed full-build reproduction') and set(proof['source_delta'])=={'common/imitate_death.h','zone/aa.cpp'}
    assert proof['shipping']['baseline-zone']==m['base_hashes']['bin/zone']
    assert proof['shipping']['candidate-zone']==m['binaries']['zone']==m['files']['bin/zone']
    assert all(proof['source_sha256'][n]==pin for n,pin in m['source_hashes'].items())
    checks=read(STAGE/'release-checks.json')
    assert checks['status']=='PASS' and checks['native_build_sha256']==m['files']['native-build.json']
    assert read(STAGE/'review.json')['status']=='PASS'

def binaries(candidate=True):
    result={k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')}
    return {**result,**m['binaries']} if candidate else result
def unchanged(before,after_open=False,client_published=False):
    for name in ('db','web','tunnel'):assert r.compact(name)==before['services'][name],name
    assert r.runtime()==before['runtime'],'Quest/plugin drift'
    publication=copy.deepcopy(before['publication'])
    if client_published:publication['channels']['channel.json']=m['files']['client/channel.json']
    assert h.publication()==publication,'Client/wiki publication drift'
    assert h.caches()==before['caches'],'Cache drift'
    actual,expected=a.content(),before['content']
    if after_open:
        mutable={table+'/complete-icon-release' for table in a.prior.NEW_TABLES}
        actual={k:v for k,v in actual.items() if k not in mutable}
        expected={k:v for k,v in expected.items() if k not in mutable}
    assert actual==expected,'Content/campaign drift'
    assert a.prior.p.rules()==before['rules'],'Rules drift'
def contract():return a.contract()

def image():
    r.call('docker','tag',m['base_image_id'],TAG+'-base')
    (STAGE/'Dockerfile').write_text('FROM '+TAG+'-base\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--pull=false','--network','none','-t',TAG,str(STAGE))
    value=r.out('docker','image','inspect','--format','{{.Id}}',TAG).strip()
    assert r.image_hashes(value)=={**m['base_hashes'],'bin/zone':m['binaries']['zone']}
    layers=lambda name:json.loads(r.out('docker','image','inspect',name))[0]['RootFS']['Layers']
    assert layers(value)[:-1]==layers(m['base_image_id'])
    for candidate in (m['base_image_id'],value):
        assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',candidate,'/opt/nightcap/bin/zone')
        r.call('docker','run','--rm','--network','none','--entrypoint','python3',candidate,'-c',
               'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return value

def preflight():
    assert not EVIDENCE.exists(),'Existing attempt: inspect receipts; never replay'
    assert a.prior.players()==0,'Players online'
    services={n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
    assert all(s['running'] and not s['oom_killed'] for s in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    assert sha(ROOT/'data/public/channel.json')==m['client_channel_sha256'],'Client baseline changed'
    r.running(m['base_image_id'],binaries(False),services['game']['restarts'])
    base.health();startup.startup_guards();r.closed_ports();checks=contract()
    assert shutil.disk_usage(ROOT).free>4*1024**3
    EVIDENCE.mkdir(mode=0o700)
    before=dict(manifest_sha256=sha(STAGE/'manifest.json'),services=services,checks=checks,
        runtime=r.runtime(),publication=h.publication(),caches=h.caches(),content=a.content(),rules=a.prior.p.rules())
    save(EVIDENCE/'preflight-started.json',before)
    dry=EVIDENCE/'boot-preflight';dry.mkdir(mode=0o700);previous=base.EVIDENCE;base.EVIDENCE=dry
    try:base.boot_state(a.prior.saved())
    finally:base.EVIDENCE=previous
    before['image']=image();unchanged(before)
    assert all(r.compact(n)==s for n,s in services.items())
    save(EVIDENCE/'preflight.json',before)
    print('Preflight passed; compatible base retained; runtime and access unchanged.',flush=True)

def activate():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert before['manifest_sha256']==sha(STAGE/'manifest.json') and not folder.exists()
    assert a.prior.players()==0,'Players online'
    unchanged(before);startup.startup_guards()
    assert all(r.compact(n)==s for n,s in before['services'].items())
    folder.mkdir(mode=0o700);save(folder/'started.json',{'image':before['image']})
    try:
        r.compose('stop','gateway')
        for elapsed in range(0,125,25):
            print(f'Draining admissions: {elapsed}/125 seconds.',flush=True);time.sleep(25)
        assert a.prior.players()==0,'Player appeared during drain'
        started=time.monotonic();r.compose('stop','-t','90','game');assert time.monotonic()-started<70
        state=r.state('game')['State']
        assert not state['Running'] and not state['OOMKilled'] and state['ExitCode']==0
        assert not r.state('gateway')['State']['Running']
        unchanged(before);startup.startup_guards()
        saved=a.prior.saved();market_before=market.market()
        save(folder/'stopped-state.json',saved);save(folder/'market-before.json',market_before)
        r.STAGE=folder;base.EVIDENCE=folder
        save(folder/'backup.json',r.database_backup());assert a.prior.saved()==saved
        expected=base.boot_state(saved);unchanged(before);contract()
        r.select(before['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        first=r.running(before['image'],binaries());base.health();time.sleep(8)
        current=r.running(before['image'],binaries());assert first['started_at']==current['started_at']
        assert a.prior.saved()==expected,'Unexpected saved-state boot drift'
        rotation=market.verify_market(market_before,current['started_at'])
        unchanged(before);checks=contract();base.health();r.closed_ports()
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        assert not any(x in logs for x in ('MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement'))
        save(folder/'verified-closed.json',dict(runtime=current,game=r.compact('game'),checks=checks,market=rotation))
        print('Imitate Death zone verified; access remains closed.',flush=True)
    except BaseException:
        h.hold(folder);raise

def open_access():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation';verified=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==verified['game']
        assert a.prior.saved()==read(folder/'expected-boot-state.json')
        unchanged(before);contract();base.health();r.closed_ports()
        # Server metadata only; preserve the current signed client and wiki.
        save(folder/'opening.json',{'owner_authorized':True})
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        current=r.running(before['image'],binaries());base.health();r.closed_ports()
        assert current['started_at']==verified['runtime']['started_at'] and r.state('gateway')['State']['Running']
        unchanged(before,after_open=True)
        save(folder/'deployed.json',{**verified,'runtime':current,'gateway_open':True,
            'source_revision':m['source_revision'],'database_restored':False,'owner_gameplay_accepted':False,
            'client_release':2026111201,'client_channel_sha256':m['client_channel_sha256']})
        print('Imitate Death zero cooldown deployed; access restored.',flush=True)
    except BaseException:
        h.hold(folder);raise

def main():
    assert __debug__;os.umask(0o077);initialize()
    p=argparse.ArgumentParser();p.add_argument('action',choices=('preflight','activate','open'));action=p.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert a.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access}[action]()
if __name__=='__main__':main()
