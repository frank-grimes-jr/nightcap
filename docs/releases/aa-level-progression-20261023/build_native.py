"""Fresh complete build from the independently authenticated retained source."""
import hashlib,io,json,subprocess,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEST='/tmp/nightcap-aa-level-progression-v1'
report=json.loads(subprocess.check_output([sys.executable,str(HERE/'review-build-provenance.py')],text=True))
files=report['checkout_delta']
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as tar:
 for name in files:
  data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
  info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
# Explicit streaming extraction, no blind archive traversal.
extract="""
from pathlib import Path
import sys,tarfile
p=Path(%r);p.mkdir(exist_ok=False)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for m in archive:
 assert m.isfile() and m.name in %r
 target=(p/'input'/m.name).resolve();assert p in target.parents
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(archive.extractfile(m).read())
""" % (DEST,files)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract],input=buf.getvalue(),check=True)
build=r"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
report=json.load(sys.stdin);out=Path('/tmp/nightcap-aa-level-progression-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=out/'source';source.mkdir()
base=Path(report['base_source'])
initial=json.loads(Path('/tmp/nightcap-thj-behaviors-v1/final-manifest.json').read_text())['source_files']
for name,h in initial.items():
 original=base/name;assert sha(original)==h
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
for overlay in report['ordered_overlays']:
 for name,entry in overlay['sources'].items():
  original=Path(entry['path']);assert sha(original)==entry['sha256']
  target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
for name in report['checkout_delta']:
 original=out/'input'/name;target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(original,target)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
(out/'source-manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
command=[str(source) if x=='<fresh-source>' else str(out/'build') if x=='<fresh-build>' else x for x in report['fresh_configure_command']]
print('Configuring isolated source and fresh PCH',flush=True)
with (out/'configure.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
command=[str(out/'build') if x=='<fresh-build>' else x for x in report['fresh_build_command']]
print('Building world, zone and shared_memory',flush=True)
with (out/'build.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
assert all(sha(source/name)==h for name,h in pins.items()),'source mutated during build'
binaries={}
for name in ('world','zone','shared_memory'):
 p=out/'build/bin'/name;assert p.is_file();binaries[name]=sha(p)
 r=subprocess.run(['ldd',str(p)],text=True,capture_output=True,check=True)
 assert 'not found' not in r.stdout+r.stderr
report={'status':'fresh complete native build passed','baseline_binaries':report['retained_binaries'],'binaries':binaries,'candidate_sources':{n:sha(out/'input'/n) for n in report['checkout_delta']},'source_files':pins,'rule_catalog_changed':True,'production_changed':False}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'binaries':binaries}),flush=True)
"""
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',build],input=json.dumps(report),text=True,check=True)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/manifest.json',str(HERE/'native-build-manifest.json')],check=True)
