import sys,json,hashlib,shutil,subprocess
from pathlib import Path
spec=json.load(sys.stdin)
base=Path('/tmp/nightcap-aa-purchase-20260913'); source=base/'source'
base.mkdir(exist_ok=False); source.mkdir()
old=Path('/tmp/nightcap-aa-bulk-20260913/source')
for rel,digest in spec['manifest'].items():
    path=source/rel
    if not path.resolve().is_relative_to(source): raise RuntimeError('Source path escapes build root')
    raw=(old/rel).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest: raise RuntimeError('Frozen source mismatch: '+rel)
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
for rel,text in spec['overlay'].items(): (source/rel).write_bytes(text.encode())
manifest={rel:hashlib.sha256((source/rel).read_bytes()).hexdigest() for rel in spec['manifest']}
(base/'full-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(base/'configure-command.json').write_text(json.dumps(spec['configure'],indent=2)+'\n')
with (base/'configure.log').open('wb') as log: config=subprocess.run(spec['configure'],stdout=log,stderr=subprocess.STDOUT)
if config.returncode: raise SystemExit('Configure failed; read configure.log')
with (base/'build.log').open('wb') as log: build=subprocess.run(['cmake','--build',str(source/'build'),'--target','zone','tests','-j','2'],stdout=log,stderr=subprocess.STDOUT)
if build.returncode: raise SystemExit('Build failed; read build.log')
with (base/'cpp-tests.log').open('wb') as log: tests=subprocess.run([str(source/'build/bin/tests')],cwd=source,stdout=log,stderr=subprocess.STDOUT)
zone=(source/'build/bin/zone').read_bytes()
checks={'source_files_checked':len(manifest),'source_mismatches':[p for p,d in manifest.items() if hashlib.sha256((source/p).read_bytes()).hexdigest()!=d], 'build_exit_code':build.returncode,'cpp_exit_code':tests.returncode,'zone_bytes':len(zone),'zone_magic':zone[:4].hex(),'zone_sha256':hashlib.sha256(zone).hexdigest(),'overlay':{p:manifest[p] for p in spec['overlay']}}
(base/'build-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks))
raise SystemExit(tests.returncode)
