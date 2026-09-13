"""Container-only fresh build of the atomic release candidate; never installs it."""
import hashlib,json,subprocess,sys
from pathlib import Path
spec=json.load(sys.stdin)
old=Path('/tmp/nightcap-aa-purchase-20260913')
base=Path('/tmp/nightcap-aa-release-20260913')
source=base/'source'
base.mkdir(exist_ok=False); source.mkdir()
manifest=json.loads((old/'full-source-manifest.json').read_text())
for rel,digest in manifest.items():
    path=source/rel
    if not path.resolve().is_relative_to(source): raise RuntimeError('Invalid source path')
    raw=(old/'source'/rel).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest: raise RuntimeError('Frozen source changed: '+rel)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
for rel,text in spec['overlay'].items():
    if rel not in manifest: raise RuntimeError('Overlay outside frozen source: '+rel)
    (source/rel).write_bytes(text.encode('utf-8'))
manifest={rel:hashlib.sha256((source/rel).read_bytes()).hexdigest() for rel in manifest}
(base/'full-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
configure=[s.replace(str(old),str(base)) for s in json.loads((old/'configure-command.json').read_text())]
(base/'configure-command.json').write_text(json.dumps(configure,indent=2)+'\n')
with (base/'configure.log').open('wb') as log: result=subprocess.run(configure,stdout=log,stderr=subprocess.STDOUT)
if result.returncode: raise SystemExit('Configure failed; see isolated configure.log')
with (base/'build.log').open('wb') as log: result=subprocess.run(['cmake','--build',str(source/'build'),'--target','zone','tests','-j','2'],stdout=log,stderr=subprocess.STDOUT)
if result.returncode: raise SystemExit('Build failed; see isolated build.log')
fixture=base/'cpp-tests';fixture.mkdir()
with (base/'cpp-tests.log').open('wb') as log: tests=subprocess.run([str(source/'build/bin/tests')],cwd=fixture,stdout=log,stderr=subprocess.STDOUT)
raw=(source/'build/bin/zone').read_bytes()
checks={'source_files_checked':len(manifest),'source_mismatches':[p for p,d in manifest.items() if hashlib.sha256((source/p).read_bytes()).hexdigest()!=d], 'build_exit_code':result.returncode,'cpp_exit_code':tests.returncode,'zone_bytes':len(raw),'zone_sha256':hashlib.sha256(raw).hexdigest(),'overlay':{p:manifest[p] for p in spec['overlay']}}
(base/'build-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks))
raise SystemExit(tests.returncode)
