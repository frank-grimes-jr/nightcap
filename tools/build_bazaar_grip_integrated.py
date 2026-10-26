"""Integrate only after the weapon build is terminal; retain its full source/binaries."""
import hashlib,io,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST='/tmp/nightcap-paladin-grip-20261026-v1'
FILES=['common/bazaar_panel_protocol.h','common/bazaar_panel_query.h','zone/client.h','zone/client_bazaar.cpp']
probe=subprocess.run(['docker','exec','akk-stack-eqemu-server-1','pgrep','-af','^(/usr/bin/)?cmake --build '+DEST+'/build'],capture_output=True,text=True)
assert probe.returncode==1,'Existing builder active or unavailable'
archive=io.BytesIO();pins={}
with tarfile.open(fileobj=archive,mode='w') as tar:
 for name in FILES:
  data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n');pins[name]=hashlib.sha256(data).hexdigest()
  entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
# Stream exact four members into a new exclusive input directory.
extract="""from pathlib import Path
import tarfile,sys
root=Path(%r);dest=root/'bazaar-input';dest.mkdir(exist_ok=False)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for m in archive:
 assert m.isfile() and m.name in %r
 p=dest/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile(m).read())
""" % (DEST,FILES)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract],input=archive.getvalue(),check=True)
source=r"""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
root=Path('/tmp/nightcap-paladin-grip-20261026-v1');source=root/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/'manifest.json')=='e735da5af64bdee27c72d2f82943a290c8ae68d508ff7458bab11d9b6a4261fc'
prior=json.loads((root/'manifest.json').read_text())
assert all(sha(source/n)==h for n,h in prior['source_files'].items())
assert all(sha(root/'build/bin'/n)==h for n,h in prior['binaries'].items())
backup=root/'standalone-weapon';backup.mkdir(exist_ok=False)
assert shutil.disk_usage(root).free>sum((source/n).stat().st_size for n in prior['source_files'])+sum((root/'build/bin'/n).stat().st_size for n in prior['binaries'])+512*1024**2
shutil.copy2(root/'manifest.json',backup/'manifest.json');shutil.copytree(source,backup/'source');(backup/'bin').mkdir()
for n in prior['binaries']:shutil.copy2(root/'build/bin'/n,backup/'bin'/n)
for n,h in overlay.items():
 p=root/'bazaar-input'/n;assert sha(p)==h;shutil.copy2(p,source/n)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
log_path=root/('combined-build-'+str(time.time_ns())+'.log');print(str(log_path),flush=True)
with log_path.open('x') as log:r=subprocess.run(['cmake','--build',str(root/'build'),'--target','zone','world','shared_memory','-j2'],stdout=log,stderr=subprocess.STDOUT)
if r.returncode:print(log_path.read_text()[-9000:],flush=True);raise SystemExit(r.returncode)
assert all(sha(source/n)==h for n,h in pins.items())
assert all(sha(backup/'source'/n)==h for n,h in prior['source_files'].items())
assert all(sha(backup/'bin'/n)==h for n,h in prior['binaries'].items())
binaries={n:sha(root/'build/bin'/n) for n in prior['binaries']}
for n in binaries:assert 'not found' not in subprocess.check_output(['ldd',str(root/'build/bin'/n)],text=True)
report={'status':'complete integrated zone/world/shared_memory build passed; not installed','source_files':pins,'binaries':binaries,'overlay':overlay,'weapon_manifest_sha256':sha(backup/'manifest.json'),'source_revision':revision,'log':str(log_path),'production_changed':False}
(root/'combined-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='source_files'},flush=True)
"""
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c','overlay='+repr(pins)+'\nrevision='+repr(revision)+'\n'+source],check=True)
assert all(hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h for n,h in pins.items())
out=ROOT/'docs/bazaar/private/seller-panel/integrated-build.json'
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/combined-manifest.json',str(out)],check=True)
