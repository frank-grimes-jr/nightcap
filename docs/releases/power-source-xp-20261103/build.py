"""Build world/zone/shared_memory from the deployed Hunt-rates source plus Power Source item XP; never install.

Seventeen item-XP files are unchanged on the live base since the Oct 31 candidate and are
copied from it. Four (SSF-era) are three-way merged; any conflict aborts.
"""
import json
import subprocess

LIVE = '/tmp/nightcap-zone-hunt-rates-20261101-v1'
LIVE_ZONE = '90717ac7da93f2fe7c4c2ba0243bf093c45ce3eb456cc33cfc27ffc74b3a52b5'  # stripped, deployed Nov 2
OLD = '/tmp/nightcap-hate-boss-placement-20261030-v1'  # base of the Oct 31 candidate
ITEM = '/tmp/nightcap-item-xp-live-20261031-v1'      # Oct 31 Power Source candidate tree
DEST = '/tmp/nightcap-power-source-xp-20261103-v1'
FILES = ('common/item_instance.cpp common/item_xp_eligibility.h common/item_xp_inventory.h '
         'common/item_xp_metadata.h common/item_xp_policy.h common/paladin_weapon_grip.h '
         'common/patches/rof2.cpp common/ruletypes.h common/shareddb.cpp zone/advanced_loot_inventory.cpp '
         'zone/advanced_loot_inventory.h zone/bonuses.cpp zone/client.h zone/client_mods.cpp '
         'zone/client_packet.cpp zone/command.cpp zone/command.h zone/exp.cpp zone/inventory.cpp '
         'zone/spell_effects.cpp zone/spells.cpp').split()

CODE = r'''
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
live=Path(LIVE);old=Path(OLD)/'source';item=Path(ITEM);dest=Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda p:p.read_bytes().replace(b'\r\n',b'\n') if p.exists() else None
assert not dest.exists()
assert json.loads((live/'shipping-identity.json').read_text())['sha256']==LIVE_ZONE==sha(live/'shipping/zone')
pins=json.loads((item/'manifest.json').read_text())['source_pins']
for name in FILES:assert sha(item/'source'/name)==pins[name],'candidate drift '+name
dest.mkdir();shutil.copytree(live/'source',dest/'source',symlinks=True)
how={}
for name in FILES:
 cur,base,cand=norm(live/'source'/name),norm(old/name),norm(item/'source'/name)
 crlf=(live/'source'/name).exists() and b'\r\n' in (live/'source'/name).read_bytes()
 if cur==base:text,how[name]=cand,'candidate'
 else:
  with tempfile.TemporaryDirectory() as t:
   paths=[]
   for label,data in (('ours',cur),('base',base),('theirs',cand)):
    p=Path(t)/label;p.write_bytes(data);paths.append(str(p))
   r=subprocess.run(['git','merge-file','-p',*paths],capture_output=True)
   assert r.returncode==0,'merge conflict '+name
   text,how[name]=r.stdout,'merged'
 if crlf:text=text.replace(b'\n',b'\r\n')
 p=dest/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text)
src={n:sha(dest/'source'/n) for n in FILES}
(dest/'manifest.json').write_text(json.dumps({'live_baseline':LIVE,'live_zone':LIVE_ZONE,'candidate':ITEM,'candidate_base':OLD,'method':how,'changed_sources':src},indent=2)+'\n')
cmd=['cmake','-S',str(dest/'source'),'-B',str(dest/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON']
for label,command in [('configure',cmd),('build',['cmake','--build',str(dest/'build'),'--target','world','zone','shared_memory','-j8'])]:
 with (dest/(label+'.log')).open('x') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(label+' failed: '+str(dest/(label+'.log')))
print(json.dumps({'status':'built','root':DEST,'method':how,'binaries':{n:sha(dest/'build/bin'/n) for n in ('world','zone','shared_memory')}}))
'''

def main():
    preamble = ''.join(f'{n}={v!r}\n' for n, v in {'LIVE': LIVE, 'LIVE_ZONE': LIVE_ZONE, 'OLD': OLD,
                                                   'ITEM': ITEM, 'DEST': DEST, 'FILES': FILES}.items())
    subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                   input=preamble + CODE, text=True, check=True)

if __name__ == '__main__':
    main()
