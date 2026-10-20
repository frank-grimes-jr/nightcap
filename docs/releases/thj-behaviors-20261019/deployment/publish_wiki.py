"""Publish the repair notice using the unchanged guarded wiki updater."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'thj-all-class-aa-20261019/deployment'))
from remote import SSH
HERE=Path(__file__).resolve().parent
ARTIFACTS=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019')
STAGE='/opt/nightcap/releases/thj-behaviors-live-20261019'

ROOT = HERE.parents[3]
RELEASE = '20261019-thj-behaviors-live-v1'


def run(source, timeout=180):
    result = subprocess.run(SSH+['sudo -n python3 -'], input=source, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    return result.stdout


def main():
    before = json.loads(run('''
import hashlib,json
from pathlib import Path
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current'
assert pointer.is_symlink()
release=pointer.readlink().name
manifest=json.loads((base/'website-history'/release/'manifest.json').read_text())
print(json.dumps({'release':release,'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest(),'manifest':manifest}))
'''))
    assert before['release'] == '20261019-thj-behaviors-candidate-v1', 'Wiki baseline changed'
    files = [ARTIFACTS/(RELEASE.replace('20261019-', 'wiki20261019-')+'.tar.gz'),
             ARTIFACTS/(RELEASE.replace('20261019-', 'wiki20261019-')+'.tar.json'),
             ROOT/'wiki/update.py', ROOT/'wiki/deploy.py']
    manifest = json.loads(files[1].read_text(encoding='utf-8'))
    assert len(manifest) == 465 and set(manifest) == set(before['manifest'])
    changed = sorted(name for name in manifest if manifest[name] != before['manifest'][name])
    assert set(changed) == {'index.html','features.html','multiclass.html','combat.html','unreleased.html','recent-changes.html','search-index.json','equipment.html','ascension.html','item-upgrades.html','pets.html','getting-started.html'}, changed
    (HERE/'wiki-before.json').write_text(json.dumps(before,indent=2)+'\n')
    pins = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload = '/home/ubuntu/thj-behaviors-live-wiki-20261019'
    # Only this dedicated upload folder is created; it contains no private seed.
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),
                    SSH[-1]+':'+upload+'/'],check=True,timeout=120)
    source = f'''
import hashlib,json,shutil,subprocess
from pathlib import Path
upload=Path({upload!r}); stage=Path({(STAGE+'/wiki')!r}); pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(parents=True,exist_ok=False)
for name,digest in pins.items():
    p=upload/name
    assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
    shutil.copyfile(p,stage/name)
    assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
result=subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{files[0].name!r}),str(stage/{files[1].name!r}),{RELEASE!r},{before['release']!r},{before['config_sha256']!r}],timeout=150)
print(result.decode())
'''
    report = json.loads(run(source))
    assert report['result'] == 'PASS' and report['files'] == 465
    report['changed_files'] = changed
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
