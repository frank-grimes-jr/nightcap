"""Fresh read-only public-content capture; keeps the original audit capture intact."""
import importlib.util
import json
from pathlib import Path
import subprocess
from probe import SSH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('audit_capture', ROOT / 'tools/capture_augment_audit.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
queries = {k:v for k,v in module.QUERIES.items() if k not in ('spawns','sources')}
code = module.REMOTE.replace('queries=' + repr(module.QUERIES), 'queries=' + repr(queries))
result = subprocess.run(SSH + ['sudo -n python3 -'], input=code, text=True, encoding='utf-8', capture_output=True, timeout=120)
if result.returncode:
    raise RuntimeError(result.stderr[-2500:])
data = json.loads(result.stdout)
(HERE / 'content-private.json').write_text(json.dumps(data, indent=2) + '\n')
old = json.loads((ROOT / 'docs/audits/augments-20261106/item-preimages.json').read_text())
items = {r['id']: r for r in data['items']}
assert all(items[r['before']['id']] == r['before'] for r in old), 'Item preimage drift'
zones = json.loads((ROOT / 'docs/audits/augments-20261106/zone-preimages.json').read_text())
assert data['zones'] == zones, 'Zone preimage drift'
effects = json.loads((ROOT / 'docs/audits/augments-20261106/effect-preimages.json').read_text())
assert data['effects'] == effects, 'Existing effect drift'
print(json.dumps({'status':'PASS','captured_utc':data['captured_utc'],'item_preimages':len(old),'zones':len(zones),'effects':len(effects)}))
