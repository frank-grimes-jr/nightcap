"""Reconcile the completed companion handoff without overwriting our edits."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
manifest=json.loads((REL/'companion-snapshot.json').read_text())
source=Path(manifest['source'])
def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(source),*args]).decode()
names=set(git('diff','--name-only','-z').split('\0'))|set(git('ls-files','--others','--exclude-standard','-z').split('\0'))
allowed=('server-mods/','tools/','eq-client-dll/','eq-launcher/','config/','wiki/','docs/releases/thj-pet-scaling-20261018/','docs/releases/wpm-melee-20261018/')
changed={};conflicts=[]
for name in sorted(n for n in names if n and (n.startswith(allowed) or n in ('CHANGES.md','docs/status.md'))):
    data=(source/name).read_bytes();digest=sha(data);prior=manifest['files'].get(name)
    if digest==prior:continue
    target=ROOT/name
    if target.exists() and sha(target.read_bytes()) not in (prior,digest):
        conflicts.append(name);continue
    target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    changed[name]=digest
if conflicts:raise RuntimeError('Reconcile manually: '+repr(conflicts))
out=REL/'companion-final-snapshot.json'
if out.exists():raise RuntimeError('Already recorded final handoff')
manifest['files'].update(changed);manifest['status']='completed companion handoff, tested separately; combined acceptance pending'
out.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'refreshed':list(changed),'total':len(manifest['files'])}))
