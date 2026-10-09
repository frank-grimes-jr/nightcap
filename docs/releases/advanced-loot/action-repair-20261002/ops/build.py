"""Fresh paired build over the exact preserved hardened production source."""
import difflib,hashlib,json,shutil,subprocess,time
from pathlib import Path

BASE=Path('/tmp/nightcap-advloot-production-20260930-reviewed')
INPUT=Path('/tmp/nightcap-advloot-actions-input-20261002')
OUT=Path('/tmp/nightcap-advloot-actions-build-20261002')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:
        r=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:
        print('\n'.join((OUT/(name+'.log')).read_text().splitlines()[-30:]),flush=True)
        raise RuntimeError(name+' failed')

prior=json.loads((BASE/'manifest.json').read_text())
assert fingerprints(BASE/'source')==prior['source_files'],'Hardened production source drift'
assert sha(BASE/'build/bin/zone')==prior['binaries']['zone']
for name,digest in prior['binaries'].items():
    path=BASE/'build/bin'/name if name in prior['built_targets'] else Path(prior['unchanged_binary_source'])/name
    assert sha(path)==digest,name
inputs=json.loads((INPUT/'input-manifest.json').read_text())
for name,digest in inputs['files'].items():
    assert sha(INPUT/name)==digest,name
OUT.mkdir(exist_ok=False)
source=OUT/'source'
shutil.copytree(BASE/'source',source,ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
for name in inputs['modified']:
    p=source/name
    p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
run('patch-check',['patch','--batch','--forward','--fuzz=0','--dry-run','-p1','-i',str(INPUT/'tracked-changes.patch')],source)
run('patch-apply',['patch','--batch','--forward','--fuzz=0','-p1','-i',str(INPUT/'tracked-changes.patch')],source)
overlaid=[]
for name in inputs['added']:
    p=source/name
    if p.exists():overlaid.append(name)
    p.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(INPUT/'added'/name,p)
before=fingerprints(source)
expected=set(inputs['added']+inputs['modified'])
changed={name for name,digest in before.items() if prior['source_files'].get(name)!=digest}
assert changed==expected,(changed,expected)
assert not set(prior['source_files'])-set(before)
diff=[]
for name in sorted(changed):
    old=BASE/'source'/name
    diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],(source/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(OUT/'production-source.patch').write_text(''.join(diff))
(OUT/'prepared.json').write_text(json.dumps({'changed':sorted(changed),'existing_new_overlays':overlaid,'input_manifest':inputs},indent=2)+'\n')
build=OUT/'build'
run('configure',['cmake','-S',str(source),'-B',str(build),*prior['cmake_flags']])
run('build',['cmake','--build',str(build),'--target','world','zone','-j','4'])
assert fingerprints(source)==before,'Source changed during build'
assert fingerprints(BASE/'source')==prior['source_files'],'Production baseline source changed'
binaries={**prior['binaries'],**{name:sha(build/'bin'/name) for name in ('world','zone')}}
manifest={'source_commit':inputs['candidate_commit'],'production_main':inputs['production_main'],
          'base_manifest_sha256':sha(BASE/'manifest.json'),'hardening_sha256':prior['hardening_sha256'],
          'input_manifest_sha256':sha(INPUT/'input-manifest.json'),'patch_sha256':sha(OUT/'production-source.patch'),
          'source_files':before,'binaries':binaries,'changed_source_files':sorted(changed),
          'built_targets':['world','zone'],'cmake_flags':prior['cmake_flags'],
          'unchanged_binary_source':prior['unchanged_binary_source'],'status':'built_not_installed'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'status':manifest['status'],'binaries':binaries}),flush=True)
