"""Stage/run this release only. Never print configuration or database secrets."""
import argparse,json,subprocess
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('release_remote',HERE.parents[1]/'quests/camil-chapterhouse/deployment/remote.py')
remote_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote_module);SSH=remote_module.SSH
STAGE='/opt/nightcap/releases/october-24-coordinated-20261024-v2'
ARCHIVE=HERE/'private/v2/release.tar.gz'

def remote(script):
 r=subprocess.run(SSH+['sudo -n python3 -'],input=script,text=True,capture_output=True,timeout=1800)
 if r.returncode:raise RuntimeError(r.stderr[-6000:])
 return r.stdout

def stage():
 receipt=json.loads((HERE/'package-receipt.json').read_text())
 dest='/tmp/nightcap-october-24-coordinated-20261024.tar.gz'
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(ARCHIVE),SSH[-1]+':'+dest],check=True)
 script='''import hashlib,json,os,tarfile
from pathlib import Path
os.umask(0o077)
archive=Path(ARCHIVE);root=Path(STAGE)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==DIGEST
root.mkdir(exist_ok=False)
with tarfile.open(archive) as tar:
 for m in tar:
  target=root/m.name
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  assert target.resolve().is_relative_to(root)
  target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(tar.extractfile(m).read())
  target.chmod(m.mode)
manifest=json.loads((root/'manifest.json').read_text())
for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({'staged_files':len(manifest['files']),'stage':str(root),'archive_sha256':DIGEST}))
'''.replace('ARCHIVE',repr(dest)).replace('STAGE',repr(STAGE)).replace('DIGEST',repr(receipt['archive_sha256']))
 result=json.loads(remote(script));(HERE/'private/v2/staging-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def action(name):
 path=HERE/(name+'.log')
 assert not path.exists(),'Preserve previous attempt log'
 print('Starting '+name,flush=True)
 with path.open('w',encoding='utf-8') as log:
  r=subprocess.run(SSH+['sudo -n python3 '+STAGE+'/rollout.py '+name],stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 print(path.read_text(encoding='utf-8')[-6000:],flush=True)
 if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('stage','preflight','activate','open'));a=p.parse_args()
 stage() if a.action=='stage' else action(a.action)
