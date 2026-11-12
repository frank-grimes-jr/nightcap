"""Reproduce the live Quick Buff zone, then compile only the Imitate Death delta."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/releases/imitate-death-20261112/deployment'
REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
full=Path('/tmp/nightcap-quick-buff-full-20261112-v1')
base=Path('/tmp/nightcap-quick-buff-hotkey-20261112-v2')
dest=Path('/tmp/nightcap-imitate-death-20261112-v1')
proof=json.loads((base/'native-build.json').read_text())
assert proof['status']=='PASS' and not dest.exists()
assert proof['shipping']['candidate-zone']==LIVE_ZONE
for name,pin in proof['source_sha256'].items():assert sha(base/'source'/name)==pin,name
for name,pin in proof['retained_link_inputs'].items():assert sha(Path(name))==pin,name
assert sha(base/'candidate-zone.stripped')==LIVE_ZONE
assert (base/'source/zone/aa.cpp').read_text()==BASE_AA,'AA source differs from current Git baseline'
dest.mkdir();shutil.copytree(base/'source',dest/'source')
delta=[]
for name,data in SOURCES.items():
 p=dest/'source'/name
 assert not p.exists() or name=='zone/aa.cpp'
 if not p.exists() or p.read_text()!=data:delta.append(name);p.write_text(data)
assert set(delta)=={'zone/aa.cpp','common/imitate_death.h'}
work=full/'build/zone'
link=shlex.split((work/'CMakeFiles/zone.dir/link.txt').read_text())
for name in ('aa.cpp','spells.cpp'):
 link[link.index('CMakeFiles/zone.dir/'+name+'.o')]=str(base/(name+'.o'))
inputs={str((work/x).resolve()):sha((work/x).resolve()) for x in link if (work/x).is_file()}
idx=link.index('-o')+1
def run(args):
 with (dest/'build.log').open('a') as log:subprocess.run(args,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
baseline=link.copy();baseline[idx]=str(dest/'baseline-zone');run(baseline)
run(['strip','--strip-debug','-o',str(dest/'baseline-zone.stripped'),str(dest/'baseline-zone')])
assert sha(dest/'baseline-zone.stripped')==LIVE_ZONE,'Shipping predecessor must reproduce'
flags=(work/'CMakeFiles/zone.dir/flags.make').read_text();opts=[]
for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):
 value=next(x.split(' = ',1)[1] for x in flags.splitlines() if x.startswith(key+' = '))
 opts+=shlex.split(value.replace(str(full/'source'),str(dest/'source')))
pch=dest/'cmake_pch.hxx'
pch.write_text((work/'CMakeFiles/zone.dir/cmake_pch.hxx').read_text().replace(str(full/'source'),str(dest/'source')))
run(['/usr/bin/clang++',*opts,'-include',str(pch),'-MD','-MF',str(dest/'aa.cpp.d'),'-c',str(dest/'source/zone/aa.cpp'),'-o',str(dest/'aa.cpp.o')])
link[link.index(str(base/'aa.cpp.o'))]=str(dest/'aa.cpp.o');link[idx]=str(dest/'candidate-zone');run(link)
shipping=dest/'candidate-zone.stripped'
run(['strip','--strip-debug','-o',str(shipping),str(dest/'candidate-zone')])
assert all(sha(Path(n))==pin for n,pin in inputs.items()),'Retained link inputs changed'
identity={'__name__':'identity'};exec(IDENTITY,identity)
loaded=identity['verify'](dest/'candidate-zone',shipping);assert loaded['status']=='PASS'
ldd=subprocess.check_output(['ldd',str(shipping)],text=True);assert 'not found' not in ldd
pins={n:sha(dest/'source'/n) for n in set(proof['source_sha256'])|set(SOURCES)}
assert all(pins[n]==v for n,v in proof['source_sha256'].items() if n not in SOURCES)
dependencies=shlex.split((dest/'aa.cpp.d').read_text().replace('\\\n',' '))[1:]
deps={str(Path(n).resolve()):sha(Path(n)) for n in dependencies if Path(n).is_file()}
assert str(dest/'source/common/imitate_death.h') in deps
result=dict(status='PASS',scope='Deployed full-build reproduction and one-TU Imitate Death follow-up; Client layout unchanged',
 binary=str(shipping),shipping={'baseline-zone':LIVE_ZONE,'candidate-zone':sha(shipping)},
 source_delta=delta,source_sha256=pins,retained_link_inputs=inputs,compile_dependencies=deps,
 runtime_identity=loaded,ldd=ldd)
(dest/'native-build.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status='PASS',binary=str(shipping),sha256=sha(shipping),dependencies=len(deps))))
'''

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--finalize-existing',action='store_true');args=parser.parse_args()
    probe=json.loads((OUT/'production-probe.json').read_text(encoding='utf-8'))
    sources={n:(ROOT/'server-mods/code'/n).read_text(encoding='utf-8') for n in ('zone/aa.cpp','common/imitate_death.h')}
    baseline=subprocess.check_output(['git','show','423f9c3b:server-mods/code/zone/aa.cpp'],cwd=ROOT,text=True,encoding='utf-8')
    prefix=f'SOURCES={sources!r}\nBASE_AA={baseline!r}\nLIVE_ZONE={probe["image_files"]["bin/zone"]!r}\nIDENTITY={(ROOT/"tools/elf_runtime_identity.py").read_text(encoding="utf-8")!r}\n'
    code=REMOTE
    if args.finalize_existing:
        # A completed compile/link can be re-verified after a proof-only error.
        # Never rerun a live operator or modify retained build inputs.
        code=code.replace("assert proof['status']=='PASS' and not dest.exists()", "assert proof['status']=='PASS' and dest.is_dir() and not (dest/'native-build.json').exists()")
        code=code.replace("dest.mkdir();shutil.copytree(base/'source',dest/'source')", "assert all((dest/'source'/n).read_text()==v for n,v in SOURCES.items())")
        code=code.replace(" assert not p.exists() or name=='zone/aa.cpp'", " assert p.is_file()")
        code=code.replace(" if not p.exists() or p.read_text()!=data:delta.append(name);p.write_text(data)", " delta.append(name)")
        code=code.replace("with (dest/'build.log').open('a') as log:subprocess.run(args,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)", "assert (dest/'candidate-zone.stripped').is_file(), 'Completed compile/link required'")
        code=code.replace("pch.write_text((work/'CMakeFiles/zone.dir/cmake_pch.hxx').read_text().replace(str(full/'source'),str(dest/'source')))", "assert pch.read_text()==(work/'CMakeFiles/zone.dir/cmake_pch.hxx').read_text().replace(str(full/'source'),str(dest/'source'))")
    p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+code,text=True,encoding='utf-8',capture_output=True,timeout=1200)
    (OUT/('build-finalize.log' if args.finalize_existing else 'build.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');print((p.stdout+p.stderr)[-4000:])
    if p.returncode:raise SystemExit(p.returncode)
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-imitate-death-20261112-v1/native-build.json',str(OUT/'native-build.json')],check=True,capture_output=True)
