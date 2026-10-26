"""Build an isolated zone from authenticated retained source; never install it."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import sys

ROOT=Path(__file__).resolve().parents[1]
DEST='/tmp/nightcap-bazaar-20261024-v1'
BASE='/tmp/nightcap-october24-integrated-v2'
FILES=['common/bazaar.cpp','common/bazaar.h','common/bazaar_escrow.h','common/bazaar_search_policy.h','zone/client_bazaar.cpp',
       'zone/trading.cpp','zone/client.h','zone/client_packet.cpp','zone/command.cpp','zone/command.h','zone/CMakeLists.txt']
probe=subprocess.run(['docker','exec','akk-stack-eqemu-server-1','pgrep','-af','^(/usr/bin/)?cmake --build '+DEST+'/build'],capture_output=True,text=True)
if probe.returncode==0:raise RuntimeError('Candidate build still active; observe its existing handle')
if probe.returncode!=1:raise RuntimeError('Unable to verify candidate builder state')
archive=io.BytesIO()
with tarfile.open(fileobj=archive,mode='w') as tar:
    for name in FILES:
        data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
        entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
extract="""import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=%r)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for m in archive:
 assert m.isfile() and m.name in %r
 p=(root/'input'/m.name).resolve();assert root in p.parents
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile(m).read())
""" % (DEST,"--resume" in sys.argv,FILES)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract],input=archive.getvalue(),check=True)
build=r"""
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path('/tmp/nightcap-bazaar-20261024-v1');base=Path('/tmp/nightcap-october24-integrated-v2')
manifest=json.loads((base/'manifest.json').read_text());source=root/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='4f37ee330f43bf2f6f5aea7883f314ca4803c3583d032915415ed833d365c744'
assert sha(base/'build/bin/zone')==manifest['binaries']['zone']==expected
earlier=json.loads(Path('/tmp/nightcap-rogue-tomes-20261024-v1/manifest.json').read_text())
source.mkdir(exist_ok=True)
for name,digest in manifest['source_files'].items():
 p=base/'source'/name;assert sha(p)==digest,'Retained source drift: '+name
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():shutil.copy2(p,target)
 elif not (root/'input'/name).exists():
  assert sha(target) in (digest,earlier['source_files'].get(name)),'Unexpected candidate drift: '+name
  if sha(target)!=digest:shutil.copy2(p,target)
changed={}
for p in (root/'input').rglob('*'):
 if p.is_file():
  name=p.relative_to(root/'input').as_posix();changed[name]={'before':manifest['source_files'].get(name),'after':sha(p)}
  if not (source/name).exists() or sha(source/name)!=sha(p):shutil.copy2(p,source/name)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],['cmake','--build',str(root/'build'),'--target','zone','-j2']]
for label,command in zip(('configure','build'),commands):
 print(label+' isolated Commonlands bazaar candidate',flush=True)
 import time
 log_path=root/(label+'-'+str(time.time_ns())+'.log')
 print(str(log_path),flush=True)
 with log_path.open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:print(log_path.read_text()[-9000:],flush=True);raise SystemExit(r.returncode)
assert all(sha(source/n)==h for n,h in pins.items())
assert all(sha(base/'source'/n)==h for n,h in manifest['source_files'].items())
ldd=subprocess.check_output(['ldd',str(root/'build/bin/zone')],text=True);assert 'not found' not in ldd
report=dict(status='complete zone build passed; not installed',baseline_zone_sha256=expected,baseline_source='ad7a42069b28eb47dbcd6c061c2640c68aafe580',zone_sha256=sha(root/'build/bin/zone'),source_files=pins,changed_sources=changed,production_changed=False,client_verified=False,owner_accepted=False)
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='source_files'},flush=True)
"""
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',build],check=True)
out=ROOT/'docs/bazaar/private';out.mkdir(parents=True,exist_ok=True)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/manifest.json',str(out/'native-build-manifest.json')],check=True)
