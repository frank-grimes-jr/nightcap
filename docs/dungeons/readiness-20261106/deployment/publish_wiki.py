"""Publish only the scoped Keeper guide/history delta after verified game activation."""
import hashlib
import json
from pathlib import Path
import subprocess
from probe import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ART=ROOT/'artifacts/dungeon-readiness'
WIKI=ART/'wiki-source/wiki'
RELEASE='20261106-dungeon-readiness-v1'
PREVIOUS='20261106-character-stats-shield-block-v1'


def remote(code,timeout=600):
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if result.returncode:raise RuntimeError(result.stderr[-3500:])
    return json.loads(result.stdout)


def main():
    deployed=json.loads((HERE/'deployed.json').read_text())
    assert deployed['gateway_open'] and deployed['status']=='deployed for live QA'
    baseline=json.loads((HERE/'wiki-baseline-manifest.json').read_text())
    archive=ART/(RELEASE+'.tar.gz');manifest_path=archive.with_suffix('.json')
    manifest=json.loads(manifest_path.read_text())
    assert manifest.keys()==baseline.keys() and len(manifest)==510
    changed=sorted(k for k in manifest if manifest[k]!=baseline[k])
    assert changed==['dungeon-modes.html','recent-changes.html','search-index.json']
    files=[archive,manifest_path]+[WIKI/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-dungeon-readiness-20261106-v1'
    stage='/opt/nightcap/releases/wiki-dungeon-readiness-20261106-v1'
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=300)
    config=json.loads((ROOT/'docs/releases/character-stats-shield-block-20261106/wiki-publication.json').read_text())['config_sha256']
    report=remote(f'''from pathlib import Path
import fcntl,hashlib,json,subprocess,shutil
base=Path('/opt/nightcap/deploy/production');upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins);stage.mkdir(mode=0o700,exist_ok=False)
for name,pin in pins.items():
 path=upload/name;assert path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==pin
 shutil.copyfile(path,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-2500:]
deployed=json.loads((Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1')/'evidence/activation/deployed.json').read_text())
assert deployed['gateway_open'] and deployed['zone_only'] and not deployed['client_update_required']
def guard():
 for name in ('game','gateway','db','web','tunnel'):
  cid=subprocess.check_output(['docker','compose','ps','-q',name],cwd=base,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled'],name
  if name in ('game','db'):assert row['State']['Health']['Status']=='healthy'
  if name=='game':assert row['Image']==deployed['runtime']['image_id'] and row['State']['StartedAt']==deployed['runtime']['started_at']
with (base/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=base/'data/public/wiki/current'
 assert pointer.is_symlink() and pointer.readlink()==Path('releases')/{PREVIOUS!r}
 assert hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()=={config!r}
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),str(stage/{manifest_path.name!r}),{RELEASE!r},{PREVIOUS!r},{config!r}],timeout=500))
 guard()
result['linux_tests']=tests.stderr.strip().splitlines()[-1];print(json.dumps(result))
''')
    assert report['result']=='PASS' and report['files']==510
    report.update(changed_existing=changed,preserved_files=507,package_sha256=pins[archive.name],
                  scope='Dungeon entry guidance and dated repair note only; existing rewards/catalog/current client guidance retained')
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
