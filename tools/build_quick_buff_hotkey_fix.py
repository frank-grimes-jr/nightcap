"""Reproduce deployed full build, then compile the two affected translation units."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112/hotkey-fix'
REMOTE=r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
base=Path('/tmp/nightcap-quick-buff-full-20261112-v1')
dest=Path('/tmp/nightcap-quick-buff-hotkey-20261112-v2')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((base/'instrument-correction.json').read_text())
assert proof['status']=='PASS'
assert not dest.exists(),'Inspect existing build; never overwrite'
for n,pin in proof['source_sha256'].items():assert sha(base/'source'/n)==pin,n
dest.mkdir();shutil.copytree(base/'source',dest/'source')
delta=[]
for n,data in SOURCES.items():
 p=dest/'source'/n
 if p.read_text()!=data:delta.append(n);p.write_text(data)
assert set(delta)=={'common/quick_buff.h','zone/aa.cpp'},delta
assert sha(dest/'source/zone/client.h')==proof['source_sha256']['zone/client.h']
work=base/'build/zone';link=shlex.split((work/'CMakeFiles/zone.dir/link.txt').read_text())
inputs={str((work/x).resolve()):sha((work/x).resolve()) for x in link if (work/x).is_file()}
def run(args):
 with (dest/'build.log').open('a') as log:subprocess.run(args,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
idx=link.index('-o')+1
original=link.copy();original[idx]=str(dest/'baseline-zone');run(original)
run(['strip','--strip-debug','-o',str(dest/'baseline-zone.stripped'),str(dest/'baseline-zone')])
assert sha(dest/'baseline-zone.stripped')==proof['shipping']['candidate-zone']
flags=(work/'CMakeFiles/zone.dir/flags.make').read_text()
opts=[]
for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):
 value=next(x.split(' = ',1)[1] for x in flags.splitlines() if x.startswith(key+' = '))
 opts+=shlex.split(value.replace(str(base/'source'),str(dest/'source')))
pch=dest/'cmake_pch.hxx';pch.write_text((work/'CMakeFiles/zone.dir/cmake_pch.hxx').read_text().replace(str(base/'source'),str(dest/'source')))
for name in ('aa.cpp','spells.cpp'):
 run(['/usr/bin/clang++',*opts,'-include',str(pch),'-MD','-MF',str(dest/(name+'.d')),'-c',str(dest/'source/zone'/name),'-o',str(dest/(name+'.o'))])
 link[link.index('CMakeFiles/zone.dir/'+name+'.o')]=str(dest/(name+'.o'))
link[idx]=str(dest/'candidate-zone');run(link)
shipping=dest/'candidate-zone.stripped';run(['strip','--strip-debug','-o',str(shipping),str(dest/'candidate-zone')])
assert all(sha(Path(n))==pin for n,pin in inputs.items()),'Retained link input mutated'
identity={'__name__':'identity'};exec(IDENTITY,identity)
loaded=identity['verify'](dest/'candidate-zone',shipping);assert loaded['status']=='PASS'
ldd=subprocess.check_output(['ldd',str(shipping)],text=True);assert 'not found' not in ldd
pins={n:sha(dest/'source'/n) for n in proof['source_sha256']}
result=dict(status='PASS',scope='Deployed full-build reproduction and two-TU metadata-only follow-up; Client layout unchanged',
 binary=str(shipping),shipping={'baseline-zone':proof['shipping']['candidate-zone'],'candidate-zone':sha(shipping)},
 source_delta=delta,source_sha256=pins,retained_link_inputs=inputs,runtime_identity=loaded,ldd=ldd)
(dest/'native-build.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','binary':str(shipping),'sha256':sha(shipping)}))
'''
if __name__=='__main__':
 OUT.mkdir(exist_ok=True)
 names=('common/quick_buff.h','zone/aa.cpp','zone/aa_quick_buff.inc','zone/client.h','zone/spells.cpp')
 sources={n:(ROOT/'server-mods/code'/n).read_text(encoding='utf-8') for n in names}
 prefix=f'SOURCES={sources!r}\nIDENTITY={(ROOT/"tools/elf_runtime_identity.py").read_text(encoding="utf-8")!r}\n'
 p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=1200)
 (OUT/'build.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print((p.stdout+p.stderr)[-5000:])
 if p.returncode:raise SystemExit(p.returncode)
 subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-quick-buff-hotkey-20261112-v2/native-build.json',str(OUT/'native-build.json')],check=True,capture_output=True)
