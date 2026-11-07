"""Publish the scoped wiki delta after the paired gameplay/client release."""
import hashlib,json,subprocess
from pathlib import Path
from ship_last_lantern import ROOT,HERE,ART,SSH,STAGE,remote

RELEASE='20261107-last-lantern-v2'
PREVIOUS='20261107-last-lantern-v1'

def main():
    deployed=json.loads((HERE/'production-verification.json').read_text());assert deployed['gateway_open']
    client=json.loads((HERE/'client-public-verification.json').read_text());assert client['hosted'] and client['release']==2026110701
    candidate=json.loads((HERE/'wiki-candidate.json').read_text());assert candidate['files']==613 and candidate['baseline_files']==613
    archive=ART/(RELEASE+'.tar.gz');manifest=archive.with_suffix('.json')
    wiki=ART/'wiki-source/wiki'
    files=[archive,manifest]+[wiki/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/wiki-last-lantern-20261107-v2';stage='/opt/nightcap/releases/wiki-last-lantern-20261107-v2'
    ssh=SSH[:-1]
    subprocess.run(ssh+['mkdir -m 700 '+upload],check=True,timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,files),ssh[-1]+':'+upload+'/'],check=True,timeout=300)
    result=remote(f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
base=Path('/opt/nightcap/deploy/production');upload=Path({upload!r});stage=Path({stage!r});pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
os.umask(0o077);stage.mkdir(mode=0o700,exist_ok=False)
for n,pin in pins.items():
 p=upload/n;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 shutil.copyfile(p,stage/n)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,text=True,capture_output=True,timeout=180)
assert tests.returncode==0,tests.stderr[-2500:]
spec=importlib.util.spec_from_file_location('campaign',Path({STAGE!r})/'rollout.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.initialize()
proof=m.read(Path({STAGE!r})/'evidence/activation/deployed.json');assert proof['gateway_open']
before={{s:m.r.compact(s) for s in ('game','gateway','db','web','tunnel')}}
def guard():
 assert all(m.r.compact(s)==v for s,v in before.items()),'Service drift'
 assert m.sha(base/'data/public/channel.json')=={client['channel_sha256']!r}
 m.r.running(proof['runtime']['image_id'],m.binaries());m.base.health()
with (base/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=base/'data/public/wiki/current';assert pointer.is_symlink() and pointer.readlink()==Path('releases')/{PREVIOUS!r}
 config=hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()
 assert config=='46355a5e09bc63bc0a05713c02a315966378ef2ecbc5856bbab2140093a619c6'
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),str(stage/{manifest.name!r}),{RELEASE!r},{PREVIOUS!r},config],timeout=240))
 guard()
result['linux_tests']=tests.stderr.strip().splitlines()[-1]
print(json.dumps(result))
''')
    assert result['result']=='PASS' and result['files']==613
    result.update(changed_existing=candidate['changed_existing'],preserved_files=candidate['preserved_files'],added_files=len(candidate['added_files']),package_sha256=pins[archive.name],scope='Last Lantern guide/reachable rewards/context; authenticated current public source; unrelated main previews remain unpublished')
    (HERE/'wiki-publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
