from pathlib import Path,PurePosixPath
import hashlib,json,tarfile
archive=Path('/home/ubuntu/blessing-lifetime-server-20261004-r3.tar.gz')
stage=Path('/opt/nightcap/releases/blessing-lifetime-server-20261004-r3')
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='c98bf9702685688c6c4cc26affbe759490f927a435729a6371b3199a60f39d9c' and not stage.exists()
with tarfile.open(archive) as tar:
    seen=set()
    for m in tar.getmembers():
        p=PurePosixPath(m.name)
        assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.as_posix()==m.name and m.name not in seen and chr(92) not in m.name
        seen.add(m.name)
    stage.mkdir(mode=0o700);tar.extractall(stage,filter='data')
    for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)

import shutil
prior=Path('/opt/nightcap/releases/blessing-lifetime-server-20261004-r2')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(prior/'manifest.json')=='9e4610a7c1eab3891a7b40a1b42e5e1a43503ba28632d62c237ccea3d354c36d'
old=json.loads((prior/'manifest.json').read_text())
new=json.loads((stage/'manifest.json').read_text())
assert new['binaries']==old['binaries'] and new['old_image_id']==old['old_image_id']
(stage/'native-bin').mkdir(mode=0o700)
for n in ('world','zone'):
    name='native-bin/'+n;source=prior/name;target=stage/name
    assert not source.is_symlink() and source.resolve().is_relative_to(prior)
    assert sha(source)==old['files'][name]==new['files'][name]==new['binaries'][n]
    shutil.copyfile(source,target);target.chmod(0o600)
for name,h in new['files'].items():
    p=stage/name;assert not p.is_symlink() and p.resolve().is_relative_to(stage) and sha(p)==h
print(json.dumps({'staged':True,'archive_sha256':'c98bf9702685688c6c4cc26affbe759490f927a435729a6371b3199a60f39d9c','reused_binaries_verified':True,'client_release':new['client_release']}))
