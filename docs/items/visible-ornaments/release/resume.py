"""Resume only the verified post-content, pre-boot hold of November 21."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path

def mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

stage=Path(__file__).resolve().parent
a=mod('ornament',stage/'activate.py')
m=a.read(stage/'manifest.json')
assert all(a.sha(stage/k)==v for k,v in m['files'].items())
aa=mod('aa',stage.parent/'aa-purchase-latency-20261121-v1/release.py')
assert a.sha(aa.OLD)==m['stock_operator']
op=mod('stock',aa.OLD);op.initialize()
r=op.r
a.m,a.r,a.h,a.a,a.stock,a.aa,a.save=m,r,op.h,op.a,op,aa,op.p.save
aa.STAGE,aa.m,aa.r,aa.sql=stage,m,r,a.sql
pre=a.read(stage/'preflight.json')
folder=a.active
with (a.root/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (a.root/'private/gm-maintenance.json').exists() and a.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
    assert not r.compact('game')['running'] and not r.compact('gateway')['running']
    assert r.compact('game')['image_id']==m['image'] and not (folder/'opening.json').exists()
    assert pre['manifest']==a.sha(stage/'manifest.json') and a.sha(a.quest)==m['files']['998946.pl']
    assert op.h.caches()==m['caches'] and op.h.publication()==pre['publication']
    assert aa.rules_digest()==pre['rules']
    backup=a.read(folder/'backup.json')
    assert backup['gzip_integrity'] and a.sha(Path(backup['path']))==backup['sha256']
    expected=a.read(folder/'expected-boot-state.json')
    assert a.read(folder/'native-expiry.json')['expired_noncorpse_rows']==0
    existing=op.a.prior.saved()
    added={'nightcap_ornament_design','nightcap_ornament_source'}
    assert set(existing)==set(expected)|added
    assert all(existing[name]==value for name,value in expected.items())
    counts=a.check_content()
    market=op.p.market.market()
    a.save(folder/'content-preserved.json',dict(original_tables=len(expected),owned=sorted(added),content=counts))
    r.STAGE=op.base.EVIDENCE=folder
    opening=False
    try:
        r.select(pre['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        run=a.check_running(pre)
        assert op.a.prior.saved()==existing
        rotation=op.p.market.verify_market(market,run['started_at'])
        a.save(folder/'verified-closed.json',dict(started_at=run['started_at'],market=rotation))
        opening=True
        a.save(folder/'opening.json',dict(image=pre['image']))
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        assert r.compact('gateway')['running'] and a.check_running(pre)['started_at']==run['started_at']
        a.save(folder/'deployed.json',dict(source=m['source'],workers=12,errors=run['errors'],gateway_open=True,
              image=pre['image'],binaries=m['binaries'],cache=pre['cache'],content=counts,
              preserved_original_tables=len(expected),backup_sha256=backup['sha256'],manual_qa='open'))
    except BaseException:
        if opening:r.compose('stop','gateway')
        else:op.h.hold(folder)
        raise
