"""Publish SSF wiki guidance over the exact live release (adapted from keyless doors).

Usage: python publish_wiki.py <wiki dir built from hate-density b6204eef + wiki_edit.py> <package dir>
The package changes only the four allowed files; every other public file must
match the live manifest. Uses wiki/update.py (atomic pointer, rehearsed rollback).
"""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
RELEASE='20261101-ssf-v1'
PREVIOUS='20261030-hate-boss-placement-v1'
CONFIG='46355a5e09bc63bc0a05713c02a315966378ef2ecbc5856bbab2140093a619c6'
ALLOWED={'features.html','multiclass.html','recent-changes.html','search-index.json'}

def remote(code):
    r=subprocess.run(SSH+['sudo -n python3 -'],input=code.encode(),capture_output=True,timeout=600)
    if r.returncode:raise RuntimeError(r.stderr.decode()[-4000:])
    return json.loads(r.stdout)

def main(wiki,art):
    wiki,art=Path(wiki),Path(art)
    files=[art/(RELEASE+'.tar.gz'),art/(RELEASE+'.tar.json')]+[wiki/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    manifest=json.loads(files[1].read_text())
    guard='''from pathlib import Path
import json,hashlib,subprocess
base=Path('/opt/nightcap/deploy/production')
deployed=json.loads(Path('/opt/nightcap/releases/ssf-mode-20261101-v1/evidence/activation/deployed.json').read_text())
def target_guard():
    for name in ['game','gateway','db','web','tunnel']:
        cid=subprocess.check_output(['docker','compose','ps','-q',name],cwd=base,text=True).strip()
        row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
        assert row['State']['Running'] and not row['State']['OOMKilled'],name
        if name in ('game','db'):assert row['State']['Health']['Status']=='healthy',name
    game=json.loads(subprocess.check_output(['docker','inspect',subprocess.check_output(['docker','compose','ps','-q','game'],cwd=base,text=True).strip()],text=True))[0]
    assert game['Image']==deployed['runtime']['image_id'] and game['State']['StartedAt']==deployed['runtime']['started_at'],'Game changed'
target_guard()
'''
    before=remote(guard+'''pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert before['release']==PREVIOUS and before['config_sha256']==CONFIG,'Concurrent publication or config change'
    baseline=before['manifest'];assert len(manifest)==len(baseline)==499 and set(manifest)==set(baseline)
    changed={n for n,h in manifest.items() if baseline[n]!=h};assert changed==ALLOWED,changed
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-ssf-20261101-v1';stage='/opt/nightcap/releases/wiki-ssf-20261101-v1'
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=300)
    report=remote(f'''from pathlib import Path
import json,hashlib,subprocess,shutil,fcntl
upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
for name,digest in pins.items():
    p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
    shutil.copyfile(p,stage/name)
shutil.rmtree(upload)
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=120)
assert tests.returncode==0,tests.stderr[-3000:]
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    exec({guard!r})
    result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{files[0].name!r}),str(stage/{files[1].name!r}),{RELEASE!r},{PREVIOUS!r},{CONFIG!r}],timeout=300))
    target_guard()
result['linux_tests']=tests.stderr.strip().splitlines()[-1];print(json.dumps(result))
''')
    assert report['result']=='PASS' and report['files']==499,report
    report.update(changed_files=sorted(changed),preserved_files=499-len(changed),baseline_source=PREVIOUS,package_sha256=pins[files[0].name])
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('result','files','changed_files','linux_tests') if k in report}))

if __name__=='__main__':main(*sys.argv[1:3])
