"""Fresh five-binary release from the verified deployed source, retaining hardening."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-throw-stone-build-20261009')
INPUT=Path('/tmp/nightcap-zone-hunt-hardened-input')
OUT=Path('/tmp/nightcap-zone-hunt-hardened-build-20261009')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:r=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:
        lines=(OUT/(name+'.log')).read_text().splitlines();print('\n'.join(x for x in lines if 'error:' in x.lower())[-3500:]);print('\n'.join(lines[-12:]));raise RuntimeError(name+' failed')
prior=json.loads((BASE/'manifest.json').read_text());assert fingerprints(BASE/'source')==prior['source_files'],'Deployed source drift'
assert sha(BASE/'build/bin/zone')==prior['binaries']['zone']
OUT.mkdir(exist_ok=False);source=OUT/'source'
shutil.copytree(BASE/'source',source,ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
changed=json.loads((INPUT/'changed.json').read_text());added=json.loads((INPUT/'added.json').read_text())
for name in changed:
    p=source/name;p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
for label,args in [('patch-check',['--dry-run']),('patch-apply',[])]:
    run(label,['patch','--batch','--forward','--fuzz=0','--no-backup-if-mismatch',*args,'-p1','-i',str(INPUT/'changes.patch')],source)
for name in added:
    p=source/name;assert not p.exists(),name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(INPUT/'added'/name,p)
before=fingerprints(source)
assert {n for n,h in before.items() if prior['source_files'].get(n)!=h}==set(changed)|set(added)
assert set(prior['source_files'])<=set(before)
targets=['world','zone','shared_memory','ucs','loginserver']
run('configure',['cmake','-S',str(source),'-B',str(OUT/'build'),*prior['cmake_flags']])
run('build',['cmake','--build',str(OUT/'build'),'--target',*targets,'-j','4'])
assert fingerprints(source)==before and fingerprints(BASE/'source')==prior['source_files']
run('crypto',[str(OUT/'build/bin/loginserver'),'--nightcap-crypto-self-test'])
m={'source_commit':'77f5d63','base_manifest_sha256':sha(BASE/'manifest.json'),'hardening_sha256':prior['hardening_sha256'],'source_files':before,'binaries':{n:sha(OUT/'build/bin'/n) for n in targets},'changed_source_files':changed,'added_source_files':added,'cmake_flags':prior['cmake_flags'],'patch_sha256':sha(INPUT/'changes.patch'),'status':'built_not_installed','private_login_crypto_self_test':'passed'}
(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:v for k,v in m.items() if k not in ('source_files','cmake_flags')}),flush=True)
