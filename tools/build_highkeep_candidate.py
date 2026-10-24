"""Compile a local candidate against the retained Chapterhouse source. No installation."""
import io, json, subprocess, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/dungeons/highkeep-rescue'
DEST='/tmp/nightcap-highkeep-rescue-20261024'
FILES=['common/highkeep_policy.h','zone/highkeep_rescue.inc','zone/dungeon_service.cpp',
       'zone/dungeon_service.h','zone/client.cpp','zone/npc.cpp','zone/aggro.cpp','zone/attack.cpp','zone/spells.cpp']
archive=io.BytesIO()
with tarfile.open(fileobj=archive,mode='w') as tar:
    for name in FILES:
        data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
        info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
extract="""import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=True)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for m in archive:
 assert m.isfile() and m.name in %r
 p=(root/'input'/m.name).resolve();assert root in p.parents
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile(m).read())
""" % (DEST,FILES)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract],input=archive.getvalue(),check=True)
build=r'''
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path('/tmp/nightcap-highkeep-rescue-20261024');base=Path('/tmp/nightcap-chapterhouse-v1');source=root/'source'
manifest=json.loads((base/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in manifest['source_files'].items():
 p=base/'source'/name;assert sha(p)==digest,'Retained source drift: '+name
 target=source/name
 if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for p in (root/'input').rglob('*'):
 if p.is_file():
  t=source/p.relative_to(root/'input');t.parent.mkdir(parents=True,exist_ok=True)
  if not t.exists() or t.read_bytes()!=p.read_bytes():t.write_bytes(p.read_bytes())
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],['cmake','--build',str(root/'build'),'--target','zone','-j4']]
for label,command in zip(('configure','build'),commands):
 print(label+' isolated High Keep candidate',flush=True)
 with (root/(label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:print((root/(label+'.log')).read_text()[-14000:],flush=True);raise SystemExit(r.returncode)
assert all(sha(source/n)==h for n,h in pins.items())
report=dict(status='native zone build passed; not installed',zone_sha256=sha(root/'build/bin/zone'),source_files=pins,baseline_binaries=manifest['binaries'],production_changed=False)
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report['zone_sha256'],flush=True)
'''
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',build],check=True)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/manifest.json',str(OUT/'native-build-manifest.json')],check=True)
