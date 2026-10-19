"""Import the frozen starter policy, leaving its original checkout untouched."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path('E:/EQ_Local_Dev/_worktrees/weapon-tier-damage')
names=['tools/starter_retune.py','tools/gear_progression.py','tools/tests/test_starter_retune.py',
       'docs/items/starter-retune-reference.json']
names += [p.relative_to(SOURCE).as_posix() for p in (SOURCE/'docs/releases/starter-retune-20261018').glob('*') if p.is_file()]
manifest={}
for name in names:
    data=(SOURCE/name).read_bytes();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    manifest[name]=hashlib.sha256(data).hexdigest()
(Path(__file__).with_name('starter-snapshot.json')).write_text(json.dumps({'head':subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip(),'source':str(SOURCE),'files':manifest},indent=2)+'\n')
print('Imported',len(names),'starter files')
