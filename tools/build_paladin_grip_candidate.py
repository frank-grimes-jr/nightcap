"""Build the grip candidate against retained live source; never install or restart."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DEST = '/tmp/nightcap-paladin-grip-20261026-v1'
BASE = '/tmp/nightcap-bazaar-20261024-v1'
FILES = ['common/item_instance.cpp', 'common/item_instance.h', 'common/patches/rof2.cpp',
         'common/paladin_weapon_grip.h', 'zone/client.h', 'zone/client_packet.cpp', 'zone/inventory.cpp']
sha = lambda data: hashlib.sha256(data).hexdigest()
before, after = {}, {}
archive = io.BytesIO()
with tarfile.open(fileobj=archive, mode='w') as tar:
    for name in FILES:
        if name != 'common/paladin_weapon_grip.h':
            old = subprocess.check_output(['git', 'show', '465003f6:server-mods/code/' + name], cwd=ROOT)
            before[name] = sha(old.replace(b'\r\n', b'\n'))
        data = (ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n', b'\n')
        after[name] = sha(data)
        entry = tarfile.TarInfo(name)
        entry.size = len(data)
        tar.addfile(entry, io.BytesIO(data))
extract = '''import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=True)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for entry in archive:
 assert entry.isfile() and entry.name in %r
 target=root/'input'/entry.name;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(archive.extractfile(entry).read())
''' % (DEST, FILES)
probe = subprocess.run(['docker','exec','akk-stack-eqemu-server-1','pgrep','-af','^(/usr/bin/)?cmake --build '+DEST+'/build'], capture_output=True)
assert probe.returncode == 1, 'Builder active or inspection failed; do not start another build'
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',extract], input=archive.getvalue(), check=True)
build = r'''
import hashlib,json,shutil,subprocess,time
from pathlib import Path
root=Path(DEST);base=Path(BASE)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=base/'manifest.json'
assert sha(manifest)=='a5f5691cd1cf76e47771b3bf2d206f35c8cfb890e4adfb2d27f2e8f5b2ed7a1c'
prior=json.loads(manifest.read_text())
assert sha(base/'build/bin/zone')==prior['zone_sha256']=='84b6b9ff5a5ce598e0e583d948c945b79c7742ee1a9364ddd1ed05148b6c5bc1'
for name,digest in prior['source_files'].items():
 assert sha(base/'source'/name)==digest,'Retained source drift: '+name
for name,digest in before.items():
 assert hashlib.sha256((base/'source'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,'Checkout differs from live retained source: '+name
source=root/'source';source.mkdir(exist_ok=True)
for name,digest in prior['source_files'].items():
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():shutil.copy2(base/'source'/name,target)
 elif name not in after:assert sha(target)==digest,'Candidate unrelated drift: '+name
for name,digest in after.items():
 p=root/'input'/name;assert sha(p)==digest
 target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists() or sha(target)!=digest:shutil.copy2(p,target)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
 '-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
 '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
 '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
 '-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],
 ['cmake','--build',str(root/'build'),'--target','zone','world','shared_memory','-j2']]
logs=[]
for label,cmd in zip(('configure','build'),commands):
 log_path=root/(label+'-'+str(time.time_ns())+'.log');logs.append(str(log_path))
 print(label+': '+str(log_path),flush=True)
 with log_path.open('x') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:print(log_path.read_text()[-10000:],flush=True);raise SystemExit(result.returncode)
assert all(sha(source/n)==h for n,h in pins.items())
assert all(sha(base/'source'/n)==h for n,h in prior['source_files'].items())
binaries={}
for name in ('zone','world','shared_memory'):
 p=root/'build/bin'/name
 assert 'not found' not in subprocess.check_output(['ldd',str(p)],text=True)
 binaries[name]=sha(p)
report=dict(date='2026-10-26',status='complete native build passed; not installed',
 baseline_manifest_sha256=sha(manifest),baseline_zone_sha256=prior['zone_sha256'],
 source_files=pins,changed_sources=after,binaries=binaries,logs=logs,
 production_changed=False,client_verified=False,owner_accepted=False)
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='source_files'}),flush=True)
'''
prefix = f'DEST={DEST!r}\nBASE={BASE!r}\nbefore={before!r}\nafter={after!r}\n'
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',prefix+build], check=True)
assert all(sha((ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n', b'\n')) == digest
           for name, digest in after.items()), 'Checkout changed during build; rerun before recording success'
out = ROOT/'docs/items/paladin-weapon-grip'
out.mkdir(parents=True, exist_ok=True)
raw = subprocess.check_output(['docker','exec','akk-stack-eqemu-server-1','cat',DEST+'/manifest.json'])
report = json.loads(raw)
report['source_file_count'] = len(report.pop('source_files'))
(out/'native-build.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8')
