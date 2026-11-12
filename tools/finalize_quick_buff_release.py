"""Apply the independently reviewed instrument correction to the completed full build."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112'
REMOTE=r'''
from pathlib import Path
import hashlib,json,subprocess
dest=Path('/tmp/nightcap-quick-buff-full-20261112-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=Path('/tmp/nightcap-augment-icons-20261112-v2')
baseline=json.loads((base/'native-build.json').read_text());assert baseline['status']=='PASS'
pins=json.loads((dest/'source-before-build.json').read_text())
corrections=json.loads((dest/'source-corrections.json').read_text())
assert set(corrections['source_after'])=={'zone/command.h','zone/spells.cpp'}
expected={**pins,**corrections['source_after']}
assert sha(dest/'baseline-zone.stripped')==baseline['shipping']['candidate-zone']
assert not (dest/'instrument-correction.json').exists(),'Inspect previous correction; do not replay'
for name,pin in expected.items():assert sha(dest/'source'/name)==pin,name
header=(base/'source/zone/command.h').read_text()
anchor='void command_nightcapui(Client *c, const Seperator *sep);'
assert (dest/'source/zone/command.h').read_text()==header.replace(anchor,anchor+'\nvoid command_augstats(Client *c, const Seperator *sep);',1)
for name,data in SOURCES.items():
 p=dest/'source'/name
 assert p.read_text()==data,name
command=['cmake','--build',str(dest/'build'),'--target','zone','-j','3']
with (dest/'instrument-correction-build.log').open('w') as log:
 p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,(dest/'instrument-correction-build.log').read_text()[-5000:]
candidate=dest/'build/bin/zone';shipping=dest/'candidate-zone-final.stripped'
subprocess.run(['strip','--strip-debug','-o',str(shipping),str(candidate)],check=True)
identity={'__name__':'identity'};exec(IDENTITY,identity)
loaded=identity['verify'](candidate,shipping);assert loaded['status']=='PASS'
ldd=subprocess.check_output(['ldd',str(shipping)],text=True);assert 'not found' not in ldd
proof=dict(status='PASS',scope='Fresh full zone build including all zone/common/GM/Lua/Perl dependencies; no deployment',
 directory=str(dest),shipping={'baseline-zone':baseline['shipping']['candidate-zone'],'candidate-zone':sha(shipping)},
 runtime_identity=loaded,source_sha256=expected,compile_units=len(json.loads((dest/'build/compile_commands.json').read_text())),
 ldd=ldd,retained_source_corrections=corrections)
proof['instrument_correction']='Independent review: native instrument type checks for primary/secondary Bard, without pulses or component consumption'
proof['binary']=str(shipping)
assert all(sha(dest/'source'/n)==pin for n,pin in proof['source_sha256'].items())
(dest/'instrument-correction.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'status':'PASS','binary':str(shipping),'sha256':sha(shipping)}))
'''
if __name__=='__main__':
    names=('common/quick_buff.h','zone/aa_quick_buff.inc','zone/aa.cpp','zone/client.h','zone/spells.cpp')
    sources={n:(ROOT/'server-mods/code'/n).read_text(encoding='utf-8') for n in names}
    prefix=f'SOURCES={sources!r}\nIDENTITY={(ROOT/"tools/elf_runtime_identity.py").read_text(encoding="utf-8")!r}\n'
    r=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+REMOTE,
        text=True,encoding='utf-8',capture_output=True,timeout=1800)
    (OUT/'final-build.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');print((r.stdout+r.stderr)[-6000:])
    if r.returncode:raise SystemExit(r.returncode)
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-quick-buff-full-20261112-v1/instrument-correction.json',str(OUT/'full-build.json')],check=True,capture_output=True)
