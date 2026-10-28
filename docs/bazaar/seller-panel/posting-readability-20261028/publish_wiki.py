"""Publish the scoped editorial wiki release with rollback and preservation guards."""
import hashlib
import os
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ART=ROOT/'docs/bazaar/private/posting-readability-20261028/wiki'
RELEASE='20261028-bazaar-post-readability-v1'
PREVIOUS='20261028-bazaar-startup-hotfix-v1'
from ship_publish import ship
SSH=ship.SSH


def remote(code):
    r=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=240)
    if r.returncode:raise RuntimeError(r.stderr[-3500:])
    return json.loads(r.stdout)


def main():
    client=json.loads((HERE/'published.json').read_text());assert client['release']==2026102803
    assert not (HERE/'wiki-publication.json').exists(),'Inspect existing publication receipt before any replay'
    target_guard=f'''from pathlib import Path
import json,hashlib,subprocess
base=Path('/opt/nightcap/deploy/production')
def target_guard():
 assert hashlib.sha256((base/'data/public/channel.json').read_bytes()).hexdigest()=={client['channel_sha256']!r},'Signed channel changed'
 for name in ['game','gateway','db','web','tunnel']:
  cid=subprocess.check_output(['docker','compose','ps','-aq',name],cwd=base,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled'],name
  if name in ['game','db']:assert row['State']['Health']['Status']=='healthy',name
  expected={client['services_after']!r}[name]
  assert all(row[k]==expected[k] for k in ['Id','Image','RestartCount']),'Service identity changed'
  assert all(row['State'][k]==expected['state'][k] for k in ['Running','StartedAt','OOMKilled']),'Service state changed'
target_guard()
'''
    before=remote(target_guard+'''from pathlib import Path
import json,hashlib
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert before['release']==PREVIOUS,'Concurrent publication: reconcile current content before proceeding'
    baseline=json.loads((HERE/'wiki-baseline.json').read_text())
    assert baseline==before['manifest'],'Starting release differs from its reviewed published manifest'
    files=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    files += [ROOT/'wiki'/name for name in ['update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf']]
    manifest=json.loads(files[1].read_text())
    assert len(manifest)==499 and set(baseline)<=set(manifest)
    assert set(manifest)==set(baseline)
    changed={n for n,h in manifest.items() if baseline.get(n)!=h}
    allowed={'launcher.html','tunnel.html','recent-changes.html','search-index.json'}
    assert changed<=allowed,changed-allowed
    (HERE/'wiki-before.json').write_text(json.dumps(before,indent=2)+'\n')
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-bazaar-post-readability-20261028-v1'
    stage='/opt/nightcap/releases/wiki-bazaar-post-readability-20261028-v1'
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=120)
    report=remote(f'''from pathlib import Path
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
    assert report['result']=='PASS' and report['files']==499
    report['changed_files']=sorted(changed)
    report['baseline_source']='20261028-bazaar-startup-hotfix-v1 verified499filemanifest';report['scope']='Preserve495files; publish launcher, tunnel and change-log posting/readability instructions plus search index'
    report['package_sha256']=pins[files[0].name]
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':report['result'],'release':RELEASE,'files':499,'changed':len(changed)}))


if __name__=='__main__':main()
