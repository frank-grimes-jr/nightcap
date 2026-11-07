"""Publish only loot guide/history over the freshly reproduced public wiki."""
import hashlib
import json
from pathlib import Path
import subprocess
from ship_client import SSH, remote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ART = ROOT / 'eq-client-dll/build/advanced-loot-release'
WIKI = ART / 'wiki-source/wiki'
RELEASE = '20261107-advanced-loot-v1'


def main():
    verified = json.loads((HERE / 'client-public-verification.json').read_text())
    assert verified['release'] == 2026110605 and verified['hosted']
    publication = json.loads((HERE / 'client-published.json').read_text())
    baseline = json.loads((HERE / 'client-preflight.json').read_text())
    previous = baseline['wiki_release']
    archive = ART / (RELEASE + '.tar.gz')
    manifest_path = archive.with_suffix('.json')
    manifest = json.loads(manifest_path.read_text())
    assert manifest.keys() == baseline['wiki_manifest'].keys() and len(manifest) == 510
    changed = sorted(name for name in manifest if manifest[name] != baseline['wiki_manifest'][name])
    assert changed == ['advanced-loot.html', 'recent-changes.html', 'search-index.json']
    files = [archive, manifest_path] + [WIKI / name for name in (
        'update.py', 'deploy.py', 'test_update.py', 'test_deploy.py', 'nginx.conf')]
    pins = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    upload = '/home/ubuntu/wiki-advanced-loot-20261107-v1'
    stage = '/opt/nightcap/releases/wiki-advanced-loot-20261107-v1'
    subprocess.run(SSH + ['mkdir -m 700 ' + upload], check=True, timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *SSH[1:-1],
                    *map(str, files), SSH[-1] + ':' + upload + '/'], check=True, timeout=300)
    report = remote(f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
base=Path('/opt/nightcap/deploy/production');upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{path.name for path in upload.iterdir()}}==set(pins)
os.umask(0o077);stage.mkdir(mode=0o700,exist_ok=False)
for name,pin in pins.items():
 path=upload/name;assert path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==pin
 shutil.copyfile(path,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-2500:]
spec=importlib.util.spec_from_file_location('client_guard',Path('/opt/nightcap/releases/advanced-loot-client-2026110605-v1/publish.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def guard():
 assert p.services()=={publication['services_after']!r},'Service drift'
 assert p.sha((p.PUBLIC/'channel.json').read_bytes())=={publication['channel_sha256']!r},'Client channel drift'
with (base/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=base/'data/public/wiki/current'
 assert pointer.is_symlink() and pointer.readlink()==Path('releases')/{previous!r}
 assert hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()=={baseline['config_sha256']!r}
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),
  str(stage/{manifest_path.name!r}),{RELEASE!r},{previous!r},{baseline['config_sha256']!r}],timeout=200))
 guard()
result['linux_tests']=tests.stderr.strip().splitlines()[-1]
print(json.dumps(result))
''')
    assert report['result'] == 'PASS' and report['files'] == 510
    report.update(changed_existing=changed, preserved_files=507,
                  package_sha256=pins[archive.name],
                  scope='Loot guide/history/search only; all catalogs, other guides and assets retained')
    (HERE / 'wiki-publication.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
