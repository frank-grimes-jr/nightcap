"""Publish the owner-confirmed wiki wording as a guarded immutable release."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki')
ARTIFACTS = Path('E:/EQ_Local_Dev/artifacts/hate-keeper-commonlands-20261022')
RELEASE = '20261022-hate-keeper-confirmed-v1'
PREVIOUS = '20261022-hate-keeper-v1'
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', str(Path.home()/'.ssh/nightcap_ovh'),
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', 'ubuntu@135.148.47.202']


def run(source):
    result = subprocess.run(SSH + ['sudo -n python3 -'], input=source, text=True,
                            capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    return json.loads(result.stdout)


def main():
    before = run('''
import hashlib,json
from pathlib import Path
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current'
assert pointer.is_symlink()
release=pointer.readlink().name
manifest=json.loads((base/'website-history'/release/'manifest.json').read_text())
print(json.dumps({'release':release,'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest(),'manifest':manifest}))
''')
    assert before['release'] == PREVIOUS, 'Concurrent publication: reconcile before proceeding'
    archive = ARTIFACTS / (RELEASE + '.tar.gz')
    manifest_path = ARTIFACTS / (RELEASE + '.tar.json')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert len(manifest) == len(before['manifest']) == 466
    changed = sorted(name for name in manifest if manifest[name] != before['manifest'].get(name))
    expected = {name + '.html' for name in ('dungeon-modes', 'tunnel', 'travel', 'features', 'index', 'unreleased', 'recent-changes')} | {'search-index.json'}
    assert set(changed) == expected, changed
    files = [archive, manifest_path]
    files += [ROOT / 'wiki' / name for name in ['update.py', 'deploy.py', 'test_update.py', 'test_deploy.py', 'nginx.conf']]
    (HERE / 'wiki-before-confirmed.json').write_text(json.dumps(before, indent=2) + '\n', encoding='utf-8')
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload = '/home/ubuntu/hate-keeper-wiki-confirmed-20261022-v1'
    stage = '/opt/nightcap/releases/hate-keeper-wiki-confirmed-20261022-v1'
    subprocess.run(SSH + ['mkdir -m 700 ' + upload], check=True, timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *SSH[1:-1], *map(str, files), SSH[-1] + ':' + upload + '/'], check=True, timeout=120)
    report = run(f'''
import hashlib,json,shutil,subprocess
from pathlib import Path
upload=Path({upload!r}); stage=Path({stage!r}); pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
for name,digest in pins.items():
    p=upload/name
    assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
    shutil.copyfile(p,stage/name)
    assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=60)
assert tests.returncode==0,tests.stderr
result=subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),str(stage/{manifest_path.name!r}),{RELEASE!r},{PREVIOUS!r},{before['config_sha256']!r}],timeout=180)
report=json.loads(result);report['linux_tests']=tests.stderr;print(json.dumps(report))
''')
    assert report['result'] == 'PASS' and report['files'] == 466
    report.update(changed_files=changed, previous_release=PREVIOUS,
                  package_sha256=pins[archive.name], owner_acceptance='Confirmed')
    (HERE / 'wiki-publication-confirmed.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': report['result'], 'release': RELEASE, 'files': report['files'], 'changed': len(changed)}))


if __name__ == '__main__':
    main()
