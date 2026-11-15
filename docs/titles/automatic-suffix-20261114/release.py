"""Guarded zone-only upgrade of the active title runtime; no SQL migration."""
import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import re
from pathlib import Path
import sys

STAGE=Path(__file__).resolve().parent
PREVIOUS=STAGE.parent/'titles-live-20261114-v1'
REST=STAGE.parent/'post-combat-regen-20261114-v1'
ROOT=Path('/opt/nightcap/deploy/production')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def initialize():
    previous=load('active_title_predecessor',PREVIOUS/'release.py')
    op=previous.initialize()
    m=op.read(STAGE/'manifest.json')
    assert STAGE.name==m['stage']=='titles-automatic-suffix-20261114-v1'
    assert re.fullmatch('[0-9a-f]{40}',m['source_revision'])
    assert op.sha(PREVIOUS/'release.py')==m['title_operator']
    assert op.sha(REST/'release.py')==m['prior_operator']
    assert op.sha(REST/'manifest.json')==m['prior_manifest']
    assert op.sha(REST/'evidence/activation/deployed.json')==m['prior_receipt']
    assert set(m['files'])=={'release.py','build.json','bin/zone'}
    for name,pin in m['files'].items():
        path=STAGE/name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and op.sha(path)==pin,name
    title_dep=op.read(op.ACTIVE/'deployed.json')
    rest=op.read(REST/'manifest.json');dep=op.read(REST/'evidence/activation/deployed.json')
    assert set(rest['files'])=={'release.py','forward.sql','build.json','bin/world','bin/zone'}
    for name,pin in rest['files'].items():
        path=REST/name
        assert not path.is_symlink() and path.resolve().is_relative_to(REST) and op.sha(path)==pin,name
    assert rest['image']==title_dep['image']
    expected={**rest['base_hashes'],**{'bin/'+k:v for k,v in dep['binaries'].items()}}
    assert expected==m['base_hashes']
    assert dep['gateway_open'] and dep['image']==m['base_image_id']
    assert title_dep['client_release']==m['client_release']==2026111301
    assert title_dep['client_channel_sha256']==rest['channel']==m['client_channel_sha256']
    assert op.r.image_hashes(dep['image'])==m['base_hashes']
    build=op.read(STAGE/'build.json')
    assert build['status']=='PASS' and build['profile']=='shipping' and build['link_input_count']==144
    assert build['baseline']==m['base_hashes']['bin/zone']=='d9ab889ad7f9c40a7e3066810b201f802f211c2c2d870637d4d775e6f691ca0b'
    assert build['zone']==m['binaries']['zone']==m['files']['bin/zone']!=build['baseline']
    assert set(build['units'])=={'titles','client_packet','client_process','exp','dungeon_service','task_manager','task_client_state'}
    assert all(v['source_reproduction']=='exact' and v['predecessor']==v['recompiled_predecessor']!=v['candidate'] for v in build['units'].values())
    assert set(m['binaries'])=={'zone'}
    # The previous migration wrapper normalizes its one added command against
    # its pre-migration preflight. This release changes no commands or schema:
    # restore actual full content hashing and retain independent title guards.
    restore_title_migration(op)
    op.STAGE=op.p.STAGE=STAGE
    op.EVIDENCE=op.p.EVIDENCE=STAGE/'evidence'
    op.ACTIVE=op.EVIDENCE/'activation'
    op.p.TAG='nightcap-game:'+STAGE.name
    op.m=op.p.m=m
    install_guards(op)
    return op


def restore_title_migration(op):
    closure=inspect.getclosurevars(op.p.a.content).nonlocals
    assert set(closure)=={'state','content_original','op','installed'}
    assert closure['state'] is op.title_state
    op.p.a.content=closure['content_original']
    op.r.database_backup=op.title_original_backup


def title_data(op):
    result={}
    for table,columns in [('nightcap_title_counters','character_id,counter_id,value'),
                          ('nightcap_title_awards','character_id,title_id,earned_at')]:
        rows=op.prior.sql('SELECT '+columns+' FROM '+table+' ORDER BY '+columns)
        result[table]=dict(sha256=hashlib.sha256(rows.encode()).hexdigest(),rows=len(rows.splitlines()))
    return result


def install_guards(op):
    original_unchanged=op.p.unchanged
    original_backup=op.r.database_backup
    snapshot=op.ACTIVE/'title-state-before.json'

    def unchanged(before,after_open=False,**kwargs):
        original_unchanged(before,after_open=after_open,**kwargs)
        op.title_state()
        if not after_open and snapshot.exists():
            assert title_data(op)==op.read(snapshot),'Closed title awards/counters drift'

    def backup():
        state=op.r.state('game')['State']
        assert not state['Running'] and not state['OOMKilled'] and state['ExitCode']==0
        assert not op.r.compact('gateway')['running']
        assert not snapshot.exists(),'Existing stopped snapshot: inspect, never replay'
        op.title_state()
        data=title_data(op)
        value=original_backup()
        assert value['gzip_integrity'] and op.sha(Path(value['path']))==value['sha256']
        assert title_data(op)==data
        op.p.save(snapshot,data)
        return value

    op.p.unchanged=unchanged
    op.r.database_backup=backup
    op.title_original_backup=original_backup


def deploy(op):
    op.title_state()
    path=PREVIOUS.parent/'heroic-cast-sources-20261114-v1/maintenance.py'
    assert op.sha(path)==op.m['maintenance']
    maintenance=load('automatic_title_maintenance',path)
    maintenance.release=sys.modules[__name__]
    maintenance.REVISION=op.m['source_revision']
    maintenance.deploy(op)


def recover_closed(op):
    assert not (op.ACTIVE/'opening.json').exists() and not (op.ACTIVE/'deployed.json').exists()
    assert not op.r.compact('gateway')['running']
    original_players=op.p.a.prior.players
    def players():
        state=op.r.state('game')['State']
        if not state['Running']:
            assert state['ExitCode']==0 and not state['OOMKilled']
            assert not op.r.compact('gateway')['running']
            return 0
        return original_players()
    assert players()==0
    op.r.database_backup=op.title_original_backup
    op.p.a.prior.players=players
    try:op.recover_closed()
    finally:op.p.a.prior.players=original_players


if __name__=='__main__':
    import fcntl
    assert __debug__;os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('action',choices=['deploy','verify','recover-closed']);args=p.parse_args()
    op=initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert op.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        if args.action=='deploy':deploy(op)
        elif args.action=='recover-closed':recover_closed(op)
        else:
            op.title_state()
            print(json.dumps(op.verify_open()))
