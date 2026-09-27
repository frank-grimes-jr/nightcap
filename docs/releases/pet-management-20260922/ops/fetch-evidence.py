"""Export only sanitized deployment evidence; private SQL/config stays on host."""
from pathlib import Path
import importlib.util,json
stage=Path('/opt/nightcap/releases/pet-management-20260922')
spec=importlib.util.spec_from_file_location('pet_rollout',stage/'rollout.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m=r.manifest();p=r.load('preflight.json')
record={name:r.load(name) for name in ('backup.json','rehearsal.json','epoch-before.json','verified-before-open.json','activated.json')}
record['manifest']={k:v for k,v in m.items() if k!='files'}
record['manifest_sha256']=r.sha(stage/'manifest.json')
record['post_deployment']=r.running(p['new_image_id'],m['binaries'])
assert r.state('gateway')['State']['Running']
record['post_deployment']['gateway_running']=True
record['runtime_unchanged']=r.runtime_files()==p['runtime'];assert record['runtime_unchanged']
client=Path('/opt/nightcap/releases/pet-client-2026092201')
if (client/'published.json').exists():record['client']=json.loads((client/'published.json').read_text())
print(json.dumps(record,indent=2))
