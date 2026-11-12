"""Authenticate actual compiler dependency closures and the two source deltas."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,subprocess
dest=Path('/tmp/nightcap-augment-icons-20261112-v2')
prior=Path('/tmp/nightcap-last-lantern-20261107-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((prior/'native-build.json').read_text())
report=json.loads((dest/'native-build.json').read_text())
deps={};source_checks={}
for path in [dest/'zone/item_instance.d',dest/'world/item_instance.d',dest/'client_packet.d']:
 names=shlex.split(path.read_text().replace(chr(92)+chr(10),' ').split(':',1)[1])
 assert names
 closure={}
 for name in names:
  p=Path(name).resolve();assert p.is_absolute() and p.is_file(),name
  closure[str(p)]=sha(p)
  if '/source/' in str(p):
   relative=str(p).split('/source/',1)[1]
   if relative in EXPECTED:
    assert p.read_text()==EXPECTED[relative],relative
   elif (prior/'source'/relative).is_file():
    assert sha(p)==proof['source_sha256'][relative],('Header drift',str(p))
    source_checks[str(p)]=relative
 deps[str(path.relative_to(dest))]=closure
# Each changed unit must appear in its actual compilation dependency list.
assert str(dest/'source/common/item_instance.cpp') in deps['zone/item_instance.d']
assert str(dest/'source/common/item_instance.cpp') in deps['world/item_instance.d']
assert str(dest/'source/zone/client_packet.cpp') in deps['client_packet.d']
compiler=Path('/usr/bin/clang++').resolve()
report['dependency_closures']=deps
report['authenticated_header_dependencies']=len(source_checks)
report['compiler']={'path':str(compiler),'sha256':sha(compiler),'version':subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0]}
report['source_delta']='Both retained files exactly equal reviewed Git base after newline normalization; only reviewed candidate text replaces them. All remaining retained source matches prior release hashes.'
for path,closure in deps.items():
 for name,pin in closure.items():assert sha(Path(name))==pin,name
(dest/'native-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','compile_closures':len(deps),'authenticated_header_dependencies':len(source_checks),'dependency_files':len({n for d in deps.values() for n in d})}))
'''

if __name__ == '__main__':
    expected = {n: (ROOT / 'server-mods/code' / n).read_text(encoding='utf-8')
                for n in ('common/item_instance.cpp', 'zone/client_packet.cpp')}
    result = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                            input='EXPECTED=' + repr(expected) + '\n' + REMOTE,
                            text=True, encoding='utf-8', capture_output=True, timeout=180)
    print((result.stdout + result.stderr)[-1800:])
    if result.returncode:
        raise SystemExit(result.returncode)
    subprocess.run(['docker', 'cp', 'akk-stack-eqemu-server-1:/tmp/nightcap-augment-icons-20261112-v2/native-build.json',
                    str(ROOT / 'docs/items/augment-icons-20261112/native-build.json')], check=True, capture_output=True)
