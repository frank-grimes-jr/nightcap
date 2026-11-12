"""Reproduce shipping native binaries, then rebuild only the icon fix units."""
import difflib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/items/augment-icons-20261112'
REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
prior=Path('/tmp/nightcap-last-lantern-20261107-v1')
dest=Path('/tmp/nightcap-augment-icons-20261112-v2')
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
full=Path('/tmp/nightcap-power-source-xp-20261103-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not dest.exists(),'Existing build attempt; inspect it, do not overwrite'
proof=json.loads((prior/'native-build.json').read_text())
assert proof['status']=='PASS'
for name in ('zone','world','shared_memory'):
 assert proof['shipping']['candidate-'+name]==EXPECTED['bin/'+name]
for name,pin in proof['source_sha256'].items():
 assert sha(prior/'source'/name)==pin,name
commands=json.loads((prior/'link-commands.json').read_text())
inputs={}
for name in ('zone','world','shared_memory'):
 c=commands['candidate-'+name];args=c['arguments'];output=args[args.index('-o')+1]
 for arg in args:
  p=Path(arg) if Path(arg).is_absolute() else Path(c['cwd'])/arg
  if arg!=output and p.is_file():inputs[str(p.resolve())]=sha(p)
dest.mkdir();shutil.copytree(prior/'source',dest/'source')
(dest/'retained-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
def run(command,cwd,label):
 with (dest/(label+'.log')).open('w') as log:r=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0,(label,(dest/(label+'.log')).read_text()[-1500:])
results={};linked={}
for name in ('zone','world','shared_memory'):
 c=commands['candidate-'+name];args=c['arguments'].copy();args[args.index('-o')+1]=str(dest/('baseline-'+name))
 run(args,c['cwd'],'baseline-'+name)
 subprocess.run(['strip','--strip-debug','-o',str(dest/('baseline-'+name+'.stripped')),str(dest/('baseline-'+name))],check=True)
 actual=sha(dest/('baseline-'+name+'.stripped'));assert actual==EXPECTED['bin/'+name],(name,actual)
 results['baseline-'+name]=actual
 print(json.dumps({'baseline_reproduced':name,'sha256':actual}),flush=True)
for name,patch in PATCHES.items():
 p=dest/'source'/name;before=sha(p)
 assert p.read_text()==SOURCES[name]['before'],name
 p.write_text(SOURCES[name]['after'])
 assert sha(p)!=before,name
archives={};compiles=[]
for label,base in (('zone',old),('world',full)):
 flags=(base/'build/common/CMakeFiles/common.dir/flags.make').read_text()
 parts=[next(l.split(' = ',1)[1] for l in flags.splitlines() if l.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
 folder=dest/label;folder.mkdir()
 args=['/usr/bin/clang++','-I'+str(dest/'source')]+shlex.split(' '.join(parts))+['-MMD','-MF',str(folder/'item_instance.d'),'-c',str(dest/'source/common/item_instance.cpp'),'-o',str(folder/'item_instance.cpp.o')]
 run(args,base/'build','compile-item-instance-'+label)
 archive=dest/('libcommon-'+label+'.a');shutil.copyfile(prior/('libcommon-'+label+'.a'),archive)
 members=subprocess.check_output(['ar','t',str(archive)],text=True).splitlines();assert members.count('item_instance.cpp.o')==1
 subprocess.run(['ar','r',str(archive),str(folder/'item_instance.cpp.o')],check=True)
 archives[label]=archive
 compiles.append({'label':label,'command':args,'object_sha256':sha(folder/'item_instance.cpp.o')})
 print(json.dumps({'compiled':'item_instance.cpp','consumer':label}),flush=True)
flags=(old/'build/zone/CMakeFiles/zone.dir/flags.make').read_text()
parts=[next(l.split(' = ',1)[1] for l in flags.splitlines() if l.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
pch=dest/'cmake_pch.hxx';pch.write_text((prior/'cmake_pch.hxx').read_text().replace(str(prior/'source'),str(dest/'source')))
args=['/usr/bin/clang++','-I'+str(dest/'source')]+shlex.split(' '.join(parts))+['-include',str(pch),'-MMD','-MF',str(dest/'client_packet.d'),'-c',str(dest/'source/zone/client_packet.cpp'),'-o',str(dest/'client_packet.cpp.o')]
run(args,old/'build','compile-client-packet')
compiles.append({'label':'zone-packet','command':args,'object_sha256':sha(dest/'client_packet.cpp.o')})
for name in ('zone','world','shared_memory'):
 c=commands['candidate-'+name];args=c['arguments'].copy();args[args.index('-o')+1]=str(dest/('candidate-'+name))
 common=[i for i,a in enumerate(args) if a.endswith('libcommon-zone.a') or a.endswith('libcommon-world.a')]
 assert len(common)==(2 if name=='zone' else 1)
 for index in common:args[index]=str(archives['zone' if name=='zone' else 'world'])
 if name=='zone':
  target='CMakeFiles/zone.dir/client_packet.cpp.o';assert args.count(target)==1
  args[args.index(target)]=str(dest/'client_packet.cpp.o')
 run(args,c['cwd'],'candidate-'+name)
 subprocess.run(['strip','--strip-debug','-o',str(dest/('candidate-'+name+'.stripped')),str(dest/('candidate-'+name))],check=True)
 results['candidate-'+name]=sha(dest/('candidate-'+name+'.stripped'));linked[name]={'cwd':c['cwd'],'arguments':args}
 print(json.dumps({'linked':name,'sha256':results['candidate-'+name]}),flush=True)
for name,pin in inputs.items():assert sha(Path(name))==pin,name
identity={'__name__':'identity'};exec(IDENTITY,identity)
identities={name:identity['verify'](dest/('candidate-'+name),dest/('candidate-'+name+'.stripped')) for name in ('zone','world','shared_memory')}
assert all(v['status']=='PASS' for v in identities.values())
report={'status':'PASS','shipping':results,'runtime_identity':identities,'compiles':compiles,
 'retained_inputs':inputs,'source_sha256':{name:sha(dest/'source'/name) for name in PATCHES},
 'scope':'Shipping baseline reproduction and isolated relink, not deployment or player acceptance'}
(dest/'link-commands.json').write_text(json.dumps(linked,indent=2)+'\n')
(dest/'native-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','shipping':results}),flush=True)
'''


if __name__ == '__main__':
    patches = {}
    sources = {}
    for name in ('common/item_instance.cpp', 'zone/client_packet.cpp'):
        path = 'server-mods/code/' + name
        before = subprocess.check_output(['git', 'show', 'b7e404b2:' + path], cwd=ROOT).decode('utf-8')
        before = before.replace('\r\n', '\n')
        after = (ROOT / path).read_text(encoding='utf-8')
        sources[name] = {'before': before, 'after': after}
        patches[name] = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                                   fromfile='a/' + name, tofile='b/' + name))
    expected = json.loads((ROOT / 'artifacts/augment-icons-20261112/production-probe.json').read_text())['image_files']
    prefix = 'SOURCES=' + repr(sources) + '\nPATCHES=' + repr(patches) + '\nEXPECTED=' + repr(expected) + '\nIDENTITY=' + repr((ROOT / 'tools/elf_runtime_identity.py').read_text()) + '\n'
    result = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                            input=prefix + REMOTE, text=True, encoding='utf-8', capture_output=True, timeout=1800)
    (OUT / 'native-build.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    print((result.stdout + result.stderr)[-2200:])
    if result.returncode:
        raise SystemExit(result.returncode)
    subprocess.run(['docker', 'cp', 'akk-stack-eqemu-server-1:/tmp/nightcap-augment-icons-20261112-v2/native-build.json',
                    str(OUT / 'native-build.json')], check=True, capture_output=True)
