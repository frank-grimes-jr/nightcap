from pathlib import Path
import json,subprocess,sys,hashlib
A=Path(__file__).resolve().parent;W=Path('E:/EQ_Local_Dev/_worktrees/aa-availability');S=A/'wiki'
sys.path.insert(0,str(W/'docs/releases/classic-raid-augments-20261112'))
from probe import remote,SSH
release='20261120-aa-availability-v1';previous='20261120-fast-healing-v1'
archive=A/(release+'.tar.gz');manifest=archive.with_suffix('.json')
paths=[archive,manifest]+[S/n for n in ('update.py','deploy.py','test_update.py','test_deploy.py','nginx.conf')]
pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
upload='/home/ubuntu/wiki-'+release
subprocess.run(SSH[:-1]+['mkdir -m 700 '+upload],check=True,timeout=30)
subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],*map(str,paths),SSH[-2]+':'+upload+'/'],check=True,timeout=180)
code=f"""from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,importlib.util
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');public=root/'data/public'
source=Path({upload!r});stage=Path('/opt/nightcap/releases/wiki-{release}');pins={pins!r}
stage.mkdir(mode=0o700,exist_ok=False)
for name,pin in pins.items():
 p=source/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 with (stage/name).open('xb') as f:f.write(p.read_bytes());f.flush();os.fsync(f.fileno())
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-3000:]
p=Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py')
s=importlib.util.spec_from_file_location('stock',p);op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 services={{k:op.r.compact(k) for k in ('game','gateway','db','web','tunnel')}}
 channel=sha(public/'channel.json');config=sha(root/'nginx.conf');inode=(root/'nginx.conf').stat().st_ino
 receipt=json.loads(Path('/opt/nightcap/releases/aa-availability-20261120-v1/evidence/activation/deployed.json').read_bytes())
 assert receipt['gateway_open'] and services['game']['image_id']==receipt['image']
 assert (public/'wiki/current').readlink()==Path('releases/{previous}')
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{archive.name!r}),str(stage/{manifest.name!r}),{release!r},{previous!r},config],timeout=600))
 assert result['result']=='PASS' and result['rollback_rehearsed']
 assert services=={{k:op.r.compact(k) for k in services}}
 assert channel==sha(public/'channel.json') and config==sha(root/'nginx.conf') and inode==(root/'nginx.conf').stat().st_ino
 result.update(linux_tests=tests.stderr.strip(),services_preserved=True,channel_preserved=True)
 (stage/'published.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
"""
result=json.loads(remote(code,timeout=900));(A/'wiki-publication.json').write_text(json.dumps(result,indent=2));print(result)

