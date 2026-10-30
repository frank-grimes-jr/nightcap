"""Build all three native targets from authenticated retained source; never install."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = 'akk-stack-eqemu-server-1'
FILES = {
    'common/item_instance.cpp', 'common/item_xp_eligibility.h',
    'common/item_xp_inventory.h', 'common/item_xp_metadata.h', 'common/item_xp_policy.h',
    'common/paladin_weapon_grip.h', 'common/patches/rof2.cpp', 'common/ruletypes.h',
    'common/shareddb.cpp', 'zone/advanced_loot_inventory.cpp',
    'zone/advanced_loot_inventory.h', 'zone/bonuses.cpp', 'zone/client.h',
    'zone/client_mods.cpp', 'zone/client_packet.cpp', 'zone/command.cpp',
    'zone/command.h', 'zone/exp.cpp', 'zone/inventory.cpp',
    'zone/spell_effects.cpp', 'zone/spells.cpp',
}


def main():
    hate_path = ROOT/'docs/dungeons/hate-layout-20261029/native-build/manifest.json'
    faction_path = ROOT/'docs/releases/faction-standing-20261029/release/native-build.json'
    hate = json.loads(hate_path.read_bytes())
    faction = json.loads(faction_path.read_bytes())
    assert hashlib.sha256(hate_path.read_bytes()).hexdigest() == faction['baseline_manifest_sha256']
    expected = {**hate['all_sources'], **faction['changed_sources']}
    overlay = {p.relative_to(ROOT/'server-mods/code').as_posix():
               hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (ROOT/'server-mods/code').rglob('*') if p.is_file()}
    assert set(overlay)-set(faction['source_overlay']) == {n for n in FILES if n not in expected}
    assert not set(faction['source_overlay'])-set(overlay)
    dest = '/tmp/nightcap-item-xp-full-' + uuid.uuid4().hex[:12]
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        for name in overlay:
            data = (ROOT/'server-mods/code'/name).read_bytes()
            entry = tarfile.TarInfo(name); entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))
    unpack = '''import sys,tarfile
from pathlib import Path
root=Path(DEST);root.mkdir(exist_ok=False)
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
 for entry in archive:
  assert entry.isfile() and entry.name in allowed
  p=root/'input'/entry.name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(archive.extractfile(entry).read())
'''
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-c',
                    f'DEST={dest!r}\nallowed={set(overlay)!r}\n'+unpack], input=archive.getvalue(), check=True)
    remote = r'''
import hashlib,json,shutil,subprocess,time
from pathlib import Path
root=Path(DEST);base=Path(faction['candidate_root']);source=root/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'zone')==faction['zone_sha256'],'Retained faction executable changed'
for name,h in expected.items():assert sha(base/'source'/name)==h,'Retained source drift: '+name
changed=set()
for name,h in overlay.items():
 p=root/'input'/name;assert sha(p)==h
 if name not in expected or p.read_bytes().replace(b'\r\n',b'\n')!=(base/'source'/name).read_bytes().replace(b'\r\n',b'\n'):
  changed.add(name)
assert changed==FILES,'Unreviewed source delta: '+str(changed^FILES)
source.mkdir()
for name,h in expected.items():
 p=source/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/'source'/name,p)
for name in changed:
 p=source/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'input'/name,p)
pins={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
commands=[['cmake','-S',str(source),'-B',str(root/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
 '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
 '-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
 '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
 '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
 '-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],
 ['cmake','--build',str(root/'build'),'--target','zone','world','shared_memory','-j2']]
report={'date':'2026-10-30','status':'building; not installed','candidate_root':DEST,
 'baseline_root':str(base),'baseline_manifest_sha256':baseline_hash,
 'baseline_zone_sha256':faction['zone_sha256'],'all_sources':pins,
 'changed_sources':{n:overlay[n] for n in sorted(changed)},'commands':commands,
 'production_changed':False,'owner_accepted':False}
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('Candidate: '+DEST,flush=True)
for label,command in zip(('configure','build'),commands):
 log=root/(label+'.log');print(label+': '+str(log),flush=True)
 with log.open('x') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
 if result.returncode:
  report['status']=label+' failed';report['returncode']=result.returncode
  (root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
  print(log.read_text()[-10000:],flush=True);raise SystemExit(result.returncode)
for name,h in expected.items():assert sha(base/'source'/name)==h
for name,h in pins.items():assert sha(source/name)==h
report['binaries']={}
for name in ('zone','world','shared_memory'):
 p=root/'build/bin'/name
 dependencies=subprocess.check_output(['ldd',str(p)],text=True)
 assert 'not found' not in dependencies
 report['binaries'][name]={'sha256':sha(p),'bytes':p.stat().st_size,'ldd':dependencies}
report['logs']={n:sha(root/n) for n in ('configure.log','build.log')}
report['status']='complete paired native build passed; not installed'
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],flush=True)
'''
    prefix = (f'DEST={dest!r}\nfaction={faction!r}\nexpected={expected!r}\n'
              f'overlay={overlay!r}\nFILES={FILES!r}\n'
              f'baseline_hash={hashlib.sha256(faction_path.read_bytes()).hexdigest()!r}\n')
    print('Isolated build: '+dest, flush=True)
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'], input=prefix+remote,
                   text=True, encoding='utf-8', check=True)
    assert all(hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes()).hexdigest()==h for n,h in overlay.items())
    result = subprocess.check_output(['docker','exec',CONTAINER,'cat',dest+'/manifest.json'])
    (ROOT/'docs/items/power-source-xp/native-build.json').write_bytes(result)


if __name__ == '__main__':
    main()
