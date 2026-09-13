"""Apply reviewed fixes to the completed isolated fresh build and rebuild."""
import hashlib,json,subprocess,sys
from pathlib import Path
spec=json.load(sys.stdin);base=Path('/tmp/nightcap-aa-release-20260913');source=base/'source'
manifest=json.loads((base/'full-source-manifest.json').read_text())
for rel,digest in manifest.items():
    if hashlib.sha256((source/rel).read_bytes()).hexdigest()!=digest: raise RuntimeError('Prior source changed: '+rel)
(base/'initial-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for rel,text in spec['overlay'].items():
    if rel not in manifest: raise RuntimeError('Overlay outside frozen source')
    (source/rel).write_bytes(text.encode('utf-8'))
manifest={rel:hashlib.sha256((source/rel).read_bytes()).hexdigest() for rel in manifest}
(base/'full-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (base/'review-build.log').open('wb') as log: build=subprocess.run(['cmake','--build',str(source/'build'),'--target','zone','tests','-j','2'],stdout=log,stderr=subprocess.STDOUT)
if build.returncode: raise SystemExit('Reviewed build failed; see review-build.log')
fixture=base/'cpp-tests-review';fixture.mkdir()
with (base/'review-cpp-tests.log').open('wb') as log: tests=subprocess.run([str(source/'build/bin/tests')],cwd=fixture,stdout=log,stderr=subprocess.STDOUT)
raw=(source/'build/bin/zone').read_bytes()
checks={'source_files_checked':len(manifest),'source_mismatches':[p for p,d in manifest.items() if hashlib.sha256((source/p).read_bytes()).hexdigest()!=d], 'build_exit_code':build.returncode,'cpp_exit_code':tests.returncode,'zone_bytes':len(raw),'zone_sha256':hashlib.sha256(raw).hexdigest(),'overlay':{p:manifest[p] for p in spec['overlay']}}
(base/'review-build-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks));raise SystemExit(tests.returncode)
