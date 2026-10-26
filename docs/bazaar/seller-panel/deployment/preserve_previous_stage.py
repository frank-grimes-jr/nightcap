"""Losslessly archive this task's unmounted previous Bazaar staging executable only."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,shutil,subprocess
ROOT=Path('/opt/nightcap/deploy/production')
SOURCE=Path('/opt/nightcap/releases/commonlands-bazaar-20261026/bin/zone')
DEST=SOURCE.with_name('zone.bazaar-grip-debug-preserved.gz')
RECEIPT=SOURCE.parent/'bazaar-grip-preservation.json'
EXPECTED='84b6b9ff5a5ce598e0e583d948c945b79c7742ee1a9364ddd1ed05148b6c5bc1'
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def sync(directory):
 fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
with (ROOT/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert SOURCE.resolve()==SOURCE and SOURCE.is_file() and SOURCE.stat().st_nlink==1
 assert not DEST.exists() and not DEST.is_symlink() and not RECEIPT.exists()
 ids=subprocess.check_output(['docker','ps','-aq'],text=True).split()
 rows=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True))
 mounts=[m['Source'] for r in rows for m in r.get('Mounts',[]) if m.get('Source')]
 assert all(not SOURCE.is_relative_to(Path(m)) for m in mounts),'Staging copy is mounted'
 for exe in Path('/proc').glob('[0-9]*/exe'):
  try:assert exe.resolve()!=SOURCE,'Running staging executable'
  except FileNotFoundError:pass
 assert sha(SOURCE)==EXPECTED
 before=shutil.disk_usage(SOURCE).free;size=SOURCE.stat().st_size
 assert before>672*1024**2+120*1024**2
 with SOURCE.open('rb') as src,DEST.open('xb') as dst:
  class Bounded:
   def write(self,data):
    assert dst.tell()+len(data)<=120*1024**2,'Compression exceeded reserved space; original retained'
    return dst.write(data)
   def flush(self):dst.flush()
  with gzip.GzipFile(fileobj=Bounded(),mode='wb',compresslevel=1,mtime=0) as compressed:shutil.copyfileobj(src,compressed)
  dst.flush();os.fsync(dst.fileno())
 with gzip.open(DEST,'rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==EXPECTED
 assert sha(SOURCE)==EXPECTED and shutil.disk_usage(SOURCE).free>=672*1024**2
 receipt={'source':str(SOURCE),'archive':str(DEST),'source_sha256':EXPECTED,'archive_sha256':sha(DEST),'size':size,'archive_size':DEST.stat().st_size,'restoration':'gunzip to exclusive temporary path, authenticate source_sha256, restore755, then rename to original before old staging operator use','runtime_unchanged':True,'database_restored':False}
 with RECEIPT.open('x') as stream:json.dump(receipt,stream,indent=2);stream.flush();os.fsync(stream.fileno())
 sync(SOURCE.parent)
 SOURCE.unlink();sync(SOURCE.parent)
 receipt['free_bytes_after']=shutil.disk_usage(SOURCE.parent).free
 print(json.dumps(receipt))
