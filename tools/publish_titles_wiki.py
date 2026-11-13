"""Publish the owner-authorized title preview; never change the game runtime."""
import hashlib
import json
from pathlib import Path
import subprocess
from capture_lantern_content import SSH

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'docs/titles/wiki-release'
ART = ROOT/'artifacts/titles-wiki-20261112'
RELEASE = '20261112-earned-titles-v1'
PREVIOUS = '20261112-dot-ticks-v2'

REMOTE = r'''
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,tarfile
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');upload=Path(UPLOAD)
stage=Path('/opt/nightcap/releases/wiki-earned-titles-20261112-v1')
assert {p.name for p in upload.iterdir()}==set(PINS)
assert shutil.disk_usage(root).free>128*1024**2
stage.mkdir(mode=0o700)
for name,pin in PINS.items():
 p=upload/name
 assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
(stage/'linux-tests.log').write_text(tests.stdout+'\n'+tests.stderr)
assert tests.returncode==0,tests.stderr[-2000:]
s=importlib.util.spec_from_file_location('deploy_guard',stage/'deploy.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def guard():
 assert [list(x) for x in m.services()]==BASELINE['services'],'service identities changed'
 assert m.sha((root/'nginx.conf').read_bytes())==BASELINE['config_sha256']
 assert (root/'nginx.conf').stat().st_ino==BASELINE['config_inode']
 assert m.sha((root/'data/public/channel.json').read_bytes())==BASELINE['channel_sha256']
with (root/'.deployment.lock').open('r+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 guard()
 pointer=root/'data/public/wiki/current'
 assert pointer.is_symlink() and str(pointer.readlink())=='releases/'+PREVIOUS
 current=json.loads((root/'website-history'/PREVIOUS/'manifest.json').read_text())
 assert current==BASELINE['manifest']
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/ARCHIVE),str(stage/MANIFEST),RELEASE,PREVIOUS,BASELINE['config_sha256']],timeout=300))
 guard()
 assert str(pointer.readlink())=='releases/'+RELEASE
result.update(linux_tests=tests.stderr.strip().splitlines()[-1],changed_existing=CANDIDATE['changed_existing'],
 added=CANDIDATE['added'],preserved_files=CANDIDATE['preserved_files'],public_source_reproduced=True,
 channel_config_inode_preserved=True,title_runtime='not activated',title_player_QA='OPEN',availability='Not released preview')
(stage/'publication.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
'''


def main():
    candidate=json.loads((HERE/'candidate.json').read_text(encoding='utf-8'))
    baseline=json.loads((HERE/'baseline.json').read_text(encoding='utf-8'))
    assert candidate['public_source_reproduced'] and candidate['files']==614
    assert candidate['added']==['titles.html'] and not candidate['removed']
    assert baseline['release']==PREVIOUS and len(baseline['manifest'])==613
    wiki=ART/'wiki-source-v2/wiki'
    title=json.loads((wiki/'articles/titles.json').read_text(encoding='utf-8'))
    assert title['status']=='Not released'
    archive=ART/(RELEASE+'.tar.gz')
    paths=[archive,archive.with_suffix('.json')]+[wiki/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    upload='/home/ubuntu/wiki-earned-titles-20261112-v1'
    ssh=SSH[:-1]
    subprocess.run(ssh+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,paths),ssh[-1]+':'+upload+'/'],check=True,timeout=300)
    values=dict(PINS=pins,UPLOAD=upload,BASELINE=baseline,CANDIDATE=candidate,RELEASE=RELEASE,
                PREVIOUS=PREVIOUS,ARCHIVE=archive.name,MANIFEST=archive.with_suffix('.json').name)
    code='\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+REMOTE
    result=subprocess.run(SSH,input=code,text=True,encoding='utf-8',capture_output=True,timeout=600)
    if result.returncode:
        (ART/'publication-error.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        raise RuntimeError('Publication stopped; inspect the retained stage/receipt before any retry: '+str(ART/'publication-error.txt'))
    report=json.loads(result.stdout)
    assert report['result']=='PASS' and report['release']==RELEASE
    (HERE/'publication.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
