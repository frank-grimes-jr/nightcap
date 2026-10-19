"""Documented restart entrypoint: authenticate and reselect the new image under locks."""
import fcntl
import os
import sys
from pathlib import Path

STAGE=Path('/opt/nightcap/releases/thj-parity-20261018')
sys.path.insert(0,str(STAGE/'rule-notes-recovery'))
import resume_rule_notes as recovery
op=recovery.op

assert __debug__;os.umask(0o077);op.initialize()
with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
    p=recovery.checked();recovery.closed()
    expected={**op.manifest()['base_hashes'],**{'bin/'+n:h for n,h in op.binaries().items()}}
    assert op.r.image_hashes(p['new_image_id'])==expected
    op.save(recovery.REPAIR/'image-reselection.json',{'image':p['new_image_id'],
            'hashes':expected,'entrypoint_sha256':op.sha(Path(__file__))})
    op.r.select(p['new_image_id'])
    recovery.resume()
