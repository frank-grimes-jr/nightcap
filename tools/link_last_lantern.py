"""Reproduce current shipping identities, then link the isolated campaign pair."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
full=Path('/tmp/nightcap-power-source-xp-20261103-v1')
aug=Path('/tmp/nightcap-augment-audit-20261106-v2')
ready=Path('/tmp/nightcap-dungeon-readiness-20261106-v2')
stats=Path('/tmp/nightcap-character-stats-window-20261106-v3')
dest=Path('/tmp/nightcap-last-lantern-20261107-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((aug/'link-inputs.json').read_text())
for p,pin in pins.items():assert sha(Path(p))==pin,p
augmented=json.loads((aug/'linked-evidence.json').read_text())
for unit in augmented['compiles']:assert sha(aug/(unit['unit']+'.o'))==unit['object_sha256']
baseline_pins={name:BASELINE['binaries'][name] for name in ('zone','world','shared_memory')}
archives={}
for label,base in [('zone',old),('world',full)]:
 archive=dest/('libcommon-'+label+'.a');shutil.copyfile(base/'build/bin/libcommon.a',archive)
 members=subprocess.check_output(['ar','t',str(archive)],text=True).splitlines()
 assert members.count('shareddb.cpp.o')==1
 subprocess.run(['ar','r',str(archive),str(dest/'shareddb.cpp.o')],check=True)
 archives[label]=archive
results={};commands={}
for name in ('zone','world','shared_memory'):
 cwd=(old if name=='zone' else full)/'build'/name
 args=shlex.split((cwd/f'CMakeFiles/{name}.dir/link.txt').read_text())
 if name=='zone':
  for unit in augmented['compiles']:
   original='CMakeFiles/zone.dir/'+unit['unit']+'.o';assert args.count(original)==1
   args[args.index(original)]=str(aug/(unit['unit']+'.o'))
  args[args.index(str(aug/'dungeon_service.cpp.o'))]=str(ready/'dungeon_service.cpp.o')
  which=[i for i,a in enumerate(args) if a.endswith('libgm_commands_zone.a')];assert len(which)==1
  args[which[0]]=str(stats/'libgm_commands_zone.a')
 for label in ('baseline','candidate'):
  command=args.copy();command[command.index('-o')+1]=str(dest/(label+'-'+name))
  if label=='candidate':
   common=[i for i,a in enumerate(command) if a.endswith('libcommon.a')];assert len(common)==(2 if name=='zone' else 1)
   for index in common:command[index]=str(archives['zone' if name=='zone' else 'world'])
   if name=='zone':
    for unit in ('dungeon_service.cpp','advanced_loot_inventory.cpp','pets.cpp','spawn2.cpp','attack.cpp','task_manager.cpp','task_client_state.cpp'):
     original=str(ready/'dungeon_service.cpp.o') if unit=='dungeon_service.cpp' else str(aug/'attack.cpp.o') if unit=='attack.cpp' else 'CMakeFiles/zone.dir/'+unit+'.o'
     assert command.count(original)==1,unit;command[command.index(original)]=str(dest/(unit+'.o'))
  with (dest/(label+'-'+name+'-link.log')).open('w') as log:
   r=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
  assert r.returncode==0,(label,name,(dest/(label+'-'+name+'-link.log')).read_text()[-1500:])
  subprocess.run(['strip','--strip-debug','-o',str(dest/(label+'-'+name+'.stripped')),str(dest/(label+'-'+name))],check=True)
  actual=sha(dest/(label+'-'+name+'.stripped'))
  if label=='baseline':assert actual==baseline_pins[name],(name,actual,baseline_pins[name])
  results[label+'-'+name]=actual
  commands[label+'-'+name]=dict(cwd=str(cwd),arguments=command)
  (dest/'link-commands.partial.json').write_text(json.dumps({'status':'partial link evidence; not deployable','commands':commands,'shipping':results},indent=2)+'\n')
  print(json.dumps({'linked':label+'-'+name,'shipping_sha256':actual}),flush=True)
for p,pin in pins.items():assert sha(Path(p))==pin,p
identity={'__name__':'identity'};exec(IDENTITY,identity)
identities={name:identity['verify'](dest/('candidate-'+name),dest/('candidate-'+name+'.stripped')) for name in ('zone','world','shared_memory')}
assert all(v['status']=='PASS' for v in identities.values())
sources={str(p.relative_to(dest/'source')):sha(p) for p in (dest/'source').rglob('*') if p.is_file() and p.suffix in ('.h','.cpp','.inc')}
report={'status':'PASS','shipping':results,'runtime_identity':identities,'source_sha256':sources,
 'common_archive_sha256':{name:sha(path) for name,path in archives.items()},'retained_link_inputs_sha256':sha(aug/'link-inputs.json'),
 'scope':'isolated native build and shipping identity; no deployment or player acceptance'}
(dest/'link-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(dest/'native-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','shipping':results}))
'''


if __name__=='__main__':
    prefix='IDENTITY='+repr((ROOT/'tools/elf_runtime_identity.py').read_text())+'\nBASELINE='+repr(json.loads((ROOT/'docs/adventure-journal/release-20261107/production-native-baseline.json').read_text()))+'\n'
    r=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=prefix+REMOTE,
                     text=True,encoding='utf-8',capture_output=True,timeout=1800)
    out=ROOT/'docs/adventure-journal/release-20261107'
    (out/'native-link.log').write_text(r.stdout+'\n'+r.stderr)
    print((r.stdout+r.stderr)[-3000:])
    if r.returncode:raise SystemExit(r.returncode)
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-last-lantern-20261107-v1/native-build.json',str(out/'native-build.json')],check=True,capture_output=True)
