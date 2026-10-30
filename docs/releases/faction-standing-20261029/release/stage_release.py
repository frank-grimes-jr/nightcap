"""Upload the exact approved payload; keep runtime inventory/manifest private on-host."""
from pathlib import Path
import hashlib,io,json,subprocess,tarfile,os
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',os.environ['NIGHTCAP_DEPLOY_SSH_TARGET']]
STAGE='/opt/nightcap/releases/faction-standing-20261030-v1'
UPLOAD='/home/ubuntu/faction-standing-20261030-v1.tar.gz'
def main():
 identity=json.loads((HERE/'native-identity.json').read_text())
 payload={'bin/zone':HERE/'private/payload/zone','rollout.py':HERE/'rollout.py','test_rollout.py':HERE/'test_rollout.py'}
 pins={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in payload.items()}
 assert pins['bin/zone']==identity['sha256']
 archive=HERE/'private/faction-standing-20261030-v1.tar.gz'
 with tarfile.open(archive,'x:gz') as tar:
  for n,p in payload.items():
   data=p.read_bytes();entry=tarfile.TarInfo(n);entry.size=len(data);entry.mode=0o755 if n=='bin/zone' else 0o600
   tar.addfile(entry,io.BytesIO(data))
 archive_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
 code=f'''from pathlib import Path
import fcntl,hashlib,json,os,subprocess,tarfile,shutil
root=Path('/opt/nightcap/deploy/production');stage=Path({STAGE!r});upload=Path({UPLOAD!r});pins={pins!r}
os.umask(0o077)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (stage/'manifest.json').exists(),'Inspect prior stage before reuse'
 assert shutil.disk_usage(root).free>900*1024**2,'Insufficient staging/backup reserve'
 assert hashlib.sha256(upload.read_bytes()).hexdigest()=={archive_sha!r}
 with tarfile.open(upload,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==len(pins) and {{m.name for m in members}}==set(pins)
  for member in members:
   assert member.isfile() and not member.issym() and not member.islnk()
   p=stage/member.name;assert p.resolve().is_relative_to(stage)
   p.parent.mkdir(exist_ok=True)
   data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==pins[member.name]
   with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
   p.chmod(0o755 if member.name=='bin/zone' else 0o600)
 baseline=json.loads((stage/'baseline.json').read_text())
 m={{**baseline,'files':{{n:pins[n] for n in ['bin/zone','rollout.py']}},'zone_sha256':pins['bin/zone'],'source_revision':'3c3d815ed09d3f142af31e63645672e28e204b4e','owner_gameplay_accepted':False}}
 with (stage/'manifest.json').open('x') as f:json.dump(m,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno())
 tests=subprocess.run(['python3','-B','-m','unittest','-v','test_rollout'],cwd=stage,capture_output=True,text=True)
 (stage/'operator-tests.log').write_text(tests.stdout+tests.stderr)
 assert tests.returncode==0,'Operator tests failed; inspect host log'
 print(json.dumps({{'status':'staged and27Linux tests passed','zone_sha256':pins['bin/zone'],'archive_sha256':{archive_sha!r},'free_bytes':shutil.disk_usage(root).free,'services_changed':False,'metadata_retained_on_host':True}}))
'''
 # Exclusive remote destination check; never replace another upload.
 subprocess.run(SSH+['test ! -e '+UPLOAD],check=True)
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(archive),SSH[-1]+':'+UPLOAD],check=True,timeout=240)
 result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=240)
 (HERE/'private/staging.log').write_text(result.stdout+result.stderr,encoding='utf-8')
 if result.returncode:raise RuntimeError(result.stderr[-2500:])
 report=json.loads(result.stdout);(HERE/'staged.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
