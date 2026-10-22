"""Stage the approved immutable package and run the reviewed operator."""
import argparse,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/hate-keeper-commonlands-20261022'
def remote(source):return subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('stage','preflight','activate'));action=p.parse_args().action
    if action!='stage':
        subprocess.run(SSH+['sudo','-n','python3',STAGE+'/rollout.py',action],check=True);return
    receipt=json.loads((HERE/'package.json').read_text());archive=Path(receipt['package'])
    assert archive.name=='approved-main-v1.tar.gz'
    remote(f"from pathlib import Path;import shutil;p=Path({STAGE!r});assert not p.exists();assert shutil.disk_usage(p.parent).free>2000*1024**2;print('New stage and disk reserve checked.')")
    upload='/home/ubuntu/hate-keeper-approved-main-v1.tar.gz'
    subprocess.run(['scp',*SSH[1:-1],str(archive),SSH[-1]+':'+upload],check=True)
    remote(f'''
import hashlib,json,os,shutil,tarfile,uuid
from pathlib import Path,PurePosixPath
os.umask(0o077);archive=Path({upload!r});stage=Path({STAGE!r})
assert hashlib.sha256(archive.read_bytes()).hexdigest()=={receipt['sha256']!r}
assert not stage.exists();temporary=stage.with_name(stage.name+'-staging-'+uuid.uuid4().hex[:12]);temporary.mkdir(mode=0o700)
with tarfile.open(archive) as tar:
 members=tar.getmembers();manifest=json.load(tar.extractfile('manifest.json'))
 assert {{m.name for m in members}}==set(manifest['files'])|{{'manifest.json'}}
 assert len(members)==len(manifest['files'])+1
 for m in members:
  name=PurePosixPath(m.name);assert m.isfile() and not name.is_absolute() and '..' not in name.parts and '\\\\' not in m.name
  dest=temporary/m.name;assert dest.resolve().is_relative_to(temporary)
  dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as out:shutil.copyfileobj(tar.extractfile(m),out)
  dest.chmod(0o755 if m.name=='bin/zone' else 0o600)
  if m.name!='manifest.json':assert hashlib.sha256(dest.read_bytes()).hexdigest()==manifest['files'][m.name]
assert manifest['source_revision']=='a736fb02937931254456daf8954d7466a6aa1c28'
temporary.rename(stage)
print(json.dumps({{'staged':str(stage),'source_revision':manifest['source_revision'],'package_sha256':{receipt['sha256']!r}}}))
''')
if __name__=='__main__':main()
