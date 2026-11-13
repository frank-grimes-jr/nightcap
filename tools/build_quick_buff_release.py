"""Full isolated zone build from the authenticated current native source."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112'
REMOTE=r'''
from pathlib import Path
import hashlib,json,shutil,subprocess,time
base=Path('/tmp/nightcap-augment-icons-20261112-v2')
dest=Path('/tmp/nightcap-quick-buff-full-20261112-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists(),'Existing build attempt; inspect instead of overwrite'
proof=json.loads((base/'native-build.json').read_text())
assert proof['status']=='PASS'
commands=json.loads((base/'link-commands.json').read_text())
dest.mkdir()
c=commands['zone'];args=c['arguments'].copy();args[args.index('-o')+1]=str(dest/'baseline-zone')
with (dest/'baseline-link.log').open('w') as log:
 subprocess.run(args,cwd=c['cwd'],stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run(['strip','--strip-debug','-o',str(dest/'baseline-zone.stripped'),str(dest/'baseline-zone')],check=True)
assert sha(dest/'baseline-zone.stripped')==proof['shipping']['candidate-zone']
print('Current shipping zone reproduced exactly.',flush=True)
for name,pin in BEFORE.items():assert sha(base/'source'/name)==pin, name
shutil.copytree(base/'source',dest/'source')
for name,data in SOURCES.items():
 p=dest/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
pins={str(p.relative_to(dest/'source')):sha(p) for p in (dest/'source').rglob('*') if p.is_file()}
(dest/'source-before-build.json').write_text(json.dumps(pins,indent=2)+'\n')
configure=['cmake','-S',str(dest/'source'),'-B',str(dest/'build'),
 '-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_BUILD_TYPE=RelWithDebInfo',
 '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
 '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
 '-DEQEMU_BUILD_TESTS=OFF','-DEQEMU_BUILD_LOGIN=ON','-DEQEMU_BUILD_CLIENT_FILES=ON',
 '-DEQEMU_BUILD_SERVER=ON','-DEQEMU_BUILD_LUA=ON','-DEQEMU_BUILD_PERL=ON',
 '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
def run(args,label):
 with (dest/(label+'.log')).open('w') as log:
  p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(label+' failed: '+(dest/(label+'.log')).read_text()[-6000:])
run(configure,'configure');print('Fresh CMake zone build configured.',flush=True)
run(['cmake','--build',str(dest/'build'),'--target','zone','-j','3'],'build')
candidate=dest/'build/bin/zone'
subprocess.run(['strip','--strip-debug','-o',str(dest/'candidate-zone.stripped'),str(candidate)],check=True)
ldd=subprocess.check_output(['ldd',str(dest/'candidate-zone.stripped')],text=True);assert 'not found' not in ldd
identity={'__name__':'identity'};exec(IDENTITY,identity)
loaded=identity['verify'](candidate,dest/'candidate-zone.stripped');assert loaded['status']=='PASS'
assert all(sha(base/'source'/n)==h for n,h in BEFORE.items())
assert all(sha(dest/'source'/n)==h for n,h in pins.items())
report=dict(status='PASS',scope='Fresh full zone build including all zone/common/GM/Lua/Perl dependencies; no deployment',
 directory=str(dest),shipping={'baseline-zone':proof['shipping']['candidate-zone'],'candidate-zone':sha(dest/'candidate-zone.stripped')},
 source_sha256=pins,compile_units=len(json.loads((dest/'build/compile_commands.json').read_text())),
 configure=configure,runtime_identity=loaded,ldd=ldd)
(dest/'native-build.json').write_text(json.dumps(report,indent=2)+'\n')
print('REPORT='+json.dumps({k:v for k,v in report.items() if k!='source_sha256'}),flush=True)
'''

def main():
    names=('common/quick_buff.h','zone/aa_quick_buff.inc','zone/aa.cpp','zone/client.h','zone/spells.cpp')
    sources={n:(ROOT/'server-mods/code'/n).read_text(encoding='utf-8') for n in names}
    before={n:hashlib.sha256(subprocess.check_output(['git','show','origin/main:server-mods/code/'+n],cwd=ROOT)).hexdigest()
            for n in names if n.endswith(('.cpp','client.h'))}
    prefix=f'SOURCES={sources!r}\nBEFORE={before!r}\nIDENTITY={(ROOT/"tools/elf_runtime_identity.py").read_text(encoding="utf-8")!r}\n'
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+REMOTE,
        text=True,encoding='utf-8',capture_output=True,timeout=7200)
    (OUT/'full-build.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    print((result.stdout+result.stderr)[-6500:])
    if result.returncode:raise SystemExit(result.returncode)
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-quick-buff-full-20261112-v1/native-build.json',
                    str(OUT/'full-build.json')],check=True,capture_output=True)

if __name__=='__main__':main()
