"""Build an isolated zone candidate from the verified Chapterhouse source.

No runtime installation, database access, service restart or client change.
"""
import io
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/releases/aggro-zone-cleanup-20261024'
DEST = '/tmp/nightcap-aggro-cleanup-20261024-' + uuid.uuid4().hex[:12]
FILES = ('zone/spawn2.cpp', 'zone/zone_save_state.cpp', 'zone/attack.cpp', 'zone/client.cpp', 'zone/client.h')
CONTAINER = 'akk-stack-eqemu-server-1'


def main():
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        for name in FILES:
            data = (ROOT / 'server-mods/code' / name).read_bytes().replace(b'\r\n', b'\n')
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))
    extract = '''import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=False)
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
 for entry in archive:
  assert entry.isfile() and entry.name in %r
  path=(root/'input'/entry.name).resolve();assert root in path.parents
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(archive.extractfile(entry).read())
''' % (DEST, FILES)
    subprocess.run(['docker', 'exec', '-i', CONTAINER, 'python3', '-c', extract],
                   input=archive.getvalue(), check=True)
    build = r'''
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(TASK_ROOT)
base=Path('/tmp/nightcap-chapterhouse-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='2c9323e43c7287780acf6183b54bbd5800ed4a1e19c7655e1fd6f828de861eb6'
assert sha(base/'build/bin/zone')==expected,'Retained deployed baseline changed'
manifest=json.loads((base/'manifest.json').read_text())
assert manifest['binaries']['zone']==expected
for name,digest in {
 'zone/entity.cpp':'dbb2a48464f7038996a4f7f9c282ceb7c6a5ee31ba27708279156805b8b5ee4e',
 'zone/mob_ai.cpp':'54d4810d70bfcb3b207a3c7f7bd6c147762a4b7f4a3caace401f3fd1fd747e47',
 'zone/waypoints.cpp':'8ecd6d584bbb5fbcddc2e87f1707daf7c74232653a0613c732d14328e6819fee',
 'zone/xtargetautohaters.cpp':'1a7ddf7276dff38825f4f9c2d53566b3014d3325f9fcfbb2462ff888a0b685cd'
}.items():
 assert manifest['source_files'][name]==digest,'Native fixture helper drift: '+name
source=root/'source';source.mkdir(exist_ok=False)
for name,digest in manifest['source_files'].items():
 p=base/'source'/name
 assert sha(p)==digest,'Retained source drift: '+name
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
changed=[]
for p in (root/'input').rglob('*'):
 if p.is_file():
  name=p.relative_to(root/'input').as_posix()
  if sha(p)!=manifest['source_files'][name]:changed.append(name)
  shutil.copy2(p,source/name)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],['cmake','--build',str(root/'build'),'--target','zone','-j2']]
for label,command in zip(('configure','build'),commands):
 print(label+' isolated aggro cleanup candidate',flush=True)
 with (root/(label+'.log')).open('w') as log:
  result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:
  print((root/(label+'.log')).read_text()[-9000:],flush=True);raise SystemExit(result.returncode)
assert all(sha(source/name)==digest for name,digest in pins.items())
report=dict(status='native zone build passed; not installed',base_zone_sha256=expected,
 build_root=str(root),fresh_output_directory=True,
 binaries={'zone':sha(root/'build/bin/zone')},changed_sources=sorted(changed),
 source_files=pins,production_changed=False)
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='source_files'}),flush=True)
'''.replace('TASK_ROOT', repr(DEST))
    subprocess.run(['docker', 'exec', '-i', CONTAINER, 'python3', '-c', build], check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['docker', 'cp', CONTAINER + ':' + DEST + '/manifest.json',
                    str(OUT / 'native-build-manifest.json')], check=True)


if __name__ == '__main__':
    main()
