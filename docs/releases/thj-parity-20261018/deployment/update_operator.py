"""Guarded preparation-only operator revision; never permitted after activation."""
import base64
import hashlib
import json
from pathlib import Path
from remote import run

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[3].parent/'thj-parity-production-stage'
manifest=json.loads((OUT/'manifest.json').read_text())
old_hash=manifest['files']['rollout.py']
raw=(HERE/'rollout.py').read_bytes()
new_hash=hashlib.sha256(raw).hexdigest()
assert new_hash!=old_hash
source=r'''
import base64,fcntl,hashlib,json,os
from pathlib import Path
stage=Path('/opt/nightcap/releases/thj-parity-20261018')
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (stage/'evidence').exists(), 'Successful preflight already sealed'
 m=json.loads((stage/'manifest.json').read_text())
 path=stage/'rollout.py';old=path.read_bytes()
 assert hashlib.sha256(old).hexdigest()==m['files']['rollout.py']==OLD
 raw=base64.b64decode(DATA);assert hashlib.sha256(raw).hexdigest()==NEW
 backup=stage/('rollout-before-'+OLD[:12]+'.py')
 with backup.open('xb') as f:f.write(old)
 path.write_bytes(raw);m['files']['rollout.py']=NEW
 (stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'before':OLD,'after':NEW,'production_runtime_unchanged':True}))
'''.replace('OLD',repr(old_hash)).replace('NEW',repr(new_hash)).replace('DATA',repr(base64.b64encode(raw).decode()))
print(run(source).decode())
manifest['files']['rollout.py']=new_hash
(OUT/'rollout.py').write_bytes(raw)
for p in (OUT/'manifest.json',HERE/'manifest.json'):
    p.write_text(json.dumps(manifest,indent=2)+'\n')
