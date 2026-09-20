"""Publish only reviewed public launcher/patch assets. No server restart or DB writes."""
import hashlib,json,os,shutil,sys,tarfile
from pathlib import Path
ARCHIVE_SHA='29929e395c297bdccefbf539b592f3ec41a062a09349b964c4afda5240088a41'
OLD_GAME='fdbf8486da06342593eca7efebb78916e50c0923a26a7993009d5a715e17f5cc'
OLD_FILES={'channel.json':OLD_GAME,'nightcap-friends.zip':'1e665b6d644b20f88c627ea57a9e388e2ca9d67675cd6c3ed45fbd987b5dd2c8','guide.html':'0fa34d7d4642c7c7d6f64f7f905422c9bf96a9c3d60f12bd5c67fcfbc302fb0c'}
base=Path('/opt/nightcap');stage=base/'releases/patcher-2026092006';public=base/'deploy/production/data/public'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mode=sys.argv[1]
assert mode in ('stage','publish')
if mode=='stage':
 archive=Path('/home/ubuntu/public-patcher.tar.gz');assert sha(archive)==ARCHIVE_SHA
 if not stage.exists():
  pending=stage.with_name('.'+stage.name+'.pending');pending.mkdir(parents=True,exist_ok=True)
  with tarfile.open(archive) as bundle:bundle.extractall(pending,filter='data')
  os.replace(pending,stage)
checks=json.loads((stage/'publication-files.json').read_text())
assert len(checks)==28
for name,expected in checks.items():
 p=stage/name;assert p.resolve().is_relative_to(stage.resolve())
 assert p.stat().st_size==expected['size'] and sha(p)==expected['sha256'],name
if mode=='stage':print('Verified 28 public files; production unchanged.');sys.exit(0)
assert sha(public/'channel.json') in (OLD_GAME,checks['channel.json']['sha256']),'Unexpected live game release; review before publishing'
if (public/'launcher-channel.json').exists():assert sha(public/'launcher-channel.json')==checks['launcher-channel.json']['sha256'],'Unexpected launcher channel'
def copy_verified(source,target,expected):
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and sha(target)==expected:return
 pending=target.with_name(target.name+'.partial')
 shutil.copyfile(source,pending)
 assert sha(pending)==expected
 with pending.open('r+b') as stream:os.fsync(stream.fileno())
 pending.chmod(0o644);os.replace(pending,target)
def directory_verified(source,target,expected):
 if not target.exists():
  pending=target.with_name('.'+target.name+'.patcher-pending')
  pending.mkdir(parents=True,exist_ok=True)
  for name,digest in expected.items():copy_verified(source/name,pending/name,digest)
  for p in [pending,*pending.rglob('*')]:p.chmod(0o755 if p.is_dir() else 0o644)
  os.replace(pending,target)
 for name,digest in expected.items():assert sha(target/name)==digest
backup=stage/'previous-public'
if not backup.exists():
 for name,digest in OLD_FILES.items():assert sha(public/name)==digest,'Original public file changed before backup'
directory_verified(public,backup,OLD_FILES)
# Stage resumably in hidden folders; expose complete immutable directories atomically.
for relative in ('release/2026092006','launcher/2026092001'):
 expected={name[len(relative)+1:]:info['sha256'] for name,info in checks.items() if name.startswith(relative+'/')}
 directory_verified(stage/relative,public/relative,expected)
# New starter downloads are usable at every intermediate publication state.
# Never point either signed channel backwards after a client may have observed it.
for name in ('launcher-channel.json','nightcap-friends.zip','guide.html','channel.json'):
 copy_verified(stage/name,public/name,checks[name]['sha256'])
for name,expected in checks.items():
 if name=='release-audit.json':continue
 assert sha(public/name)==expected['sha256'],name
print(json.dumps({'published_game':2026092006,'published_launcher':2026092001,'desktop_version':'0.3.0','files_verified':27,'backup':str(backup)}))
