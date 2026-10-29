"""Publish approved keyless-door guidance after verified database/runtime activation.

Adapted from the October28 Bazaar owner-QA publisher. Requires a fresh activation
guard, immutable package, exact current baseline and unchanged service identities.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from capture_baseline import SSH, PREVIOUS, remote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ART = ROOT / 'work/keyless-wiki'
RELEASE = '20261029-keyless-doors-v1'
ALLOWED = {'features.html', 'unreleased.html', 'recent-changes.html', 'travel.html',
           'zone-hole.html', 'search-index.json'}


def check_package():
    baseline = json.loads((HERE / 'wiki-baseline.json').read_text())
    files = [ART / (RELEASE + '.tar.gz'), ART / (RELEASE + '.tar.json')]
    files += [ROOT / 'wiki' / name for name in ['update.py', 'deploy.py', 'test_update.py', 'test_deploy.py', 'nginx.conf']]
    manifest = json.loads(files[1].read_text())
    assert len(manifest) == 499 and set(manifest) == set(baseline)
    changed = {n for n, h in manifest.items() if baseline[n] != h}
    assert changed == ALLOWED, (changed - ALLOWED, ALLOWED - changed)
    return baseline, files, changed


def main():
    assert not (HERE / 'wiki-publication.json').exists(), 'Inspect existing receipt before replay'
    activation = json.loads((HERE / 'activation-guard.json').read_text())
    assert activation['verified'] is True and activation['channel_sha256']
    assert activation['runtime_receipt']
    baseline, files, changed = check_package()
    target_guard = f'''from pathlib import Path
import json,hashlib,subprocess
base=Path('/opt/nightcap/deploy/production')
def target_guard():
 assert hashlib.sha256(Path({activation['runtime_receipt']!r}).read_bytes()).hexdigest()=={activation['runtime_receipt_sha256']!r},'Runtime activation receipt changed'
 assert hashlib.sha256((base/'data/public/channel.json').read_bytes()).hexdigest()=={activation['channel_sha256']!r},'Signed channel changed'
 for name in ['game','gateway','db','web','tunnel']:
  cid=subprocess.check_output(['docker','compose','ps','-aq',name],cwd=base,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled'],name
  if name in ['game','db']:assert row['State']['Health']['Status']=='healthy',name
  expected={activation['services']!r}['/nightcap-production-'+name+'-1']
  assert row['Id']==expected['id'] and row['Image']==expected['image'] and row['RestartCount']==expected['restarts'],'Service identity changed'
  assert row['State']['StartedAt']==expected['start'],'Service lifetime changed'
target_guard()
'''
    before = remote(target_guard + '''pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert before['release'] == PREVIOUS, 'Concurrent publication; reconcile content first'
    assert before['manifest'] == baseline, 'Reviewed public baseline changed'
    expected_state = json.loads((HERE / 'baseline-state.json').read_text())
    assert before['config_sha256'] == expected_state['config_sha256'], 'Web config changed'
    (HERE / 'wiki-before.json').write_text(json.dumps(before, indent=2) + '\n')
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload = '/home/ubuntu/wiki-keyless-doors-20261029-v1'
    stage = '/opt/nightcap/releases/wiki-keyless-doors-20261029-v1'
    subprocess.run(SSH + ['mkdir -m 700 ' + upload], check=True, timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *SSH[1:-1], *map(str, files), SSH[-1] + ':' + upload + '/'], check=True, timeout=120)
    report = remote(f'''from pathlib import Path
import json,hashlib,subprocess,shutil,fcntl
upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
for name,digest in pins.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=60)
assert tests.returncode==0,tests.stderr
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 exec({target_guard!r})
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{files[0].name!r}),str(stage/{files[1].name!r}),{RELEASE!r},{PREVIOUS!r},{before['config_sha256']!r}],timeout=180))
 target_guard()
result['linux_tests']=tests.stderr;print(json.dumps(result))
''')
    assert report['result'] == 'PASS' and report['files'] == 499
    report.update(changed_files=sorted(changed), preserved_files=499-len(changed),
                  baseline_source=PREVIOUS, package_sha256=pins[files[0].name],
                  scope='194 keyless doors across 48 zones; owner gameplay acceptance open')
    (HERE / 'wiki-publication.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'result': report['result'], 'release': RELEASE, 'files': 499, 'changed': len(changed)}))


if __name__ == '__main__':
    main()
