"""Retain the exact failed isolated-loader attempt before a bounded retry."""
import argparse,fcntl,importlib.util,os
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/classic-dungeons-rewards-20261022')
spec=importlib.util.spec_from_file_location('rollout',STAGE/'rollout.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
parser=argparse.ArgumentParser()
parser.add_argument('--cause',choices=('isolated-loader-memory','clone-foreign-keys'),required=True)
args=parser.parse_args()
assert __debug__;os.umask(0o077);op.initialize()
with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (op.ROOT/'private/gm-maintenance.json').exists()
    assert {p.name for p in op.EVIDENCE.iterdir()}=={'preflight-started.json','candidate-image.json'}
    p=op.load('preflight-started.json');assert p['manifest_sha256']==op.sha(STAGE/'manifest.json')
    op.unchanged(p);assert all(op.r.compact(s)==v for s,v in p['services'].items())
    assert op.sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE 'nightcap_classic_stage_%';").strip()=='0'
    assert op.sql("SELECT COUNT(*) FROM mysql.user WHERE User LIKE 'ncr_%';").strip()=='0'
    runtime=STAGE/'rehearsal-runtime'
    assert not (runtime/'eqemu_config.json').exists() and not (runtime/'shared/items').exists()
    assert (runtime/'before.log').is_file() and not (runtime/'after.log').exists()
    assert op.sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
    archive=STAGE/'attempts'/args.cause;archive.mkdir(parents=True,exist_ok=False)
    op.EVIDENCE.rename(archive/'evidence');runtime.rename(archive/'rehearsal-runtime')
    print('Failed preflight retained; all live services/content unchanged.',flush=True)
