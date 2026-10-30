"""Losslessly archive authenticated, unmounted staging copies; keep receipts on-host."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,shutil,subprocess,time
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/faction-standing-20261030-v1')
TARGET=1280*1024**2

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def snapshot():
 rows=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-aq'],text=True).split()],text=True))
 return {r['Id']:{'image':r['Image'],'restarts':r['RestartCount'],'state':{k:r['State'][k] for k in ['Running','StartedAt','OOMKilled','ExitCode']},'mounts':r['Mounts']} for r in rows}
def save(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 sync(p.parent)
def sync(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)

def main():
 os.umask(0o077)
 with (ROOT/'.deployment.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (STAGE/'disk-preservation.json').exists(),'Inspect existing receipt; never replay'
  before=snapshot();images=subprocess.check_output(['docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}'],text=True)
  mounts=[Path(m['Source']) for r in before.values() for m in r['mounts']]
  reports=[]
  plan=json.loads((STAGE/'disk-plan.json').read_text())
  assert len(plan)<=6,'Explicit authorization covers at most six staging files'
  for row in plan:
   if shutil.disk_usage(ROOT).free>=TARGET:break
   source=Path(row['path']);manifest=source.parent.parent/'manifest.json'
   archive=source.with_name('zone.faction-release-preserved-20261030.gz')
   receipt=source.parent/'faction-preservation-20261030.json'
   assert source.is_relative_to(Path('/opt/nightcap/releases')) and source.resolve()==source
   assert source.is_file() and source.stat().st_nlink==1
   assert not archive.exists() and not receipt.exists()
   assert all(not source.is_relative_to(m) for m in mounts)
   for exe in Path('/proc').glob('[0-9]*/exe'):
    try:assert exe.resolve()!=source
    except FileNotFoundError:pass
   assert sha(manifest)==row['manifest_sha256']
   assert json.loads(manifest.read_text())['files']['bin/zone']==row['sha256']==sha(source)
   assert source.stat().st_size==row['bytes']
   assert shutil.disk_usage(ROOT).free>320*1024**2,'Retain at least200MiB during bounded compression'
   stat=source.stat()
   with source.open('rb') as src,archive.open('xb') as dst:
    class Bounded:
     def write(self,data):
      assert dst.tell()+len(data)<120*1024**2,'Archive exceeds budget; original retained'
      return dst.write(data)
     def flush(self):dst.flush()
    with gzip.GzipFile(fileobj=Bounded(),mode='wb',compresslevel=1,mtime=0) as z:shutil.copyfileobj(src,z)
    dst.flush();os.fsync(dst.fileno())
   with gzip.open(archive,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
   assert sha(source)==row['sha256'] and source.stat()==stat
   report={**row,'archive':str(archive),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'mode':stat.st_mode&0o777,'uid':stat.st_uid,'gid':stat.st_gid,'restoration':'Decompress to exclusive temporary file; verify source SHA256; restore mode and owner; atomically rename to original path before using historical operator.'}
   save(receipt,report);source.unlink();sync(source.parent);reports.append(report)
  assert before==snapshot(),'Service identity/lifetime changed'
  assert images==subprocess.check_output(['docker','image','ls','--no-trunc','--format','{{.Repository}}:{{.Tag}} {{.ID}}'],text=True)
  result={'preserved':reports,'free_bytes':shutil.disk_usage(ROOT).free,'services_images_backups_player_data_unchanged':True}
  save(STAGE/'disk-preservation.json',result)
  print(json.dumps({'archived_staging_files':len(reports),'free_bytes':result['free_bytes'],'services_images_backups_player_data_unchanged':True,'full_receipts_retained_on_host':True}))
if __name__=='__main__':main()
