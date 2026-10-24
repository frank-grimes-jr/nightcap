"""Build zone from the retained deployed source plus the three reviewed changes."""
import io,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/rogue-tomes-20261024'
DEST='/tmp/nightcap-rogue-tomes-20261024-v1'
FILES=['zone/effects.cpp','zone/client_packet.cpp','zone/client.h']
archive=io.BytesIO()
with tarfile.open(fileobj=archive,mode='w') as tar:
    for name in FILES:
        data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
        entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
extract="""import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=False)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for m in archive:
 assert m.isfile() and m.name in %r
 p=(root/'input'/m.name).resolve();assert root in p.parents
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile(m).read())
""" % (DEST,FILES)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract],input=archive.getvalue(),check=True)
build=r'''
import hashlib,json,shlex,shutil,subprocess
from pathlib import Path
root=Path('/tmp/nightcap-rogue-tomes-20261024-v1');base=Path('/tmp/nightcap-chapterhouse-v1')
manifest=json.loads((base/'manifest.json').read_text());source=root/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='2c9323e43c7287780acf6183b54bbd5800ed4a1e19c7655e1fd6f828de861eb6'
assert sha(base/'build/bin/zone')==manifest['binaries']['zone']==expected
source.mkdir()
for name,digest in manifest['source_files'].items():
 p=base/'source'/name;assert sha(p)==digest,'Retained source drift: '+name
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
# Re-link the exact retained objects before compiling changes, proving lineage.
cwd=base/'build/zone';target=cwd/'CMakeFiles/zone.dir';link=shlex.split((target/'link.txt').read_text())
link[link.index('-o')+1]=str(root/'zone-baseline')
with (root/'baseline-link.log').open('x') as log:r=subprocess.run(link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(root/'baseline-link.log').read_text()[-5000:]
assert sha(root/'zone-baseline')==expected,'Deployed baseline reproduction failed'
changed={}
for p in (root/'input').rglob('*'):
 if p.is_file():
  name=p.relative_to(root/'input').as_posix();changed[name]={'before':sha(source/name),'after':sha(p)};shutil.copy2(p,source/name)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],['cmake','--build',str(root/'build'),'--target','zone','-j2']]
for label,command in zip(('configure','build'),commands):
 print(label+' isolated tome-learning candidate',flush=True)
 with (root/(label+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:print((root/(label+'.log')).read_text()[-9000:],flush=True);raise SystemExit(r.returncode)
assert all(sha(source/n)==h for n,h in pins.items())
assert all(sha(base/'source'/n)==h for n,h in manifest['source_files'].items())
ldd=subprocess.check_output(['ldd',str(root/'build/bin/zone')],text=True);assert 'not found' not in ldd
(root/'ldd.log').write_text(ldd)
report=dict(status='complete zone build passed; not installed',baseline_reproduced=True,baseline_zone_sha256=expected,zone_sha256=sha(root/'build/bin/zone'),source_files=pins,changed_sources=changed,production_changed=False,client_or_cache_changes=False,abi_changed=False)
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='source_files'},flush=True)
'''
OUT.mkdir(parents=True,exist_ok=True)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',build],check=True)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/manifest.json',str(OUT/'native-build-manifest.json')],check=True)
