"""Build zone from the deployed SSF source plus only the per-zone rate patch; never install."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIVE = '/tmp/nightcap-ssf-mode-20261101-v1'
DEST = '/tmp/nightcap-zone-hunt-rates-20261101-v1'
LIVE_ZONE = '2ca5fa0e0b8a002a619a55658f8cfe7141791b2a19ad1a5a5314c124589a878d'  # stripped, deployed by SSF
FILES = ('zone/zone_hunt.cpp', 'common/zone_hunt_policy.h')

def blob(rev, name):
    return subprocess.check_output(['git', 'show', f'{rev}:server-mods/code/{name}'], cwd=ROOT).decode('utf-8')

def main():
    before = {n: blob('b7c53b3c^1', n) for n in FILES}
    after = {n: blob('b7c53b3c', n) for n in FILES}
    code = '''import hashlib,json,shutil,subprocess
from pathlib import Path
live=Path(LIVE);dest=Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists()
assert json.loads((live/'shipping-identity.json').read_text())['sha256']==LIVE_ZONE==sha(live/'shipping/zone')
crlf={}
for name in FILES:
 raw=(live/'source'/name).read_bytes();crlf[name]=b'\\r\\n' in raw  # Oct 9 copied zone_hunt.cpp with CRLF
 assert raw.replace(b'\\r\\n',b'\\n').decode()==BEFORE[name],'deployed source differs from patch base: '+name
dest.mkdir();shutil.copytree(live/'source',dest/'source',symlinks=True)
for name in FILES:(dest/'source'/name).write_bytes((AFTER[name].replace('\\n','\\r\\n') if crlf[name] else AFTER[name]).encode())
changed={n:sha(dest/'source'/n) for n in FILES}
cmd=['cmake','-S',str(dest/'source'),'-B',str(dest/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache','-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake','-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF','-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON']
for label,command in [('configure',cmd),('build',['cmake','--build',str(dest/'build'),'--target','zone','-j8'])]:
 with (dest/(label+'.log')).open('x') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(label+' failed: '+str(dest/(label+'.log')))
print(json.dumps({'status':'built','root':DEST,'changed_sources':changed,'zone':sha(dest/'build/bin/zone')}))
'''
    preamble = ''.join(f'{n}={v!r}\n' for n, v in {'LIVE': LIVE, 'DEST': DEST, 'LIVE_ZONE': LIVE_ZONE,
                                                   'FILES': FILES, 'BEFORE': before, 'AFTER': after}.items())
    subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                   input=preamble + code, text=True, check=True)

if __name__ == '__main__':
    main()
