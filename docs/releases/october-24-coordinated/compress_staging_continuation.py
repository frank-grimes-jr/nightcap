"""Losslessly compress explicitly enumerated obsolete, unmounted binary copies.

No images, active runtime files, database backups or evidence are removed.
Recovery: decompress the adjacent .oct24-recovery.gz into the original
path, verifying the receipt's original SHA-256 before using its old operator.
"""
import fcntl,gzip,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
ROOT=Path('/opt/nightcap/releases')
FILES=['throw-stone-20261009/native-bin/zone', 'october-17-2026/bin/zone', 'dungeon-journal-20261016/bin/zone', 'blessing-lifetime-server-20261004-r2/native-bin/world', 'blessing-lifetime-server-20261004-r3/native-bin/world', 'blessing-relogin-server-20261003/native-bin/world', 'advanced-loot-actions-server-20261002/native-bin/world', 'free-trade-20261004/native-bin/world', 'enchanter-animation-20260930/native-bin/world', 'tunnel-services-20260921/native-bin/world', 'bugfix-2026092005/native-bin/world']

def digest(stream):return hashlib.file_digest(stream,'sha256').hexdigest()

with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 containers=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-aq'],text=True).split()],text=True))
 mounts=[Path(m['Source']).resolve() for c in containers for m in c['Mounts']]
 receipt={'before_free':shutil.disk_usage(ROOT).free,'files':[],'active_files_changed':False}
 for name in FILES:
  if shutil.disk_usage(ROOT).free>=int(4.5*1024**3):break
  p=ROOT/name;assert p.resolve()==p and p.is_file() and not p.is_symlink()
  assert not any(p==m or p.is_relative_to(m) for m in mounts),str(p)
  stat=p.stat();assert stat.st_nlink==1,'Shared inode requires separate review'
  archive=p.with_name(p.name+'.oct24-recovery.gz')
  with p.open('rb') as source:before=digest(source)
  if not archive.exists():
   with p.open('rb') as source,archive.open('xb') as raw:
    os.fchmod(raw.fileno(),0o600)
    with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=6,mtime=0) as dest:shutil.copyfileobj(source,dest,1024**2)
    raw.flush();os.fsync(raw.fileno())
  with gzip.open(archive,'rb') as source:assert digest(source)==before
  with p.open('rb') as source:assert digest(source)==before
  current=p.stat()
  assert (current.st_ino,current.st_size,current.st_mtime_ns)==(stat.st_ino,stat.st_size,stat.st_mtime_ns)
  receipt['files'].append({'path':str(p),'sha256':before,'original_bytes':stat.st_size,'compressed_bytes':archive.stat().st_size,'mode':stat.st_mode,'uid':stat.st_uid,'gid':stat.st_gid,'archive':str(archive)})
  record=ROOT/'oct24-space-20261024-continuation.json'
  record.write_text(json.dumps(receipt,indent=2)+'\n');record.chmod(0o600)
  p.unlink()
 receipt['after_free']=shutil.disk_usage(ROOT).free
 record.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt))
