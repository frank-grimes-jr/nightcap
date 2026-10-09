import difflib,hashlib,json,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-advloot-production-20260930-reviewed')
OUT=Path('/tmp/nightcap-advloot-actions-build-20261002')
INPUT=Path('/tmp/nightcap-advloot-actions-fix-input-20261002')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
prior=json.loads((BASE/'manifest.json').read_text());fix=json.loads((INPUT/'manifest.json').read_text())
assert fingerprints(BASE/'source')==prior['source_files']
source=OUT/'source';before=fingerprints(source)
assert {n for n,h in before.items() if prior['source_files'].get(n)!=h}==set(fix['files'])
assert set(before)==set(prior['source_files'])
for n,h in fix['files'].items():
    assert sha(source/n)==h['before'] and sha(INPUT/n)==h['after'],n
for n in fix['files']:(source/n).write_bytes((INPUT/n).read_bytes())
final=fingerprints(source)
diff=[]
for n in sorted(fix['files']):diff.extend(difflib.unified_diff((BASE/'source'/n).read_text().splitlines(True),(source/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n))
(OUT/'production-source.patch').write_text(''.join(diff))
(OUT/'build-correction.json').write_text(json.dumps(fix,indent=2)+'\n')
print(json.dumps({'stage':'resume corrected C++17 build','source_commit':fix['source_commit']}),flush=True)
with (OUT/'build-corrected.log').open('w') as log:
    result=subprocess.run(['cmake','--build',str(OUT/'build'),'--target','world','zone','-j','4'],stdout=log,stderr=subprocess.STDOUT)
if result.returncode:
    print('\n'.join((OUT/'build-corrected.log').read_text().splitlines()[-25:]),flush=True);raise RuntimeError('Corrected build failed')
assert fingerprints(source)==final and fingerprints(BASE/'source')==prior['source_files']
binaries={**prior['binaries'],**{n:sha(OUT/'build/bin'/n) for n in ('world','zone')}}
m={'source_commit':fix['source_commit'],'base_manifest_sha256':sha(BASE/'manifest.json'),'hardening_sha256':prior['hardening_sha256'],'correction_manifest_sha256':sha(INPUT/'manifest.json'),'patch_sha256':sha(OUT/'production-source.patch'),'source_files':final,'binaries':binaries,'changed_source_files':sorted(fix['files']),'built_targets':['world','zone'],'cmake_flags':prior['cmake_flags'],'unchanged_binary_source':prior['unchanged_binary_source'],'status':'built_not_installed'}
(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'status':m['status'],'binaries':binaries}),flush=True)
