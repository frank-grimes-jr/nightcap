"""Publish only the augment delta over the verified current public baseline."""
import hashlib
import json
from pathlib import Path
import subprocess
from stage import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WIKI=ROOT/'artifacts/character-stats-shield-block/wiki-source/wiki'
ART=ROOT/'artifacts/character-stats-shield-block'
RELEASE='20261106-character-stats-shield-block-v1'


def remote(code,timeout=600):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stderr[-3500:])
    return json.loads(p.stdout)


def main():
    client=json.loads((HERE/'client-public-verification.json').read_text())
    assert client['release']==2026110604 and client['hosted'] and client['changed_assets']==1
    baseline=json.loads((HERE/'wiki-baseline.json').read_text())
    archive=ART/(RELEASE+'.tar.gz');manifest_path=archive.with_suffix('.json')
    subprocess.run(['python',str(WIKI/'build.py'),'--package',str(archive)],check=True)
    manifest=json.loads(manifest_path.read_text())
    added=set(manifest)-set(baseline['manifest']);removed=set(baseline['manifest'])-set(manifest)
    expected=set()
    assert added==expected and not removed,(added,removed)
    allowed={'augment-audit.html','equipment.html','commands.html','features.html','recent-changes.html','all-pages.html','search-index.json','sitemap.xml'}
    changed={n for n in set(manifest)&set(baseline['manifest']) if manifest[n]!=baseline['manifest'][n]}
    assert changed<=allowed,'Unreviewed public changes: '+str(sorted(changed-allowed))
    files=[archive,manifest_path]+[WIKI/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-character-stats-shield-block-20261106-v1';stage='/opt/nightcap/releases/wiki-character-stats-shield-block-20261106-v1'
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=300)
    guard='''from pathlib import Path
import json,hashlib,subprocess
base=Path('/opt/nightcap/deploy/production');game_release=Path('/opt/nightcap/releases/character-stats-window-20261106-v1/evidence/activation/deployed.json')
deployed=json.loads(game_release.read_text());assert deployed['gateway_open'] and deployed['client_update_required']
def target_guard():
 for name in ('game','gateway','db','web','tunnel'):
  cid=subprocess.check_output(['docker','compose','ps','-q',name],cwd=base,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled'],name
  if name in ('game','db'):assert row['State']['Health']['Status']=='healthy'
  if name=='game':assert row['Image']==deployed['runtime']['image_id'] and row['State']['StartedAt']==deployed['runtime']['started_at']
target_guard()
'''
    report=remote(f'''from pathlib import Path
import json,hashlib,subprocess,shutil,fcntl
upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins);stage.mkdir(mode=0o700,parents=True,exist_ok=False)
for name,pin in pins.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-2000:]
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);exec({guard!r})
 pointer=base/'data/public/wiki/current';assert pointer.is_symlink() and pointer.readlink().name=={baseline['release']!r}
 assert hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()=={baseline['config_sha256']!r}
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),str(stage/{manifest_path.name!r}),{RELEASE!r},{baseline['release']!r},{baseline['config_sha256']!r}],timeout=500))
 target_guard()
result['linux_tests']=tests.stderr.strip().splitlines()[-1];print(json.dumps(result))
''')
    assert report['result']=='PASS' and report['files']==len(manifest)
    report.update(changed_existing=sorted(changed),added_files=sorted(added),preserved_files=len(baseline['manifest'])-len(changed),
                  package_sha256=pins[archive.name],scope='five guide updates; no item/catalog/asset change')
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('result','release','files','preserved_files','linux_tests')}))


if __name__=='__main__':main()
