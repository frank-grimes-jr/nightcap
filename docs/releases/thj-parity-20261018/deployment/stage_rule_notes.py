"""Stage the reviewed recovery and corrected descriptions without changing live SQL."""
import base64
import hashlib
import json
from pathlib import Path
from remote import run

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
files={'resume_rule_notes.py':(HERE/'resume_rule_notes.py').read_bytes()}
for mode in ('forward','disable','enable'):
    files['spell-'+mode+'.sql']=(HERE.parent/'content'/('rules-'+mode+'.sql')).read_bytes()
    files['heroic-'+mode+'.sql']=(ROOT/'docs/releases/wpm-melee-20261018/content'/('heroic-rule-'+mode+'.sql')).read_bytes()
manifest={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
payload={n:base64.b64encode(b).decode() for n,b in files.items()}
source=r'''
import base64,fcntl,hashlib,json,os
from pathlib import Path
stage=Path('/opt/nightcap/releases/thj-parity-20261018')
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert list((stage/'evidence').glob('held-*.json')) and not (stage/'evidence/activated-closed.json').exists()
 target=stage/'rule-notes-recovery';target.mkdir(mode=0o700,exist_ok=False)
 data=PAYLOAD;manifest=MANIFEST
 for name,encoded in data.items():
  assert Path(name).name==name
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==manifest[name]
  with (target/name).open('xb') as f:f.write(raw)
 (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'staged_files':len(data),'production_sql_written':False}))
'''.replace('PAYLOAD',repr(payload)).replace('MANIFEST',repr(manifest))
print(run(source).decode())
(HERE/'rule-notes-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
