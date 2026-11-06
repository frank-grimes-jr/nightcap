"""Capture retained local build identities and their exact compiled SQL contract."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/dungeons/readiness-20261106'
OUT.mkdir(parents=True, exist_ok=True)
REMOTE = '''import hashlib,json,pathlib
roots=['/tmp/nightcap-power-source-xp-display-20261103-v1','/tmp/nightcap-augment-audit-20261106-v2']
out={}
for r in roots:
 p=pathlib.Path(r);out[r]={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['source/common/dungeon_contract.h','source/zone/dungeon_service.cpp']}
out['header']=(pathlib.Path(roots[1])/'source/common/dungeon_contract.h').read_text()
print(json.dumps(out))
'''
p = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'], input=REMOTE, text=True, capture_output=True, check=True)
data = json.loads(p.stdout)
header = data.pop('header')
contract = {}
for family, section in [('schema', 'SchemaChecks'), ('content', 'ContentChecks')]:
    block = header.split('inline constexpr ContractCheck '+section+'[] = {', 1)[1].split('\n};', 1)[0]
    contract[family] = [dict(label=m[0], sql=m[1], expected=m[2]) for m in re.findall(r'\{"([^"]+)",R"NC\((.*?)\)NC","([^"]+)"\}', block)]
    assert contract[family]
(OUT / 'retained-runtime-contract.json').write_text(json.dumps(contract, indent=2)+'\n')
data['counts'] = {k: len(v) for k, v in contract.items()}
data['scope'] = 'Retained authenticated November6 augment build source; no native/runtime mutation'
(OUT / 'retained-build.json').write_text(json.dumps(data, indent=2)+'\n')
print(json.dumps(data, indent=2))
