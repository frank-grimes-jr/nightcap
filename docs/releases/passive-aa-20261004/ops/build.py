"""Fresh five-target passive-AA build over the fingerprinted production source."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-free-trade-build-20261004')
INPUT=Path('/tmp/nightcap-passive-aa-release-input-20261004')
OUT=Path('/tmp/nightcap-passive-aa-build-20261004-r2')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join((OUT/(name+'.log')).read_text().splitlines()[-40:]),flush=True)
        raise RuntimeError(name+' failed')
prior=json.loads((BASE/'manifest.json').read_text())
assert fingerprints(BASE/'source')==prior['source_files'],'Production source drift'
for n,h in prior['binaries'].items():assert sha(BASE/'build/bin'/n)==h,n
OUT.mkdir(exist_ok=False)
source=OUT/'source'
shutil.copytree(BASE/'source',source,ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
changed=json.loads((INPUT/'changed.json').read_text())
assert len(changed)==8
for name in changed:
    p=source/name;p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
run('patch-check',['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch','--dry-run','-p1','-i',str(INPUT/'changes.patch')],source)
run('patch-apply',['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(INPUT/'changes.patch')],source)
before=fingerprints(source)
assert {n for n,h in before.items() if prior['source_files'].get(n)!=h}==set(changed)
assert set(before)==set(prior['source_files'])
targets=['world','zone','shared_memory','ucs','loginserver']
run('configure',['cmake','-S',str(source),'-B',str(OUT/'build'),*prior['cmake_flags']])
run('build',['cmake','--build',str(OUT/'build'),'--target',*targets,'-j','4'])
assert fingerprints(source)==before
assert fingerprints(BASE/'source')==prior['source_files']
run('crypto',[str(OUT/'build/bin/loginserver'),'--nightcap-crypto-self-test'])
result={'base_manifest_sha256':sha(BASE/'manifest.json'),'hardening_sha256':prior['hardening_sha256'],
        'source_files':before,'binaries':{n:sha(OUT/'build/bin'/n) for n in targets},
        'changed_source_files':changed,'built_targets':targets,'cmake_flags':prior['cmake_flags'],
        'patch_sha256':sha(INPUT/'changes.patch'),'feature_commit':'f8037ab',
        'status':'built_not_installed','private_login_crypto_self_test':'passed'}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'binaries':result['binaries']}),flush=True)
