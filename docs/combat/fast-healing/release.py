"""Activate the validated fast-healing floor using the retained production supervisor."""
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

STAGE = Path(__file__).resolve().parent
ROOT = Path('/opt/nightcap/deploy/production')
ACTIVE = STAGE/'evidence'/'activation'
OLD = STAGE.parent/'stock-worn-atk-20261113-v1'/'release.py'

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def rules_digest():
    values=sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name')
    return hashlib.sha256(values.encode()).hexdigest()

def image():
    tag='nightcap-game:'+STAGE.name
    r.call('docker','tag',m['image'],tag+'-base')
    (STAGE/'Dockerfile').write_text('FROM '+tag+'-base\nCOPY --chmod=0755 bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!bin\n!bin/world\n!bin/zone\n')
    r.call('docker','build','--network','none','--pull=false','-t',tag,str(STAGE))
    value=r.out('docker','image','inspect','--format','{{.Id}}',tag).strip()
    assert r.image_hashes(value)=={**m['base_hashes'],**{'bin/'+k:v for k,v in m['binaries'].items()}}
    for name in m['binaries']:
        assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',value,'/opt/nightcap/bin/'+name)
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',value,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return value

def verify(candidate,pre):
    bins={k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')}
    if candidate!=m['image']:bins.update(m['binaries'])
    runtime=r.running(candidate,bins)
    assert not any(runtime['errors'].values()) and runtime['restart_count']==0
    assert sum(x[0]=='zone' for x in runtime['processes'])==12
    assert rules_digest()==pre['rules_digest']
    assert op.h.caches()==pre['caches'] and op.h.publication()==pre['publication']
    assert all(r.compact(n)==m['services'][n] for n in ('db','web','tunnel'))
    op.base.health()
    op.p.contract()
    r.closed_ports()
    return runtime

def deploy(allow_admission_drain=False):
    assert not ACTIVE.exists() and r.image_hashes(m['image'])==m['base_hashes']
    assert all(r.compact(k)==v for k,v in m['services'].items())
    assert sha(ROOT/'data/public/channel.json')==m['channel']
    op.p.startup.startup_guards()
    pre=dict(caches=op.h.caches(),publication=op.h.publication(),rules_digest=rules_digest())
    assert pre['caches']==m['caches']
    verify(m['image'],pre)
    assert allow_admission_drain or op.a.prior.players()==0, 'Wait for players to log out before maintenance'
    target=image()
    ACTIVE.mkdir(parents=True,mode=0o700)
    save(ACTIVE/'started.json',dict(source=m['source'],image=target,players=op.a.prior.players(),**pre))
    r.compose('stop','gateway')
    try:
        time.sleep(125)
        deadline=time.monotonic()+180
        while op.a.prior.players():
            assert time.monotonic()<deadline,'World did not drain'
            time.sleep(3)
        assert not r.compact('gateway')['running'] and rules_digest()==pre['rules_digest']
        r.compose('stop','-t','90','game')
        state=r.state('game')['State']
        assert not state['Running'] and not state['OOMKilled'] and state['ExitCode']==0
        saved=op.a.prior.saved()
        market=op.p.market.market()
        r.STAGE=op.base.EVIDENCE=ACTIVE
        backup=r.database_backup()
        assert backup['gzip_integrity'] and sha(Path(backup['path']))==backup['sha256']
        save(ACTIVE/'backup.json',backup)
        expected=op.base.boot_state(saved)
        assert saved==op.a.prior.saved() and rules_digest()==pre['rules_digest']
        r.select(target)
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        runtime=verify(target,pre)
        assert op.a.prior.saved()==expected
        rotation=op.p.market.verify_market(market,runtime['started_at'])
        save(ACTIVE/'verified-closed.json',dict(started_at=runtime['started_at'],market=rotation))
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        assert r.compact('gateway')['running']
        assert verify(target,pre)['started_at']==runtime['started_at']
        save(ACTIVE/'deployed.json',dict(source=m['source'],image=target,workers=12,rules_digest=pre['rules_digest'],backup=backup['sha256'],gateway_open=True,binaries=m['binaries'],errors=runtime['errors']))
    except BaseException:
        if r.compact('game')==m['services']['game'] and rules_digest()==pre['rules_digest']:
            r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        else:
            op.h.hold(ACTIVE)
        raise

if __name__=='__main__':
    os.umask(0o077)
    m=read(STAGE/'manifest.json')
    assert __debug__ and re.fullmatch('[0-9a-f]{40}',m['source'])
    assert set(m['files'])=={'release.py','build.json','bin/zone'}
    for n,v in m['files'].items():assert sha(STAGE/n)==v
    assert sha(OLD)==m['stock_operator']
    build=read(STAGE/'build.json')
    assert build['binaries']==m['binaries'] and all(m['files']['bin/'+k]==v and build['baseline'][k]==m['base_hashes']['bin/'+k] for k,v in m['binaries'].items())
    spec=importlib.util.spec_from_file_location('stock',OLD)
    op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
    r,sql,save=op.r,op.op.sql,op.p.save
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        if sys.argv[1]=='preflight':
            assert all(r.compact(k)==v for k,v in m['services'].items())
            assert op.h.caches()==m['caches'] and sha(ROOT/'data/public/channel.json')==m['channel']
            target=image()
            result=dict(result='PASS',candidate=target,players=op.a.prior.players(),baseline=m['image'],binaries=m['binaries'])
            save(STAGE/'preflight.json',result);print(json.dumps(result))
        elif sys.argv[1] in ('activate','activate-authorized-drain'):
            deploy(allow_admission_drain=sys.argv[1]=='activate-authorized-drain')
        elif sys.argv[1]=='verify':
            dep=read(ACTIVE/'deployed.json');pre=read(ACTIVE/'started.json');assert r.compact('gateway')['running']
            assert verify(dep['image'],pre)['started_at']==read(ACTIVE/'verified-closed.json')['started_at']
            print(json.dumps(dep))
