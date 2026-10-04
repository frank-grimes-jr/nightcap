"""Build all paired binaries in fresh storage; never modifies the running server."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-blessing-lifetime-build-20261004')
INPUT=Path('/tmp/nightcap-free-trade-input-20261004')
OUT=Path('/tmp/nightcap-free-trade-build-20261004')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join((OUT/(name+'.log')).read_text().splitlines()[-35:]),flush=True)
        raise RuntimeError(name+' failed')
prior=json.loads((BASE/'manifest.json').read_text())
assert fingerprints(BASE/'source')==prior['source_files'],'Production source drift'
for name in ('world','zone'):assert sha(BASE/'build/bin'/name)==prior['binaries'][name]
OUT.mkdir(exist_ok=False)
source=OUT/'source'
shutil.copytree(BASE/'source',source,ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
inputs=json.loads((INPUT/'inputs.json').read_text())
changed=json.loads((INPUT/'changed.json').read_text())
for name in changed:
    p=source/name;p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
run('patch-check',['patch','--batch','--forward','--fuzz=0','--dry-run','-p1','-i',str(INPUT/'changes.patch')],source)
run('patch-apply',['patch','--batch','--forward','--fuzz=0','-p1','-i',str(INPUT/'changes.patch')],source)
for name,h in inputs.items():
    p=INPUT/'overlay'/name;assert sha(p)==h,name
    dest=source/name;assert dest.resolve().is_relative_to(source)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
before=fingerprints(source)
assert {n for n,h in before.items() if prior['source_files'].get(n)!=h}==set(inputs)|set(changed)
assert set(prior['source_files'])<=set(before)
targets=['world','zone','shared_memory','ucs','loginserver']
run('configure',['cmake','-S',str(source),'-B',str(OUT/'build'),*prior['cmake_flags']])
run('build',['cmake','--build',str(OUT/'build'),'--target',*targets,'-j','4'])
assert fingerprints(source)==before
assert fingerprints(BASE/'source')==prior['source_files']
result={'base_manifest_sha256':sha(BASE/'manifest.json'),'hardening_sha256':prior['hardening_sha256'],
        'source_files':before,'binaries':{n:sha(OUT/'build/bin'/n) for n in targets},
        'changed_source_files':sorted(set(inputs)|set(changed)),'built_targets':targets,'cmake_flags':prior['cmake_flags'],
        'status':'built_not_installed'}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'binaries':result['binaries']}),flush=True)
