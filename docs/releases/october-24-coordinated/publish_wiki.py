"""Publish the scoped editorial wiki release with rollback and preservation guards."""
import hashlib
import os
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=Path('E:/EQ_Local_Dev/artifacts/wiki-october24-coordinated')
RELEASE='20261024-coordinated-v1'
PREVIOUS='20261024-rogue-tomes-v1'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']


def remote(code):
    r=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=240)
    if r.returncode:raise RuntimeError(r.stderr[-3500:])
    return json.loads(r.stdout)


def main():
    runtime=HERE/'open-receipt.json'
    receipt=json.loads(runtime.read_text());assert receipt['result']=='PASS'
    assert not (HERE/'wiki-publication.json').exists(),'Inspect existing publication receipt before any replay'
    before=remote('''from pathlib import Path
import json,hashlib
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert before['release']==PREVIOUS,'Concurrent publication: reconcile current content before proceeding'
    baseline=json.loads((Path('E:/EQ_Local_Dev/artifacts/wiki-rogue-tomes-20261024')/(PREVIOUS+'.tar.json')).read_text())
    assert baseline==before['manifest'],'Starting release differs from its reviewed published manifest'
    files=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    files += [ROOT/'wiki'/name for name in ['update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf']]
    manifest=json.loads(files[1].read_text())
    assert len(manifest)==499 and set(baseline)<=set(manifest)
    added={'ashen-compact.html','zone-kael.html'}|{'item-'+str(i)+'.html' for i in [*range(960420,960426),*range(961020,961024),*range(961030,961033),990510]}
    assert set(manifest)-set(baseline)==added
    changed={n for n,h in manifest.items() if baseline.get(n)!=h}
    allowed=added|{'all-pages.html','camil-vigil.html','combat.html','commands.html','dungeon-modes.html','equipment.html','features.html','item-upgrades.html','launcher.html','recent-changes.html','search-index.json','sitemap.xml','travel.html','unreleased.html','waypoints.html','zone-highkeep.html','zone-hunt.html','zones.html'}
    assert changed<=allowed,changed-allowed
    (HERE/'wiki-before.json').write_text(json.dumps(before,indent=2)+'\n')
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-october24-coordinated-v1'
    stage='/opt/nightcap/releases/wiki-october24-coordinated-v1'
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
    assert report['result']=='PASS' and report['files']==499
    report['changed_files']=sorted(changed)
    report['baseline_source']='75d98fcf'
    report['package_sha256']=pins[files[0].name]
    (HERE/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':report['result'],'release':RELEASE,'files':499,'changed':len(changed)}))


if __name__=='__main__':main()
