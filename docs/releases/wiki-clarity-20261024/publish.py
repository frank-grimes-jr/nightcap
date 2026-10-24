"""Publish the scoped editorial wiki release with rollback and preservation guards."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=Path('E:/EQ_Local_Dev/artifacts/wiki-clarity-20261024')
RELEASE='20261024-wiki-clarity-v1'
PREVIOUS='20261024-hole-keyless-v1'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']


def remote(code):
    r=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=240)
    if r.returncode:raise RuntimeError(r.stderr[-3500:])
    return json.loads(r.stdout)


def main():
    assert not (HERE/'wiki-publication.json').exists(),'Inspect existing publication receipt before any replay'
    before=remote('''from pathlib import Path
import json,hashlib
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert before['release']==PREVIOUS,'Concurrent publication: reconcile current content before proceeding'
    baseline=json.loads(Path('E:/EQ_Local_Dev/artifacts/hole-keyless-wiki-20261024-matched.tar.json').read_text())
    assert baseline==before['manifest'],'Starting release differs from its reviewed published manifest'
    files=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    files += [ROOT/'wiki'/name for name in ['update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf']]
    manifest=json.loads(files[1].read_text())
    assert len(manifest)==483 and set(manifest)==set(baseline)
    changed={n for n,h in manifest.items() if baseline[n]!=h}
    allowed={n for n in manifest if n.endswith('.html')}|{'assets/wiki.css','assets/search.js','search-index.json'}
    assert changed<=allowed,changed-allowed
    (HERE/'wiki-before.json').write_text(json.dumps(before,indent=2)+'\n')
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-clarity-20261024-v1'
    stage='/opt/nightcap/releases/wiki-clarity-20261024-v1'
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=120)
    report=remote(f'''from pathlib import Path
import json,hashlib,subprocess,shutil
upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
for name,digest in pins.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=60)
assert tests.returncode==0,tests.stderr
result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{files[0].name!r}),str(stage/{files[1].name!r}),{RELEASE!r},{PREVIOUS!r},{before['config_sha256']!r}],timeout=180))
result['linux_tests']=tests.stderr;print(json.dumps(result))
''')
    assert report['result']=='PASS' and report['files']==483
    report['changed_files']=sorted(changed)
    report['baseline_source']='66c7b843'
    report['package_sha256']=pins[files[0].name]
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':report['result'],'release':RELEASE,'files':483,'changed':len(changed)}))


if __name__=='__main__':main()
