"""Authorized zone-only Keeper repair; reuse authenticated current native release guards.

No SQL migration, cache/client change, run reset or player snapshot recovery.
Every action is one-shot and failures hold admissions closed.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1')
PRIOR=Path('/opt/nightcap/releases/character-stats-window-20261106-v1')
EVIDENCE=STAGE/'evidence'
TAG='nightcap-game:dungeon-readiness-20261106-v1'


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(path.read_text())


def initialize():
    global p,m,base_binaries
    m=read(STAGE/'manifest.json')
    assert set(m['files'])=={'bin/zone','rollout.py','runtime-contract.json','native-build.json','world_count.py'}
    assert m['owner_deploy_authorized']=='2026-11-06 chat: Yes, merge to main and deploy to OVH for live QA.'
    for name,digest in m['files'].items():
        path=STAGE/name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and sha(path)==digest,name
    assert sha(PRIOR/'rollout.py')==m['prior_rollout_sha256']
    spec=importlib.util.spec_from_file_location('prior_stats',PRIOR/'rollout.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.initialize()
    deployed=read(PRIOR/'evidence/activation/deployed.json')
    assert deployed['gateway_open'] and deployed['runtime']['image_id']==m['base_image_id']
    assert p.r.image_hashes(m['base_image_id'])==m['base_hashes']
    base_binaries=p.binaries()
    assert base_binaries['zone']=='ea6ad5324fbfd976210d060ad3efd29616c9da53a73f36f5d4fd7cfbd8743d6a'
    proof=read(STAGE/'native-build.json')
    assert proof['status']=='PASS' and proof['retained_baseline_shipping_sha256']==base_binaries['zone']
    assert proof['candidate_shipping_sha256']==m['zone_sha256']==m['files']['bin/zone']
    assert proof['runtime_contract_sha256']==m['files']['runtime-contract.json']
    assert proof['cache_afterimages_accepted']==8 and proof['cache_negative_mutations']==33
    # Lifecycle functions resolve these globals in the authenticated prior module.
    # Preserve its content/rule/cache/command/boot-state/market implementations.
    p.m=m;p.STAGE=STAGE;p.EVIDENCE=EVIDENCE;p.TAG=TAG
    p.binaries=binaries;p.contract=contract


def binaries(candidate=True):
    return {**base_binaries,'zone':m['zone_sha256'] if candidate else base_binaries['zone']}


def contract():
    data=read(STAGE/'runtime-contract.json')
    assert set(data)=={'schema','content'} and len(data['schema'])==51 and len(data['content'])==671
    result={}
    for family,checks in data.items():
        assert len({c['label'] for c in checks})==len(checks)
        values=p.sql(';\n'.join(c['sql'] for c in checks)+';').splitlines()
        assert len(values)==len(checks),'Contract result count: '+family
        for check,value in zip(checks,values):
            assert value==check['expected'],'Compiled contract: '+family+'/'+check['label']
        result[family]=len(checks)
    return result


def preflight():
    assert player_count()==0,'Players must fully exit before this restart'
    return p.preflight()


def player_count():
    value=json.loads(p.r.out('docker','exec',p.r.state('game')['Id'],'python3','-c',(STAGE/'world_count.py').read_text()))
    assert type(value) is int and value>=0,'Unexpected native client-count response'
    return value


def activate():
    assert player_count()==0,'Players must fully exit before this restart'
    compose=p.r.compose
    def guarded_compose(*args):
        if args==('stop','gateway'):
            result=compose(*args)
            # Drain the native 120-second transfer/auth window while ingress is closed.
            for elapsed in range(0,125,25):
                print(f'Admission hold: draining native auth ({elapsed}/125 seconds).',flush=True)
                p.time.sleep(25)
            assert player_count()==0,'A native client remains after admission drain'
            return result
        if args and args[0]=='stop' and args[-1]=='game':
            assert player_count()==0,'A native client remains before shutdown'
        return compose(*args)
    p.r.compose=guarded_compose
    try:p.activate()
    finally:p.r.compose=compose
    folder=EVIDENCE/'activation'
    try:
        verified=read(folder/'verified-closed.json')
        logs=p.r.out('docker','compose','logs','--no-color','--since',verified['runtime']['started_at'],'game')
        assert not any(s in logs for s in ('Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Chapterhouse cache drift','Unknown column'))
    except BaseException:p.h.hold(folder);raise


def rollback():
    # Select the compatible current Stats runtime only while admissions are held.
    # Recompute normal boot effects from fresh saved state, never restore snapshots.
    before=read(EVIDENCE/'preflight.json');activation=EVIDENCE/'activation';folder=EVIDENCE/'rollback'
    assert list(activation.glob('held-*.json')) and not (activation/'opening.json').exists() and not folder.exists()
    assert not p.r.state('gateway')['State']['Running'] and not p.r.state('game')['State']['Running']
    folder.mkdir(mode=0o700);p.save(folder/'started.json',{'image':m['base_image_id']})
    try:
        p.unchanged(before);data=p.base.saved_state();market=p.market_ops.market()
        p.save(folder/'stopped-state.json',data);p.base.EVIDENCE=folder
        expected=p.base.boot_state(data)
        p.r.select(m['base_image_id']);p.r.compose('up','-d','--wait','--wait-timeout','240','game')
        runtime=p.r.running(m['base_image_id'],binaries(False));p.base.health()
        rotation=p.market_ops.verify_market(market,runtime['started_at'])
        assert p.base.saved_state()==expected
        p.command_state(True);contract();p.unchanged(before);p.r.closed_ports()
        p.save(folder/'verified-closed.json',{'runtime':runtime,'game':p.r.compact('game'),'market':rotation,'checks':contract()})
    except BaseException:p.h.hold(folder);raise


def open_access():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/('rollback' if (EVIDENCE/'rollback').exists() else 'activation')
    candidate=folder.name=='activation';verified=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not p.r.state('gateway')['State']['Running'] and p.r.compact('game')==verified['game']
        assert p.base.saved_state()==read(folder/'expected-boot-state.json')
        p.command_state(True);p.unchanged(before);checks=contract();p.base.health();p.r.closed_ports()
        assert p.free()>=512*1024**2
        p.save(folder/'opening.json',{'owner_authorized':True,'source_revision':m['source_revision']})
        p.r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=p.r.running(verified['runtime']['image_id'],binaries(candidate))
        p.base.health();p.r.closed_ports();p.unchanged(before)
        assert current['started_at']==verified['runtime']['started_at'] and p.r.state('gateway')['State']['Running']
        p.save(folder/'deployed.json',{**verified,'runtime':current,'checks':checks,'gateway_open':True,
            'source_revision':m['source_revision'],'database_restored':False,'client_update_required':False,
            'owner_gameplay_accepted':False,'zone_only':True,'new_sql_migrations':0})
        print('Keeper repair deployed for live QA; access restored; no client update.' if candidate else 'Compatible prior Stats runtime restored; Keeper repair is not active.',flush=True)
    except BaseException:p.h.hold(folder);raise


def main():
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','rollback','open'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert p.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'rollback':rollback,'open':open_access}[action]()


if __name__=='__main__':main()
