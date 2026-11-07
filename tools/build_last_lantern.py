"""Build in an isolated retained-source overlay. Never install or restart."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/adventure-journal/release-20261107'
REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
aug=Path('/tmp/nightcap-augment-audit-20261106-v2')
ready=Path('/tmp/nightcap-dungeon-readiness-20261106-v2')
current=Path('/tmp/nightcap-dungeon-readiness-stats-20261106-v1')
stats=Path('/tmp/nightcap-character-stats-window-20261106-v3')
dest=Path('/tmp/nightcap-last-lantern-20261107-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not dest.exists():
 dest.mkdir()
 shutil.copytree(old/'source',dest/'source',symlinks=False)
 shutil.copytree(aug/'source',dest/'source',dirs_exist_ok=True)
 for n in ('zone/client.h','zone/command.cpp','zone/gm_commands/nightcapui.cpp','common/equipped_stats_protocol.h'):
  shutil.copyfile(stats/'source'/n,dest/'source'/n)
 shutil.copyfile(ready/'source/common/dungeon_contract.h',dest/'source/common/dungeon_contract.h')
 (dest/'retained-before.json').write_text(json.dumps({n:sha(dest/'source'/n) for n in SOURCES if (dest/'source'/n).is_file()},indent=2))
for n,s in SOURCES.items():
 p=dest/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def run(args,cwd,label):
 with (dest/(label+'.log')).open('w') as log:
  r=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError(label+'\n'+(dest/(label+'.log')).read_text()[-6500:])
for category,unit in UNITS:
 flags=(old/f'build/{category}/CMakeFiles/{category if category=="common" else "zone"}.dir/flags.make').read_text()
 parts=[next(l.split(' = ',1)[1] for l in flags.splitlines() if l.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
 args=['/usr/bin/clang++','-I'+str(dest/'source'),'-I'+str(aug/'source')]+shlex.split(' '.join(parts))
 if category=='zone':
  pch=dest/'cmake_pch.hxx';pch.write_text((aug/'cmake_pch.hxx').read_text().replace(str(aug/'source'),str(dest/'source')))
  args+=['-include',str(pch)]
 args+=['-c',str(dest/'source'/category/unit),'-o',str(dest/(unit+'.o'))]
 run(args,old/'build',unit)
 print(json.dumps({'compiled':unit,'sha256':sha(dest/(unit+'.o'))}),flush=True)
print(json.dumps({'status':'compiled','directory':str(dest)}))
'''


def main():
    names = ('common/last_lantern_policy.h', 'common/last_lantern_inventory.h',
             'common/last_lantern_scene_policy.h', 'common/last_lantern_catalog.h',
             'common/shareddb.cpp', 'zone/advanced_loot_inventory.cpp', 'zone/advanced_loot_inventory.h',
             'zone/pets.cpp', 'zone/dungeon_service.cpp', 'zone/dungeon_service.h',
             'zone/highkeep_rescue.inc', 'zone/last_lantern.inc', 'zone/spawn2.cpp', 'zone/attack.cpp', 'zone/task_manager.cpp', 'zone/task_client_state.cpp')
    sources = {n: (ROOT / 'server-mods/code' / n).read_text(encoding='utf-8') for n in names}
    import sys
    wanted=sys.argv[1:] or ['dungeon_service.cpp', 'advanced_loot_inventory.cpp', 'pets.cpp', 'spawn2.cpp', 'shareddb.cpp']
    units=[('common' if n=='shareddb.cpp' else 'zone',n) for n in wanted]
    prefix=f'SOURCES={sources!r}\nUNITS={units!r}\n'
    p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+REMOTE,
                     text=True,encoding='utf-8',capture_output=True,timeout=1800)
    (OUT/'native-compile.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    print((p.stdout+'\n'+p.stderr)[-7000:])
    if p.returncode: raise SystemExit(p.returncode)


if __name__=='__main__':main()
