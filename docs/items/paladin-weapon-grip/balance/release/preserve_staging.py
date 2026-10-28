"""Losslessly compress two authenticated unmounted historical executable copies."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,shutil,subprocess
ROOT=Path('/opt/nightcap/deploy/production')
PINS={
 '/opt/nightcap/releases/rogue-tomes-20261024/bin/zone':'75e0c7c3a8dbc42b87e09cd60ba350ce0c37b2a2c31771934665aa88fc3061df',
 '/opt/nightcap/releases/october-24-coordinated-20261024/bin/zone':'a139726f72960c8966df235088b52d77aca6ac3b6e0d01b50dfae4cba1f1e35b'}
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
  source=Path(name);archive=source.with_name('zone.paladin-release-preserved-20261028.gz');receipt=source.parent/'paladin-release-preservation-20261028.json'
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
  assert sha(source)==digest
  report={'source':name,'archive':str(archive),'source_sha256':digest,'archive_sha256':sha(archive),'source_bytes':stat.st_size,'archive_bytes':archive.stat().st_size,'mode':stat.st_mode & 0o777,'uid':stat.st_uid,'gid':stat.st_gid,'restoration':'Decompress to exclusive temp; verify source_sha256; restore recorded mode/owner; rename to original before using old staging operator.','backups_images_player_data_unchanged':True}
  with receipt.open('x') as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
  sync(source.parent);source.unlink();sync(source.parent);reports.append(report)
 after=snapshot()
 # Health probe timestamps can advance while all service identities remain stable.
 for old,new in zip(before,after):
  assert {k:v for k,v in old.items() if k!='state'}=={k:v for k,v in new.items() if k!='state'}
  for key in ['Running','StartedAt','OOMKilled','ExitCode']:assert old['state'][key]==new['state'][key]
 assert images==subprocess.check_output(['docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}'],text=True)
 print(json.dumps({'preserved':reports,'disk_free':shutil.disk_usage(ROOT).free,'services_images_unchanged':True}))
