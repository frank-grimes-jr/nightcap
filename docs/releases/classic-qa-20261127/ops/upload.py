"""Stage an immutable, allowlisted release package and optionally run its operator."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile

from capture import SSH

INSTALL = """
import hashlib, io, os, pathlib, sys, tarfile, tempfile
root=pathlib.Path('/opt/nightcap/releases')
pin=sys.argv[1]
assert len(pin)==64 and all(c in '0123456789abcdef' for c in pin)
stage=root/('classic-qa-20261127-'+pin[:12])
assert not stage.is_symlink() and stage.resolve().parent==root
stage.mkdir(mode=0o700,exist_ok=True)
allowed=set(sys.argv[2:])
seen=set()
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as archive:
    for item in archive:
        n=item.name
        assert n in allowed-seen and item.isfile() and 0<item.size<300_000_000
        p=stage/n
        p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        assert p.resolve().is_relative_to(stage) and not p.is_symlink()
        with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as out:
            import shutil
            shutil.copyfileobj(archive.extractfile(item),out)
            tmp=pathlib.Path(out.name)
        try:
            if p.exists():
                assert p.read_bytes()==tmp.read_bytes(), n
            else:
                os.link(tmp,p)
        finally:
            tmp.unlink()
        seen.add(n)
assert seen==allowed and hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()==pin
print(stage)
"""


def main(stage,action):
    manifest=stage/'manifest.json'
    m=json.loads(manifest.read_bytes())
    sha=hashlib.sha256(manifest.read_bytes()).hexdigest()
    names=sorted({'manifest.json','zone', *m['operator'], *('before/'+n for n in m['before']), *('after/'+n for n in m['after'])})
    dest='/opt/nightcap/releases/classic-qa-20261127-'+sha[:12]
    if action=='upload':
        with tempfile.TemporaryFile() as f:
            with tarfile.open(fileobj=f,mode='w:gz',compresslevel=2) as bundle:
                for name in names:
                    bundle.add(stage/name,arcname=name,recursive=False)
            f.seek(0)
            command=shlex.join(['sudo','-n','python3','-c',INSTALL,sha,*names])
            subprocess.run([*SSH,command],stdin=f,check=True)
    else:
        cmd=shlex.join(['sudo','-n','python3',dest+'/release.py',action])
        subprocess.run([*SSH,cmd],check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('stage',type=Path)
    p.add_argument('action',choices=['upload','prepare','activate','verify','rollback'])
    args=p.parse_args()
    main(args.stage,args.action)

