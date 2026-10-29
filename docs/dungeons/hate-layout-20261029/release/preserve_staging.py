"""Losslessly compress one authenticated unmounted historical executable copies."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,shutil,subprocess
ROOT=Path('/opt/nightcap/deploy/production')
PINS={'/opt/nightcap/releases/hate-keeper-commonlands-20261022/bin/zone':'1d4ef362639722b7eaddc49ae2883e2c5abcefc7c5d958f622cfb048308b995f'}

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def snapshot():
 rows=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-aq'],text=True).split()],text=True))
 return [{'id':r['Id'],'image':r['Image'],'restarts':r['RestartCount'],'state':r['State'],'mounts':r['Mounts']} for r in rows]
def sync(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
with (ROOT/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=snapshot();images=subprocess.check_output(['docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}'],text=True)
 mounts=[Path(m['Source']) for r in before for m in r['mounts']]
 reports=[]
 for name,digest in PINS.items():
  source=Path(name);archive=source.with_name('zone.hate-release-preserved-20261029.gz');receipt=source.parent/'hate-release-preservation-20261029.json'
  assert source.resolve()==source and source.is_file() and source.stat().st_nlink==1
  assert not archive.exists() and not archive.is_symlink() and not receipt.exists()
  assert all(not source.is_relative_to(m) for m in mounts)
  for exe in Path('/proc').glob('[0-9]*/exe'):
   try:assert exe.resolve()!=source
   except FileNotFoundError:pass
  assert sha(source)==digest
  assert json.loads((source.parent.parent/'manifest.json').read_text())['files']['bin/zone']==digest
  assert shutil.disk_usage(source).free>512*1024**2
  stat=source.stat()
  with source.open('rb') as src,archive.open('xb') as dst:
   class Bounded:
    def write(self,data):
     assert dst.tell()+len(data)<120*1024**2,'Archive exceeds budget; original retained'
     return dst.write(data)
    def flush(self):dst.flush()
   with gzip.GzipFile(fileobj=Bounded(),mode='wb',compresslevel=1,mtime=0) as z:shutil.copyfileobj(src,z)
   dst.flush();os.fsync(dst.fileno())
  with gzip.open(archive,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
  assert sha(source)==digest and source.stat()==stat
  report={'source':name,'archive':str(archive),'source_sha256':digest,'archive_sha256':sha(archive),'source_bytes':stat.st_size,'archive_bytes':archive.stat().st_size,'mode':stat.st_mode & 0o777,'uid':stat.st_uid,'gid':stat.st_gid,'restoration':'Decompress to exclusive temp; verify source_sha256; restore recorded mode/owner; rename to original before using old staging operator.','backups_images_player_data_unchanged':True}
  with receipt.open('x') as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
  sync(source.parent);source.unlink();sync(source.parent);reports.append(report)
 after=snapshot()
 # Health probe timestamps can advance while all service identities remain stable.
 assert {v['id'] for v in before}=={v['id'] for v in after}
 after_by_id={v['id']:v for v in after}
 for old in before:
  new=after_by_id[old['id']]
  assert {k:v for k,v in old.items() if k!='state'}=={k:v for k,v in new.items() if k!='state'}
  for key in ['Running','StartedAt','OOMKilled','ExitCode']:assert old['state'][key]==new['state'][key]
 assert images==subprocess.check_output(['docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}'],text=True)
 print(json.dumps({'preserved':reports,'disk_free':shutil.disk_usage(ROOT).free,'services_images_unchanged':True}))
