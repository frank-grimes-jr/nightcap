"""Upload the exact payload and write its manifest on-host. Changes no service."""
from pathlib import Path
import hashlib,io,json,subprocess,sys,tarfile
HERE=Path(__file__).resolve().parent
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/zone-hunt-rates-20261101-v1'
UPLOAD='/home/ubuntu/zone-hunt-rates-20261101-v1.tar.gz'

def main(zone,archive,revision):
    payload={'bin/zone':Path(zone).read_bytes(),'rollout.py':(HERE/'rollout.py').read_bytes(),
             'rates.sql':(HERE/'rates.sql').read_bytes()}
    pins={n:hashlib.sha256(d).hexdigest() for n,d in payload.items()}
    with tarfile.open(archive,'x:gz') as tar:
        for n,d in payload.items():
            entry=tarfile.TarInfo(n);entry.size=len(d);entry.mode=0o755 if n=='bin/zone' else 0o600
            tar.addfile(entry,io.BytesIO(d))
    archive_sha=hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    code=f'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,tarfile
root=Path('/opt/nightcap/deploy/production');stage=Path({STAGE!r});upload=Path({UPLOAD!r});pins={pins!r}
prior=Path('/opt/nightcap/releases/ssf-mode-20261101-v1')
os.umask(0o077)
with (root/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not stage.exists(),'Inspect prior stage before reuse'
    assert hashlib.sha256(upload.read_bytes()).hexdigest()=={archive_sha!r}
    pm=json.loads((prior/'manifest.json').read_text())
    deployed=json.loads((prior/'evidence/activation/deployed.json').read_text())
    stage.mkdir(mode=0o700)
    with tarfile.open(upload,'r:gz') as tar:
        members=tar.getmembers();assert {{m.name for m in members}}==set(pins) and len(members)==len(pins)
        for member in members:
            assert member.isfile();p=stage/member.name;assert p.resolve().is_relative_to(stage)
            p.parent.mkdir(parents=True,exist_ok=True)
            data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==pins[member.name]
            with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            p.chmod(0o755 if member.name=='bin/zone' else 0o600)
    m={{'release':'zone-hunt-rates-20261101-v1','source_revision':{revision!r},
        'base_image_id':deployed['runtime']['image_id'],
        'base_hashes':{{**pm['base_hashes'],'bin/zone':pm['zone_sha256']}},
        'zone_sha256':pins['bin/zone'],'prior_rollout_sha256':hashlib.sha256((prior/'rollout.py').read_bytes()).hexdigest(),
        'files':pins,
        'owner_deploy_authorized':'2026-11-01 chat: Merge to main and OVH','owner_gameplay_accepted':False}}
    with (stage/'manifest.json').open('x') as f:json.dump(m,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno())
    upload.unlink()
    print(json.dumps({{'staged':str(stage),'base_image_id':m['base_image_id'],'zone_sha256':pins['bin/zone'],'free_bytes':shutil.disk_usage(root).free}}))
'''
    subprocess.run(SSH+['test ! -e '+UPLOAD],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(archive),SSH[-1]+':'+UPLOAD],check=True,timeout=600)
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=240)
    if result.returncode:raise RuntimeError(result.stderr[-2500:])
    print(result.stdout)

if __name__=='__main__':main(*sys.argv[1:4])
