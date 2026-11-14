"""One-shot title activation over the exact retained fixed-AA runtime."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

STAGE=Path(__file__).resolve().parent
PREVIOUS=STAGE.parent/'fixed-aa-duration-20261114-v1'
ROOT=Path('/opt/nightcap/deploy/production')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def initialize():
    previous=load('fixed_predecessor',PREVIOUS/'release.py')
    op=previous.initialize()
    m=op.read(STAGE/'manifest.json')
    assert STAGE.name==m['stage']=='titles-live-20261114-v1'
    assert re.fullmatch('[0-9a-f]{40}',m['source_revision'])
    assert op.sha(PREVIOUS/'release.py')==m['prior_operator']
    assert op.sha(PREVIOUS/'evidence/activation/deployed.json')==m['prior_receipt']
    assert op.sha(PREVIOUS.parent/'classic-prismatic-20261114-v1/evidence/activation/deployed.json')==m['prismatic_receipt']
    assert set(m['files'])=={'release.py','schema.py','schema-expected.json','setup.sql','commands-before.json','build.json','bin/zone'}
    for name,pin in m['files'].items():
        file=STAGE/name
        assert not file.is_symlink() and file.resolve().is_relative_to(STAGE) and op.sha(file)==pin,name
    dep=op.read(op.ACTIVE/'deployed.json')
    assert dep['gateway_open'] and dep['image']==m['base_image_id']
    assert dep['client_release']==m['client_release']==2026111301
    assert dep['client_channel_sha256']==m['client_channel_sha256']
    assert op.r.image_hashes(dep['image'])==m['base_hashes']
    build=op.read(STAGE/'build.json')
    assert build['status']=='PASS' and build['baseline']==m['base_hashes']['bin/zone']=='82d5e2d2573a440beac75dabce41f9271a20d579ebc9d6bf38a32a6ad0c1c314'
    assert build['zone']==m['binaries']['zone']==m['files']['bin/zone']=='f35b4e3db6dd87f2eb5e62a916543508988df87c53ae9355ee2f4fae53fe2602'
    assert build['link_input_count']==144 and build['command_archive']['other_members_preserved']==11
    assert set(build['units'])=={'attack','client','titles'}
    assert all(v['predecessor']==v['recompiled_predecessor']!=v['candidate'] for v in build['units'].values())
    assert set(m['binaries'])=={'zone'}
    op.STAGE=op.p.STAGE=STAGE
    op.EVIDENCE=op.p.EVIDENCE=STAGE/'evidence'
    op.ACTIVE=op.EVIDENCE/'activation'
    op.p.TAG='nightcap-game:'+STAGE.name
    op.m=op.p.m=m
    schema=load('title_activation_schema',STAGE/'schema.py')
    install_guards(op,schema)
    return op


def install_guards(op,schema):
    sql=op.prior.sql
    expected=op.read(STAGE/'schema-expected.json')
    commands=op.read(STAGE/'commands-before.json')
    content_original=op.p.a.content
    saved_original=op.p.base.saved_state
    backup_original=op.r.database_backup
    installed=op.ACTIVE/'titles-sql-installed.json'
    started=op.ACTIVE/'titles-sql-started.json'
    recovered=op.ACTIVE/'titles-disabled-for-recovery.json'

    def state():
        if recovered.exists():
            assert schema.structure(sql)==expected
            assert schema.settings(sql)==[dict(id=1,catalog_version=1,enabled=0)]
            assert schema.commands(sql)==commands
            assert sql('SELECT COUNT(*) FROM titles WHERE id>=1900000000 AND id<1900001000').strip()=='0'
        elif installed.exists():
            schema.require_installed(sql,expected,1)
            assert schema.without_title(schema.commands(sql))==commands
        else:
            assert not started.exists(),'Uncertain SQL write: hold closed and inspect; do not replay'
            schema.require_uninstalled(sql)
            assert schema.commands(sql)==commands

    def content():
        state()
        result=content_original()
        if installed.exists():
            # Compare every unrelated command row before normalizing this one
            # independently validated, additive player command in old guards.
            before=op.read(op.EVIDENCE/'preflight.json')['content']
            result['command_settings/all']=before['command_settings/all']
        return result

    def saved():
        return {k:v for k,v in saved_original().items() if k not in schema.TABLES}

    def backup_and_install():
        assert not started.exists() and not installed.exists(),'Terminal/uncertain migration: do not replay'
        backup=backup_original()
        assert backup['gzip_integrity'] and op.sha(Path(backup['path']))==backup['sha256']
        assert not op.r.compact('game')['running'] and not op.r.compact('gateway')['running']
        assert op.p.a.prior.players()==0
        state()
        op.p.save(started,dict(backup=backup,source=op.m['source_revision']))
        schema.install(sql,(STAGE/'setup.sql').read_text(),expected,commands)
        op.p.save(installed,dict(enabled=True,catalog_version=1,backup_sha256=backup['sha256'],restored_player_snapshot=False))
        return backup

    op.p.a.content=content
    op.p.base.saved_state=saved
    op.r.database_backup=backup_and_install
    op.title_state=state
    op.title_schema=schema
    op.title_original_backup=backup_original


def recover_closed(op):
    """Only before opening/activity: disable owned additions, retain data, fresh backup."""
    assert (op.ACTIVE/'started.json').exists()
    assert not (op.ACTIVE/'opening.json').exists() and not (op.ACTIVE/'deployed.json').exists()
    assert not (op.ACTIVE/'titles-recovery-started.json').exists()
    assert not op.r.compact('gateway')['running'] and op.p.a.prior.players()==0
    assert (op.ACTIVE/'titles-sql-installed.json').exists(),'Partial SQL needs inspection and forward completion'
    op.title_state()
    sql=op.prior.sql
    assert sql('SELECT COUNT(*) FROM nightcap_title_awards').strip()=='0','Title activity: forward repair required'
    assert sql('SELECT COUNT(*) FROM nightcap_title_counters').strip()=='0','Title activity: forward repair required'
    op.p.save(op.ACTIVE/'titles-recovery-started.json',dict(restored_player_snapshot=False))
    assert sql('UPDATE nightcap_title_settings SET enabled=0 WHERE id=1 AND catalog_version=1 AND enabled=1; SELECT ROW_COUNT()').strip()=='1'
    assert sql("DELETE FROM command_settings WHERE command='titles' AND access=0 AND aliases=''; SELECT ROW_COUNT()").strip()=='1'
    op.p.save(op.ACTIVE/'titles-disabled-for-recovery.json',dict(enabled=False,preserved_tables=True))
    op.title_state()
    op.r.database_backup=op.title_original_backup
    op.recover_closed()


def deploy(op):
    op.title_state()
    file=PREVIOUS.parent/'heroic-cast-sources-20261114-v1/maintenance.py'
    assert op.sha(file)==op.m['maintenance']
    maintenance=load('title_maintenance',file)
    maintenance.release=sys.modules[__name__]
    maintenance.REVISION=op.m['source_revision']
    maintenance.deploy(op)


if __name__=='__main__':
    import fcntl
    assert __debug__
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('deploy','verify','recover-closed'))
    action=parser.parse_args().action
    op=initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert op.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        if action=='deploy':deploy(op)
        elif action=='recover-closed':recover_closed(op)
        else:
            op.title_state()
            result=op.verify_open();result['title_catalog_enabled']=True
            print(json.dumps(result))
