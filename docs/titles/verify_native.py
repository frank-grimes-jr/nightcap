"""Syntax-check complete changed native units in isolated retained-source copy.

Uses the local November12 full-build inputs, never the runtime source or binary.
This is compilation evidence, not a link, deployment or gameplay test.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = 'akk-stack-eqemu-server-1'
BASE = '/tmp/nightcap-quick-buff-full-20261112-v1'
SCRATCH = '/tmp/nightcap-earned-titles-20261112-' + uuid.uuid4().hex[:10]
FILES = ['zone/titles.cpp', 'zone/earned_titles.h', 'zone/earned_titles.inc',
         'zone/attack.cpp', 'zone/client.cpp', 'zone/command.cpp', 'zone/command.h',
         'common/earned_title_policy.h', 'common/earned_title_catalog.h']
REMOTE = r'''
import hashlib,json,pathlib,shlex,shutil,subprocess,sys,tarfile
payload=json.load(sys.stdin); base=pathlib.Path(payload['base']); scratch=pathlib.Path(payload['scratch'])
if scratch.exists(): raise SystemExit('scratch already exists; retain evidence and choose a new run path')
scratch.mkdir()
shutil.copytree(base/'source',scratch/'source',symlinks=True)
baseline=(scratch/'source/zone/titles.cpp').read_bytes()
assert hashlib.sha256(baseline).hexdigest()=='2f66a4b7b99247218423110d1259c08ea5a56c0b4e1f849fb9b72a67e3f76e5a'
with tarfile.open('/tmp/nightcap-earned-titles-overlay.tar') as bundle:
 for member in bundle.getmembers():
  assert member.isfile() and member.name in payload['hashes'],member.name
  (scratch/'source'/member.name).write_bytes(bundle.extractfile(member).read())
for name,expected in payload['hashes'].items():
 assert hashlib.sha256((scratch/'source'/name).read_bytes()).hexdigest()==expected,name
pch=(base/'build/zone/CMakeFiles/zone.dir/cmake_pch.hxx').read_text().replace(str(base/'source'),str(scratch/'source'))
(scratch/'cmake_pch.hxx').write_text(pch)
commands=json.loads((base/'build/compile_commands.json').read_text())
template=next(c for c in commands if c['file'].endswith('/titles.cpp'))
flags=shlex.split(template['command'])
flags=flags[:flags.index('-Xclang')]
flags=[s.replace(str(base/'source'),str(scratch/'source')) for s in flags if s!='-Winvalid-pch']
flags+=['-include',str(scratch/'cmake_pch.hxx'),'-fsyntax-only']
report={'scope':'Complete native syntax checks; not linked, deployed or player accepted','source_sha256':payload['hashes'],'units':[]}
for name in ['titles.cpp','attack.cpp','client.cpp','command.cpp']:
 print('Compiling '+name,flush=True)
 cmd=flags+[str(scratch/'source/zone'/name)]
 run=subprocess.run(cmd,capture_output=True,text=True)
 (scratch/(name+'.log')).write_text(run.stdout+run.stderr)
 report['units'].append({'unit':name,'status':'PASS' if run.returncode==0 else 'FAIL','command':cmd})
 if run.returncode: print((run.stdout+run.stderr)[-12000:],flush=True)
report['status']='PASS' if all(x['status']=='PASS' for x in report['units']) else 'FAIL'
(scratch/'native-compile.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],flush=True)
sys.exit(0 if report['status']=='PASS' else 1)
'''


def main():
    hashes = {name: hashlib.sha256((ROOT/'server-mods/code'/name).read_bytes()).hexdigest() for name in FILES}
    with tempfile.TemporaryDirectory() as temp:
        bundle = Path(temp)/'overlay.tar'
        with tarfile.open(bundle, 'w') as archive:
            for name in FILES:
                archive.add(ROOT/'server-mods/code'/name, arcname=name)
        subprocess.run(['docker', 'cp', str(bundle), CONTAINER+':/tmp/nightcap-earned-titles-overlay.tar'], check=True)
    process = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'python3', '-c', REMOTE],
                             input=json.dumps(dict(base=BASE,scratch=SCRATCH,hashes=hashes)), text=True)
    subprocess.run(['docker', 'cp', CONTAINER+':'+SCRATCH+'/native-compile.json', str(ROOT/'docs/titles/native-compile.json')], check=True)
    raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
