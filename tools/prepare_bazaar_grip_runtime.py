"""Create runtime-only copies after completed integrated build; preserve full debug originals."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST='/tmp/nightcap-paladin-grip-20261026-v1'
CONTAINER='akk-stack-eqemu-server-1'
report=ROOT/'docs/bazaar/private/seller-panel/integrated-build.json'
# Original builder's JSON serializer used a literal trailing backslash-n.
# Accept only that exact suffix and otherwise require ordinary valid JSON.
raw=report.read_text()
if raw.endswith('\\n'):
 data=json.loads(raw[:-2]);report.write_text(json.dumps(data,indent=2)+'\n')
else:data=json.loads(raw)
assert data['status']=='complete integrated zone/world/shared_memory build passed; not installed'
for name,digest in data['source_files'].items():
 path=ROOT/'server-mods/code'/name
 if path.is_file():assert hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
subprocess.run(['docker','cp',str(ROOT/'tools/elf_runtime_identity.py'),CONTAINER+':'+DEST+'/elf_runtime_identity.py'],check=True)
source=r"""
from pathlib import Path
import hashlib,importlib.util,json,subprocess
root=Path('/tmp/nightcap-paladin-grip-20261026-v1')
spec=importlib.util.spec_from_file_location('elf',root/'elf_runtime_identity.py');elf=importlib.util.module_from_spec(spec);spec.loader.exec_module(elf)
assert hashlib.sha256((root/'elf_runtime_identity.py').read_bytes()).hexdigest()==verifier
assert all(hashlib.sha256((root/'source'/n).read_bytes()).hexdigest()==h for n,h in data['source_files'].items())
out=root/'runtime-bin';out.mkdir(exist_ok=False);proof={}
for name,digest in data['binaries'].items():
 original=root/'build/bin'/name
 assert hashlib.sha256(original.read_bytes()).hexdigest()==digest
 subprocess.run(['strip','--strip-debug','-o',str(out/name),str(original)],check=True)
 proof[name]=elf.verify(original,out/name)
 assert proof[name]['original_sha256']==digest
 assert 'not found' not in subprocess.check_output(['ldd',str(out/name)],text=True)
(out/'identity.json').write_text(json.dumps(proof,indent=2))
print(json.dumps(proof))
"""
verifier=hashlib.sha256((ROOT/'tools/elf_runtime_identity.py').read_bytes()).hexdigest()
result=subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'],input='data='+repr(data)+'\nverifier='+repr(verifier)+'\n'+source,check=True,capture_output=True,text=True)
proof=json.loads(result.stdout)
assert set(proof)=={'zone','world','shared_memory'}
(ROOT/'docs/bazaar/private/seller-panel/runtime-identity.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
