"""Build zone from the deployed Power Source source plus only the display patch; never install."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIVE = '/tmp/nightcap-power-source-xp-20261103-v1'
DEST = '/tmp/nightcap-power-source-xp-display-20261103-v1'
LIVE_ZONE = '7b61b96ce59e00cc1c28f2b68148bbea21f51b59bd584b16fc9eb45bead867b5'  # stripped, deployed Nov 3
PATCH = '85dd2cea2caa2a2ab12ff288f16aef408a95eed7'
FILES = ('common/item_xp_policy.h', 'common/patches/rof2.cpp', 'zone/advanced_loot_inventory.cpp',
         'zone/advanced_loot_inventory.h', 'zone/inventory.cpp')

CODE = r'''
import hashlib,json,shutil,subprocess
from pathlib import Path
live=Path(LIVE);dest=Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists()
assert json.loads((live/'shipping-identity.json').read_text())['zone']['sha256']==LIVE_ZONE==sha(live/'shipping/zone')
crlf={}
for name in FILES:
 raw=(live/'source'/name).read_bytes();crlf[name]=b'\r\n' in raw
 assert raw.replace(b'\r\n',b'\n').decode()==BEFORE[name],'deployed source differs from patch base: '+name
dest.mkdir();shutil.copytree(live/'source',dest/'source',symlinks=True)
for name in FILES:(dest/'source'/name).write_bytes((AFTER[name].replace('\n','\r\n') if crlf[name] else AFTER[name]).encode())
changed={n:sha(dest/'source'/n) for n in FILES}
cmd=['cmake','-S',str(dest/'source'),'-B',str(dest/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON']
for label,command in [('configure',cmd),('build',['cmake','--build',str(dest/'build'),'--target','zone','-j8'])]:
 with (dest/(label+'.log')).open('x') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(label+' failed: '+str(dest/(label+'.log')))
print(json.dumps({'status':'built','root':DEST,'changed_sources':changed,'zone':sha(dest/'build/bin/zone')}))
'''

def blob(rev, name):
    raw = subprocess.check_output(['git', 'show', f'{rev}:server-mods/code/{name}'], cwd=ROOT)
    return raw.replace(b'\r\n', b'\n').decode('utf-8')

def main():
    before = {n: blob(PATCH + '^', n) for n in FILES}
    after = {n: blob(PATCH, n) for n in FILES}
    preamble = ''.join(f'{n}={v!r}\n' for n, v in {'LIVE': LIVE, 'DEST': DEST, 'LIVE_ZONE': LIVE_ZONE, 'FILES': FILES,
                                                   'BEFORE': before, 'AFTER': after}.items())
    subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                   input=preamble + CODE, text=True, encoding='utf-8', check=True)

if __name__ == '__main__':
    main()
