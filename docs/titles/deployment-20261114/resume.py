"""One bounded continuation of the authenticated pre-SQL stopped-world RPC hold.

The original immutable operator is retained. Never rerun deploy or this terminal
continuation; later failures remain held for fresh inspection.
"""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

STAGE=Path('/opt/nightcap/releases/titles-live-20261114-v1')
HELD='held-1794691016729160326.json'
HOLD_SHA='5a9fb9bf2460d2fe2a4aad86d2435194de987f165250a1a61e782bb32d727cdc'


def checkpoint(op):
    p,r=op.p,op.r
    folder=op.ACTIVE
    assert not (folder/'resume-stopped-rpc').exists()
    assert set(f.name for f in folder.glob('held-*.json'))=={HELD}
    assert op.sha(folder/HELD)==HOLD_SHA
    assert not any((folder/n).exists() for n in ['titles-sql-started.json','titles-sql-installed.json','opening.json','deployed.json','verified-closed.json','backup.json'])
    assert not r.compact('game')['running'] and r.compact('game')['image_id']==op.m['base_image_id']
    assert not r.compact('gateway')['running']
    state=r.state('game')['State']
    assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
    op.title_state()
    assert p.a.prior.saved()==op.read(folder/'stopped-state.json')
    before=op.read(op.EVIDENCE/'preflight.json')
    assert before['manifest_sha256']==op.sha(STAGE/'manifest.json')
    p.unchanged(before);p.startup.startup_guards()
    # Authenticate the first backup without reusing its exclusive output path.
    old=folder/'private-backup/peq-before.sql.gz';size=0;tail=b''
    with gzip.open(old,'rb') as stream:
        while chunk:=stream.read(1024*1024):size+=len(chunk);tail=(tail+chunk)[-4096:]
    assert size>1000000 and b'-- Dump completed on' in tail
    return before,dict(sha256=op.sha(old),uncompressed_bytes=size)


def resume(op):
    p,r=op.p,op.r;folder=op.ACTIVE
    before,old_backup=checkpoint(op)
    work=folder/'resume-stopped-rpc';work.mkdir(mode=0o700)
    p.save(work/'started.json',dict(reason='Player-count RPC called after clean world stop',original_hold_sha256=HOLD_SHA,first_backup=old_backup,restored_player_snapshot=False))
    try:
        r.STAGE=work;p.base.EVIDENCE=folder
        backup=op.title_original_backup()
        assert backup['gzip_integrity'] and op.sha(Path(backup['path']))==backup['sha256']
        p.save(folder/'backup.json',backup)
        saved=op.read(folder/'stopped-state.json')
        assert p.a.prior.saved()==saved
        op.title_state()
        p.save(folder/'titles-sql-started.json',dict(backup=backup,source=op.m['source_revision'],continuation=True))
        op.title_schema.install(op.prior.sql,(STAGE/'setup.sql').read_text(),op.read(STAGE/'schema-expected.json'),op.read(STAGE/'commands-before.json'))
        p.save(folder/'titles-sql-installed.json',dict(enabled=True,catalog_version=1,backup_sha256=backup['sha256'],restored_player_snapshot=False))
        assert p.a.prior.saved()==saved
        expected=p.base.boot_state(saved);p.unchanged(before);p.contract()
        r.select(before['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        first=r.running(before['image'],p.binaries());p.base.health();time.sleep(8)
        current=r.running(before['image'],p.binaries());assert first['started_at']==current['started_at']
        assert p.a.prior.saved()==expected
        rotation=p.market.verify_market(op.read(folder/'market-before.json'),current['started_at'])
        p.unchanged(before);checks=p.contract();p.base.health();r.closed_ports()
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        assert not any(x in logs for x in ['MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement','Earned title list unavailable','Earned title kill credit failed','Earned skill title pending refresh'])
        p.save(folder/'verified-closed.json',dict(runtime=current,game=r.compact('game'),checks=checks,market=rotation,continuation=True))
        # Preserve the exact diagnosed hold as evidence only after every closed
        # verification has passed. A new/different hold cannot be normalized.
        assert set(f.name for f in folder.glob('held-*.json'))=={HELD} and op.sha(folder/HELD)==HOLD_SHA
        resolved=work/'resolved-holds';resolved.mkdir(mode=0o700)
        (folder/HELD).rename(resolved/HELD)
        p.save(work/'resolved.json',dict(original_hold_sha256=HOLD_SHA,closed_verification_passed=True))
        op.open_access()
    except BaseException:
        p.h.hold(folder);raise


if __name__=='__main__':
    import fcntl
    assert __debug__;os.umask(0o077)
    spec=importlib.util.spec_from_file_location('titles_resume_runtime',STAGE/'release.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    op=module.initialize()
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists()
        assert op.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        resume(op)
