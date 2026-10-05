from pathlib import Path,PurePosixPath
import hashlib,json,tarfile
archive=Path('/home/ubuntu/free-trade-server-20261004.tar.gz')
stage=Path('/opt/nightcap/releases/free-trade-20261004')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)=='9612a0ab9cb46e7dfbb3da9a8ed3576f0237b4b40e1f09e7ab000f25d6cec40c' and not stage.exists()
with tarfile.open(archive) as tar:
    seen=set()
    for m in tar.getmembers():
        p=PurePosixPath(m.name)
        assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.as_posix()==m.name and m.name not in seen and chr(92) not in m.name
        seen.add(m.name)
    stage.mkdir(mode=0o700);tar.extractall(stage,filter='data')
    for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
m=json.loads((stage/'manifest.json').read_text())
for name,h in m['files'].items():
    p=stage/name;assert not p.is_symlink() and p.resolve().is_relative_to(stage) and sha(p)==h
print(json.dumps({'staged':True,'archive_sha256':'9612a0ab9cb46e7dfbb3da9a8ed3576f0237b4b40e1f09e7ab000f25d6cec40c','client_release':m['client_release']}))
