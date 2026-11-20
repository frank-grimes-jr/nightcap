"""Publish the three reviewed wiki outputs after the signed client verifies."""
import argparse
import hashlib
import json
import subprocess
import sys
from support import ART,HERE,ROOT,SSH,remote,save,sha

RELEASE='20261120-inventory-no-scrollbars-v1'
PREVIOUS='20261114-titles-automatic-suffix-v1'
SITE=ART/'wiki-source/wiki'


def prepare():
    baseline=json.loads((HERE/'baseline.json').read_bytes())
    assert baseline['wiki_release']==PREVIOUS
    archive=ART/(RELEASE+'.tar.gz')
    subprocess.run([sys.executable,'-B',str(SITE/'build.py'),'--package',str(archive)],check=True)
    manifest=json.loads(archive.with_suffix('.json').read_bytes())
    before=baseline['wiki_manifest']
    assert set(manifest)==set(before)
    changed=sorted(name for name in before if manifest[name]!=before[name])
    assert changed==['equipment.html','recent-changes.html','search-index.json']
    save(HERE/'wiki-candidate.json',dict(release=RELEASE,previous=PREVIOUS,files=len(manifest),
        changed=changed,preserved=len(manifest)-len(changed),package_sha256=sha(archive),
        manifest_sha256=sha(archive.with_suffix('.json'))))


def publish():
    client=json.loads((HERE/'client-public-verification.json').read_bytes())
    assert client['release']==2026112001 and client['hosted'] and client['changed_assets']==1
    base=json.loads((HERE/'baseline.json').read_bytes())
    candidate=json.loads((HERE/'wiki-candidate.json').read_bytes())
    archive=ART/(RELEASE+'.tar.gz');manifest=archive.with_suffix('.json')
    assert sha(archive)==candidate['package_sha256'] and sha(manifest)==candidate['manifest_sha256']
    paths=[archive,manifest]+[SITE/name for name in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:sha(p) for p in paths}
    upload='/home/ubuntu/wiki-'+RELEASE
    subprocess.run(SSH+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,paths),SSH[-1]+':'+upload+'/'],check=True,timeout=180)
    publisher_pin=sha(HERE/'publish.py')
    result=remote(f"""from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');public=root/'data/public'
source=Path({upload!r});stage=Path('/opt/nightcap/releases/wiki-{RELEASE}');pins={pins!r}
assert {{p.name for p in source.iterdir()}}==set(pins)
assert shutil.disk_usage(root).free>2*sum((source/name).stat().st_size for name in pins)+350*1024**2
stage.mkdir(mode=0o700,exist_ok=False)
for name,pin in pins.items():
 p=source/name;assert not p.is_symlink() and p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 with (stage/name).open('xb') as out:out.write(p.read_bytes());out.flush();os.fsync(out.fileno())
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-2000:]
publisher=Path('/opt/nightcap/releases/inventory-no-scrollbars-20261120-v1/publish.py')
assert hashlib.sha256(publisher.read_bytes()).hexdigest()=={publisher_pin!r}
spec=importlib.util.spec_from_file_location('client_publisher',publisher)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def guard():
 assert p.services()=={base['services']!r},'Service identity drift'
 assert hashlib.sha256((public/'channel.json').read_bytes()).hexdigest()=={client['channel_sha256']!r},'Client channel drift'
 assert hashlib.sha256((root/'nginx.conf').read_bytes()).hexdigest()=={base['config_sha256']!r},'Config drift'
 assert (root/'nginx.conf').stat().st_ino=={base['config_inode']!r},'Config inode drift'
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 assert (public/'wiki/current').readlink()==Path('releases/{PREVIOUS}')
 assert json.loads((root/'website-history/{PREVIOUS}/manifest.json').read_bytes())=={base['wiki_manifest']!r}
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),
       str(stage/{manifest.name!r}),{RELEASE!r},{PREVIOUS!r},{base['config_sha256']!r}],timeout=600))
 guard()
 assert result['result']=='PASS' and result['rollback_rehearsed'] and result['files']=={candidate['files']}
 assert (public/'wiki/current').readlink()==Path('releases/{RELEASE}')
 result.update(config_inode_preserved=True,client_release=2026112001,client_channel_sha256={client['channel_sha256']!r},
     linux_publisher_tests=tests.stderr.strip(),changed={candidate['changed']!r},preserved={candidate['preserved']})
 p.replace((json.dumps(result,indent=2)+chr(10)).encode(),stage/'published.json')
print(json.dumps(result))
""",timeout=900)
    save(HERE/'wiki-publication.json',result)
    print(json.dumps({k:result[k] for k in ('result','release','files','preserved')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','publish'))
    action=parser.parse_args().action
    prepare() if action=='prepare' else publish()
