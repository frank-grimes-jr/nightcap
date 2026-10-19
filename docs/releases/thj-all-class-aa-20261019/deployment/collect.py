import json,sys
from pathlib import Path
sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
root=Path('/opt/nightcap/releases/all-class-aa-20261019')
result={'receipts':{p.relative_to(root/'evidence').as_posix():json.loads(p.read_text()) for p in (root/'evidence').rglob('*.json') if 'private-backup' not in p.parts},'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}}
print(json.dumps(result))