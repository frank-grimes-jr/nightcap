"""Build report-only zone over the authenticated live augment inputs; never install."""
from pathlib import Path
import difflib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FILES = ('zone/command.cpp', 'zone/command.h', 'zone/gm_commands/nightcapui.cpp')
patch = ''
for name in FILES:
    before = subprocess.check_output(['git','show','8be13a1babcb45e8fd8339b9263d35bedcfc6271:server-mods/code/'+name],cwd=ROOT).decode().replace('\r\n','\n')
    after = (ROOT/'server-mods/code'/name).read_text(encoding='utf-8')
    patch += ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
assert patch
CODE = r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
aug=Path('/tmp/nightcap-augment-audit-20261106-v2')
dest=Path('/tmp/nightcap-augment-item-window-20261106-v4')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists()
pins=json.loads((aug/'link-inputs.json').read_text())
for name,pin in pins.items():assert sha(Path(name))==pin,name
evidence=json.loads((aug/'linked-evidence.json').read_text())
for unit in evidence['compiles']:assert sha(aug/(unit['unit']+'.o'))==unit['object_sha256']
dest.mkdir();shutil.copytree(aug/'source',dest/'source',symlinks=True)
pre={name:sha(dest/'source'/name) for name in FILES}
for name in FILES:
    path=dest/'source'/name;path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
p=subprocess.run(['patch','--batch','--fuzz=0','-p1'],input=PATCH,text=True,cwd=dest/'source',capture_output=True)
assert p.returncode==0,p.stdout+p.stderr
zone=old/'build/zone';args=shlex.split((zone/'CMakeFiles/zone.dir/link.txt').read_text())
for i,arg in enumerate(args):
    if arg.endswith(('.a','.o')) and not arg.startswith('/'):
        args[i]=str((zone/arg).resolve())
for unit in ('zone_hunt.cpp','bonuses.cpp','attack.cpp','dungeon_service.cpp'):
    matches=[i for i,arg in enumerate(args) if arg.endswith('/'+unit+'.o')]
    assert len(matches)==1,unit;args[matches[0]]=str(aug/(unit+'.o'))
def link(arguments,name):
    cmd=list(arguments);cmd[cmd.index('-o')+1]=str(dest/name)
    with (dest/(name+'.log')).open('x') as log:
        result=subprocess.run(cmd,cwd=zone,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0,(dest/(name+'.log')).read_text()[-1500:]
    subprocess.run(['strip','--strip-debug','-o',str(dest/(name+'.stripped')),str(dest/name)],check=True)
    return sha(dest/(name+'.stripped'))
baseline=link(args,'baseline-zone')
assert baseline=='bc88a4688d722c89f882ddb3328cf0d26867781fea49199ef681abe4f6c51892',baseline
def flags(target):
    result=[]
    for line in (zone/('CMakeFiles/'+target+'.dir/flags.make')).read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            result+=shlex.split(line.split('=',1)[1].replace(str(old/'source'),str(dest/'source')))
    return result
commands=[]
for number in (1,):
    name='unity_'+str(number)+'_cxx.cxx'
    source=(old/('build/zone/CMakeFiles/gm_commands_zone.dir/Unity/'+name)).read_text()
    assert '/zone/command.cpp"' in source and '/nightcapui.cpp"' in source
    (dest/name).write_text(source.replace(str(old/'source'),str(dest/'source')))
    commands.append((name,['/usr/bin/clang++']+flags('gm_commands_zone')+['-c',str(dest/name),'-o',str(dest/(name+'.o'))]))
compiled=[]
for name,cmd in commands:
    with (dest/(name+'.log')).open('x') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0,(dest/(name+'.log')).read_text()[-2500:]
    compiled.append(dict(unit=name,object_sha256=sha(dest/(name+'.o'))))
shutil.copy2(zone/'libgm_commands_zone.a',dest/'libgm_commands_zone.a')
subprocess.run(['ar','r',str(dest/'libgm_commands_zone.a'),str(dest/'unity_1_cxx.cxx.o')],check=True)
for suffix,replacement in [('/libgm_commands_zone.a',dest/'libgm_commands_zone.a')]:
    matches=[i for i,arg in enumerate(args) if arg.endswith(suffix)];assert len(matches)==1,suffix;args[matches[0]]=str(replacement)
candidate=link(args,'candidate-zone')
report=dict(status='PASS',source=str(dest/'source'),preimages=pre,afterimages={n:sha(dest/'source'/n) for n in FILES},baseline_zone=baseline,candidate_zone=candidate,link_inputs=len(pins),compiled=compiled,scope='report-only native build; no install or gameplay acceptance')
(dest/'evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
'''
if __name__ == '__main__':
    p = subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input='FILES='+repr(FILES)+'\nPATCH='+repr(patch)+'\n'+CODE,text=True,encoding='utf-8',capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr[-3000:] + p.stdout[-1000:])
    report=json.loads(p.stdout);(HERE/'native-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
