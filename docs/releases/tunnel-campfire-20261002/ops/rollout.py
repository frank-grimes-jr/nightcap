"""Pin the reviewed social rollout machinery to the six-resident campfire release."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if not __debug__:raise RuntimeError('Assertions must be enabled')
STAGE=Path(__file__).resolve().parent
sys.path.insert(0,str(STAGE/'tools'))
spec=importlib.util.spec_from_file_location('social_rollout',STAGE/'social_rollout.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
import tunnel_campfire
ops.content=tunnel_campfire
ops.STAGE=STAGE
ops.EVIDENCE=Path('/opt/nightcap/releases/tunnel-campfire-evidence-20261002')
ops.REHEARSAL='nightcap-campfire-rehearsal-20261002'

def manifest():
    assert STAGE==Path('/opt/nightcap/releases/tunnel-campfire-20261002')
    assert Path(__file__).resolve()==STAGE/'rollout.py'
    m=json.loads((STAGE/'manifest.json').read_text())
    for name,sha in m['files'].items():assert ops.digest((STAGE/name).read_bytes())==sha,name
    return m

def rehearse(before,after):
    image=ops.state('db')['Image'];name=ops.REHEARSAL
    assert not ops.out('docker','ps','-aq','--filter','name=^/'+name+'$').strip()
    ops.call('docker','run','-d','--rm','--name',name,'--label','nightcap.release=tunnel-campfire-20261002',
             '--network','none','--memory','1536m','-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1',image)
    try:
        for _ in range(60):
            ready=subprocess.run(['docker','exec',name,'mariadb-admin','-uroot','ping'],capture_output=True)
            daemon=subprocess.run(['docker','exec',name,'cat','/proc/1/comm'],capture_output=True,text=True)
            if ready.returncode==0 and daemon.stdout.strip()=='mariadbd':break
            time.sleep(1)
        else:raise RuntimeError('Isolated database startup timeout')
        ops.call('docker','exec',name,'mariadb','-uroot','-e','CREATE DATABASE peq;')
        ops.call('docker','cp',str(ops.EVIDENCE/'peq-before.sql.gz'),name+':/tmp/backup.sql.gz')
        with (ops.EVIDENCE/'restore-private.log').open('xb') as errors:
            restored=subprocess.run(['docker','exec',name,'bash','-o','pipefail','-c',
                'gzip -dc /tmp/backup.sql.gz | mariadb -uroot peq'],stdout=errors,stderr=errors,timeout=300)
        assert restored.returncode==0,'Restore failed; inspect private host log'
        baseline=ops.load('preservation-before.json')
        assert ops.fingerprints(True)==baseline;ops.exact(before,True)
        print('Full production backup restored and verified in isolation.',flush=True)
        sys.path.insert(0,str(STAGE/'tools/tests'))
        import rehearse_tunnel_campfire as tests
        tests.sql=lambda q,check=True:ops.sql(q,True,False) if not check else ops.checked_test_sql(q)
        checks=tests.run(ops.EVIDENCE/'before-content.json',ops.EVIDENCE/'regression')
        assert len(checks)==16
        ops.sql((ops.EVIDENCE/'forward.sql').read_text(),True);ops.exact(after,True)
        assert ops.fingerprints(True)==baseline
        ops.sql((ops.EVIDENCE/'immediate-rollback.sql').read_text(),True);ops.exact(ops.load('rollback-target.json'),True)
        assert ops.fingerprints(True)==baseline
        ops.save('rehearsal.json',dict(full_backup_restored=True,checks=checks,
            exact_full_database_forward=True,exact_full_database_rollback=True,preserved_tables=len(baseline)))
    finally:
        inspected=json.loads(ops.out('docker','inspect',name))[0]
        assert inspected['Config']['Labels'].get('nightcap.release')=='tunnel-campfire-20261002'
        ops.call('docker','stop',name)
    assert not ops.out('docker','ps','-aq','--filter','name=^/'+name+'$').strip()

ops.manifest=manifest
ops.rehearse=rehearse
verify=ops.verify

if __name__=='__main__':
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','prepare','apply','rollback','verify'])
    getattr(ops,p.parse_args().action)()
