"""Fresh CMake zone build from the verified patched production source."""
import hashlib,json,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-zone-hunt-hardened-build-20261009')
OUT=Path('/tmp/nightcap-npc-heal-build-20261009')
SOURCE=OUT/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:
        print((OUT/(name+'.log')).read_text()[-5000:],flush=True);raise RuntimeError(name+' failed')
prior=json.loads((BASE/'manifest.json').read_text());assert files(BASE/'source')==prior['source_files']
assert sha(BASE/'build/bin/zone')==prior['binaries']['zone']
before=files(SOURCE)
assert set(before)==set(prior['source_files'])
assert [n for n,h in before.items() if h!=prior['source_files'][n]]==['zone/spells.cpp']
assert not (OUT/'build').exists()
run('configure',['cmake','-S',str(SOURCE),'-B',str(OUT/'build'),*prior['cmake_flags']])
run('build',['cmake','--build',str(OUT/'build'),'--target','zone','-j','4'])
assert files(SOURCE)==before and files(BASE/'source')==prior['source_files']
assert sha(BASE/'build/bin/zone')==prior['binaries']['zone']
m={'source_commit':'26a2e7d','base_manifest_sha256':sha(BASE/'manifest.json'),'source_files':before,
   'changed_source_files':['zone/spells.cpp'],'base_binaries':prior['binaries'],
   'binaries':{**prior['binaries'],'zone':sha(OUT/'build/bin/zone')},'cmake_flags':prior['cmake_flags'],
   'patch_sha256':sha(Path('/tmp/nightcap-npc-heal-input-20261009/heal.patch')),
   'regressions':'99/99 passed on patched production source','status':'fresh_built_not_installed'}
(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({k:m[k] for k in ('binaries','changed_source_files','regressions','status')}),flush=True)
