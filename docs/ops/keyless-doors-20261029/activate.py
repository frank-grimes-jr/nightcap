"""One-shot owner-authorized content update with backup and empty-zone refresh.

Runner injects CAPTURE_SOURCE, RUNTIME_SOURCE, EXPECTED, FORWARD, ROLLBACK,
MAIN_REVISION and EXPECTED_IMAGE. Never replay an existing/uncertain operation.
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
OUT = Path('/opt/nightcap/backups/keyless-doors-20261029')


def run(args, source=None, timeout=90):
    result = subprocess.run(args, cwd=ROOT, input=source, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    return result.stdout


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def services():
    names = ['nightcap-production-' + name + '-1' for name in ('game','db','gateway','web','tunnel')]
    rows = json.loads(run(['docker', 'inspect', *names]))
    assert all(r['State']['Running'] and not r['State']['OOMKilled'] and
               r['State'].get('Health', {}).get('Status', 'healthy') == 'healthy' for r in rows)
    return {r['Name']: {'id': r['Id'], 'image': r['Image'], 'start': r['State']['StartedAt'],
                       'restarts': r['RestartCount']} for r in rows}


def game(source):
    return json.loads(run(['docker','compose','exec','-T','game','python3','-'], source))


def runtime(mode, expected_targets=None, expected_locks=None):
    affected = sorted({r['zone'] for r in EXPECTED['doors'] if r['keyitem'] or r['lockpick']})
    return game('AFFECTED=' + repr(affected) + '\nMODE=' + repr(mode) +
                '\nEXPECTED_TARGETS=' + repr(expected_targets) +
                '\nEXPECTED_LOCKS=' + repr(expected_locks) + '\n' + RUNTIME_SOURCE)


def identities(snapshot):
    return sorted((r['pid'], r['start']) for r in snapshot['workers'])


def target_ids(snapshot):
    return sorted((r['server_id'], r['pid'], r['zone']) for r in snapshot['targets'])


def expected_after(before):
    result = json.loads(json.dumps(before))
    for row in result['doors']:
        row.update(keyitem=0, lockpick=0)
    return result


def execute():
    os.umask(0o077)
    assert not OUT.exists(), 'Existing operation: inspect receipts, do not replay'
    assert not (ROOT/'private/gm-maintenance.json').exists(), 'GM maintenance active'
    namespace = {'__name__': 'capture'}
    exec(CAPTURE_SOURCE, namespace)
    capture = namespace['capture']
    before = capture()
    assert before['doors'] == EXPECTED['doors'], 'Door preimage drift'
    baseline = services()
    assert baseline['/nightcap-production-game-1']['image'] == EXPECTED_IMAGE
    workers = runtime('probe')
    assert 75 not in workers['locks'], 'Paineel already locked by another operation'
    assert {r['zone'] for r in workers['targets']} <= {'paineel'}, 'New affected zone needs static-content review'
    assert shutil.disk_usage(ROOT).free > 256 * 1024**2, 'Insufficient backup reserve'
    OUT.mkdir(mode=0o700)
    save('before.json', before)
    save('services-before.json', baseline)
    save('runtime-before.json', workers)
    for name, data in [('forward.sql', FORWARD), ('rollback.sql', ROLLBACK),
                       ('runtime.py', RUNTIME_SOURCE), ('capture.py', CAPTURE_SOURCE)]:
        (OUT/name).write_text(data)
    backup = OUT/'peq-before.sql.gz'
    with (OUT/'backup-stderr.log').open('wb') as errors, gzip.open(backup,'xb') as target:
        proc = subprocess.Popen(['docker','compose','exec','-T','db','mariadb-dump',
            '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction',
            '--quick','--routines','--events','--triggers','peq'], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=errors)
        try:
            shutil.copyfileobj(proc.stdout, target)
            assert proc.wait(timeout=240) == 0, 'Backup failed; inspect private error log'
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)
    digest = hashlib.sha256()
    size = 0
    with gzip.open(backup, 'rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            digest.update(block)
            size += len(block)
    assert size > 1000000 and shutil.disk_usage(ROOT).free > 128 * 1024**2
    result = {'main': MAIN_REVISION, 'status': 'prepared', 'backup_verified': True,
              'backup_bytes': backup.stat().st_size, 'backup_uncompressed_bytes': size,
              'backup_uncompressed_sha256': digest.hexdigest(), 'owner_gameplay_qa': 'pending'}
    save('result.json', result)
    assert capture()['doors'] == before['doors'], 'Content changed during backup'
    assert services() == baseline, 'Service changed during backup'
    prehold = runtime('probe')
    assert prehold['locks'] == workers['locks'], 'Native lock preimage drift'
    result['admission_locks_before'] = prehold['locks']
    result['status'] = 'admission_hold_requested'
    save('result.json', result)
    result['admission_hold'] = runtime('hold', expected_locks=prehold['locks'])
    result['status'] = 'admission_held_draining'
    save('result.json', result)
    return finish(capture, before, baseline, workers, result)


def finish(capture, before, baseline, workers, result):
    # Native auth expires after two 60-second sweeps. Let already-authorized
    # entries complete/expire before proving the locked target is still empty.
    for _ in range(5):
        time.sleep(25)
        assert services() == baseline
        assert identities(runtime('probe')) == identities(workers)
    fresh = runtime('probe')
    assert identities(fresh) == identities(workers) and target_ids(fresh) == target_ids(workers)
    result.update(status='commit_started', started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save('result.json', result)
    run(['docker','compose','exec','-T','db','mariadb',
         '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','peq'], FORWARD)
    after = capture()
    assert after['doors'] == expected_after(before)['doors'], 'Post-write door mismatch'
    save('after.json', after)
    changed = sum(bool(r['keyitem'] or r['lockpick']) for r in before['doors'])
    result.update(status='committed_reload_pending', changed_doors=changed,
                  preserved_other_doors=len(before['doors']) - changed)
    save('result.json', result)
    reloaded = runtime('reload', target_ids(fresh))
    time.sleep(3)
    verified = runtime('probe')
    assert identities(verified) == identities(workers), 'Worker lifetime changed'
    assert target_ids(verified) == target_ids(workers), 'Loaded target changed during refresh'
    logs = game('before=' + repr(reloaded['targets']) + '''
import json
from pathlib import Path
out={}
for row in before:
 lines=[]
 for filename,offset in row['logs'].items():
  with Path(filename).open('rb') as stream:
   stream.seek(offset)
   lines.extend(stream.read(1024**2).decode(errors='replace').splitlines())
 out[str(row['pid'])]=[s for s in lines if any(w in s for w in ('Reload','[Error]','[Fatal]'))]
print(json.dumps(out))
''')
    for lines in logs.values():
        assert any('Zone Static Data Reloaded' in line for line in lines), 'No native refresh acknowledgment'
        assert not any('[Error]' in line or '[Fatal]' in line for line in lines), 'Reload error'
    assert services() == baseline, 'Service lifetime changed'
    assert capture()['doors'] == after['doors'], 'Final content mismatch'
    run(['docker','compose','exec','-T','game','python3','/opt/nightcap/start.py','--health'])
    result['status'] = 'refreshed_admission_release_pending'
    save('result.json', result)
    result['admission_release'] = runtime('release', expected_locks=result['admission_hold']['after'])
    result.update(status='activated_verified', applied_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  total_doors=len(after['doors']), remaining_locks=0, reload_targets=target_ids(workers),
                  reload_logs=logs, service_and_worker_lifetimes_unchanged=True, health_passed=True,
                  services=baseline, no_restart=True)
    save('result.json', result)
    return result


if __name__ == '__main__':
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(execute(),indent=2))
