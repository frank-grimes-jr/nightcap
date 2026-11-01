"""Build item XP from the authenticated Hate boss production source; never install."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = '/tmp/nightcap-hate-boss-placement-20261030-v1'
ITEM = '/tmp/nightcap-item-xp-full-c4802fa0a9ad'
DEST = '/tmp/nightcap-item-xp-live-20261031-v1'
REPORT = Path('E:/EQ_Local_Dev/_worktrees/hate-density/docs/dungeons/hate-boss-placement-20261030/native-build.json')

def run(script):
    return subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],
        input=script, text=True, check=True)

def main():
    from build_item_xp import FILES
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    original = json.loads((ROOT/'docs/items/power-source-xp/native-build.json').read_text(encoding='utf-8'))
    files = sorted(FILES)
    code = '''import hashlib,json,shutil,subprocess
from pathlib import Path
live=Path(LIVE);item=Path(ITEM);old=Path(OLD);dest=Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists()
for name,h in REPORT['changed_sources'].items():assert sha(live/'source'/name)==h,name
for name,h in REPORT['binaries'].items():assert sha(live/'build/bin'/name)==h,name
assert sha(item/'manifest.json')==MANIFEST_SHA,'item manifest'
assert sha(item/'build/bin/zone')==ZONE_SHA,'item zone'
for name in FILES:
 a=old/'source'/name;b=live/'source'/name;c=item/'source'/name
 if name not in ('zone/command.cpp','zone/command.h'):
  if a.exists():assert a.read_bytes()==b.read_bytes(),'live baseline drift '+name
  assert c.exists()
dest.mkdir();shutil.copytree(live/'source',dest/'source',symlinks=True)
for name in FILES:
 if name not in ('zone/command.cpp','zone/command.h'):
  p=dest/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item/'source'/name,p)
for name,needle,insert in (
 ('zone/command.cpp','\\t\\tcommand_add("factions",','\\t\\tcommand_add("itemxp", "View training progress for the item in your Power Source slot.", AccountStatus::Player, command_itemxp) ||\\n'),
 ('zone/command.h','void command_factions(Client *c, const Seperator *sep);','void command_itemxp(Client *c, const Seperator *sep);\\n')):
 p=dest/'source'/name;s=p.read_text();assert s.count(needle)==1 and 'command_itemxp' not in s
 s=s.replace(needle,insert+needle);p.write_text(s)
for name in ('zone/command.cpp','zone/command.h'):
 original_text=(item/'source'/name).read_text();live_text=(live/'source'/name).read_text();merged=(dest/'source'/name).read_text()
 assert merged.replace('\\t\\tcommand_add("itemxp", "View training progress for the item in your Power Source slot.", AccountStatus::Player, command_itemxp) ||\\n','').replace('void command_itemxp(Client *c, const Seperator *sep);\\n','')==live_text
 assert 'command_itemxp' in merged and 'command_itemxp' in original_text
pins={p.relative_to(dest/'source').as_posix():sha(p) for p in (dest/'source').rglob('*') if p.is_file()}
(dest/'manifest.json').write_text(json.dumps({'live_baseline':LIVE,'item_baseline':ITEM,'source_pins':pins,'item_files':FILES,'live_binary_pins':REPORT['binaries']},indent=2)+'\\n')
cmd=['cmake','-S',str(dest/'source'),'-B',str(dest/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON']
for label,command in [('configure',cmd),('build',['cmake','--build',str(dest/'build'),'--target','world','zone','shared_memory','-j2'])]:
 with (dest/(label+'.log')).open('x') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(label+' failed: '+str(dest/(label+'.log')))
print(json.dumps({'status':'built','root':DEST,'binaries':{n:sha(dest/'build/bin'/n) for n in ('world','zone','shared_memory')}}))
'''
    preamble = ''.join(f'{n}={v!r}\n' for n,v in {
        'LIVE':LIVE,'ITEM':ITEM,'OLD':original['baseline_root'],'DEST':DEST,
        'REPORT':report,'FILES':files,
        'MANIFEST_SHA':'0a62f3ed524e89b1bc2dfae35d7019477adc7b5885d5da03e05d094fedeeeb52',
        'ZONE_SHA':original['binaries']['zone']['sha256']
    }.items())
    run(preamble+code)

if __name__=='__main__':main()
