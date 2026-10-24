"""Owner-approved two-field live content update; no process restart/reload.

The runner injects CAPTURE_SOURCE, EXPECTED and FORWARD from reviewed main files.
Fail closed if any worker has Paineel loaded. Never replay after an uncertain write.
"""
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/hole-keyless-passage-20261024')

PROBE = r'''
import json
from pathlib import Path
rows=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   name=(p/'comm').read_text().strip()
   if name in ('zone','world'):
    logs=sorted(set(str(f.resolve()) for f in (p/'fd').iterdir() if '/logs/' in str(f.resolve())))
    rows.append([name,int(p.name),(p/'stat').read_text().rsplit(')',1)[1].split()[19],logs])
  except FileNotFoundError:pass
assert sum(r[0]=='zone' for r in rows)==12
assert sum(r[0]=='world' for r in rows)==1
assert all(r[3] for r in rows if r[0]=='zone')
assert not any('paineel' in s.lower() for r in rows for s in r[3]), 'Paineel loaded: use targeted reload plan'
print(json.dumps(sorted(rows)))
'''


def command(args, **kwargs):
    return subprocess.check_output(args, cwd=ROOT, text=True, timeout=60, **kwargs)


def runtime():
    processes = json.loads(command(['docker','compose','exec','-T','game','python3','-c',PROBE]))
    ids = command(['docker','compose','ps','-aq']).split()
    services = json.loads(command(['docker','inspect',*ids]))
    assert len(services) == 5
    assert all(s['State']['Running'] and not s['State'].get('Paused') and
               s['State'].get('Health',{}).get('Status','healthy') == 'healthy' for s in services)
    return {'processes': processes, 'services': sorted(
        [s['Id'],s['Image'],s['State']['StartedAt'],s['RestartCount']] for s in services)}


def execute():
    os.umask(0o077)
    namespace = {'__name__': 'capture'}
    exec(CAPTURE_SOURCE, namespace)
    capture = namespace['capture']
    assert not (ROOT/'private/gm-maintenance.json').exists()
    before_runtime = runtime()
    before = capture()
    assert before['doors'] == EXPECTED['doors'] and before['keys'] == EXPECTED['keys'], 'Content drift'
    assert shutil.disk_usage(ROOT).free > 350 * 1024**2, 'Insufficient backup reserve'
    OUT.mkdir(mode=0o700)
    (OUT/'before.json').write_text(json.dumps(before,indent=2)+'\n')
    (OUT/'forward.sql').write_text(FORWARD)
    backup = OUT/'peq-before.sql.gz'
    with (OUT/'backup-stderr.log').open('wb') as errors, gzip.open(backup,'xb') as target:
        proc = subprocess.Popen(['docker','compose','exec','-T','db','mariadb-dump',
            '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction',
            '--quick','--routines','--events','--triggers','peq'],cwd=ROOT,stdout=subprocess.PIPE,stderr=errors)
        try:
            shutil.copyfileobj(proc.stdout,target)
            assert proc.wait(timeout=240) == 0, 'Backup failed; see private stderr'
        finally:
            proc.stdout.close()
            if proc.poll() is None: proc.terminate(); proc.wait(timeout=10)
    with gzip.open(backup,'rb') as check:
        digest=hashlib.sha256();size=0
        for chunk in iter(lambda:check.read(1024**2),b''):
            digest.update(chunk);size+=len(chunk)
    assert size > 1000000
    assert capture()['doors'] == before['doors']
    runtime()  # Every zone must still exclude Paineel immediately before commit.
    (OUT/'started.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'main':'7f126acb','backup_bytes':backup.stat().st_size,'backup_uncompressed_sha256':digest.hexdigest()}))
    command(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','peq'],input=FORWARD)
    after=capture()
    expected=json.loads(json.dumps(before['doors']))
    next(d for d in expected if d['id']==10599).update(keyitem=0,lockpick=0)
    assert after['doors']==expected and after['keys']==before['keys'], 'Post-write preservation mismatch'
    time.sleep(2)
    after_runtime=runtime()
    assert after_runtime['services']==before_runtime['services'], 'Service lifetime changed'
    assert [r[:3] for r in after_runtime['processes']]==[r[:3] for r in before_runtime['processes']], 'Native process lifetime changed'
    command(['docker','compose','exec','-T','game','python3','/opt/nightcap/start.py','--health'])
    result={'applied_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'main':'7f126acb',
        'door':next(d for d in after['doors'] if d['id']==10599),'preserved_other_doors':len(expected)-1,
        'changed_fields':['lockpick','keyitem'],'backup_verified':True,'backup_bytes':backup.stat().st_size,
        'paineel_unloaded_before_and_after':True,'reload':'next normal Paineel boot reads the committed DB',
        'native_and_service_lifetimes_unchanged':True,'health_passed':True,'player_acceptance':False}
    (OUT/'after.json').write_text(json.dumps(after,indent=2)+'\n')
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm): fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(execute(),indent=2))
