"""Freeze companion source without writing its checkout. Run once per named snapshot."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PET=Path('C:/Users/verre/Documents/Codex/2026-10-18/goa/work/thj-pet-scaling')
def git(*args):return subprocess.check_output(['git','-C',str(PET),*args])
def sha(b):return hashlib.sha256(b).hexdigest()
names=set(git('diff','--name-only','-z').decode().split('\0'))|set(git('ls-files','--others','--exclude-standard','-z').decode().split('\0'))
allowed=('server-mods/','tools/','eq-client-dll/','eq-launcher/','config/','wiki/','docs/releases/thj-pet-scaling-20261018/','docs/releases/wpm-melee-20261018/')
names=sorted(n for n in names if n and (n.startswith(allowed) or n in ('CHANGES.md','docs/status.md')))
out=Path(__file__).with_name('companion-snapshot.json')
if out.exists():raise SystemExit('Snapshot already exists; reconcile drift explicitly')
contents={n:(PET/n).read_bytes() for n in names}
assert all((PET/n).read_bytes()==b for n,b in contents.items()),'Concurrent source write'
for n,b in contents.items():
    p=ROOT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
out.write_text(json.dumps({'source':str(PET),'head':git('rev-parse','HEAD').decode().strip(),
    'status':'pending uncommitted companion source; not accepted','files':{n:sha(b) for n,b in contents.items()}},indent=2)+'\n')
print('Frozen companion files:',len(names))
