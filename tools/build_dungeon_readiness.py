"""Build/test the narrow Keeper contract fix against retained deployed objects; never install."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/dungeons/readiness-20261106'
REMOTE = r'''
import hashlib,json,pathlib,re,shlex,subprocess
Path=pathlib.Path
aug=Path('/tmp/nightcap-augment-audit-20261106-v2')
live=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
dest=Path('/tmp/nightcap-dungeon-readiness-20261106-v2')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normalized=lambda p:p.read_bytes().replace(b'\r\n',b'\n').decode()
evidence=json.loads((aug/'linked-evidence.json').read_text())
assert evidence['link']=='PASS'
assert sha(aug/'link-inputs.json')==evidence['link_manifest_sha256']
assert normalized(aug/'source/zone/dungeon_service.cpp')==SOURCE
old=(aug/'source/common/dungeon_contract.h').read_text()
assert sha(aug/'source/common/dungeon_contract.h')=='dfc7aadabc49f94c800070079ad5fa3a97d81ece107b6a59579b68ec318ffc81'
def contracts(header):
 result={}
 for section in ('SchemaChecks','ContentChecks'):
  block=header.split('inline constexpr ContractCheck '+section+'[] = {',1)[1].split('\n};',1)[0]
  result[section]={m[0]:(m[1],m[2]) for m in re.findall(r'\{"([^"]+)",R"NC\((.*?)\)NC","([^"]+)"\}',block)}
 return result
before,after=contracts(old),contracts(HEADER)
assert before['SchemaChecks']==after['SchemaChecks']
assert before['ContentChecks'].keys()==after['ContentChecks'].keys()
changed=[k for k in before['ContentChecks'] if before['ContentChecks'][k]!=after['ContentChecks'][k]]
assert set(changed)=={'vigil/items/0','compact/items/0'}
cases=lambda h:{int(k):v for k,v in re.findall(r'case (\d+): return ([^\n]+)',h)}
bc,ac=cases(old),cases(HEADER)
assert bc.keys()==ac.keys()
ids={int(r['after']['id']) for r in ROWS}
assert {k for k in bc if bc[k]!=ac[k]}==ids and len(ids)==8
dest.mkdir(exist_ok=False)
(dest/'source/common').mkdir(parents=True)
(dest/'source/common/dungeon_contract.h').write_text(HEADER)
(dest/'old/common').mkdir(parents=True)
(dest/'old/common/dungeon_contract.h').write_text(old)
flags=(live/'build/zone/CMakeFiles/zone.dir/flags.make').read_text()
parts={k:next(line.split(' = ',1)[1] for line in flags.splitlines() if line.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')}
base=['/usr/bin/clang++']+shlex.split(' '.join(parts.values()))
# Exercise actual EQ::ItemData and CacheMatches, starting with each unchanged
# native baseline item, then applying independently reviewed SQL afterimages.
fixture='#include "common/dungeon_contract.h"\n#include <cassert>\n#include <cstring>\nint main(){\n'
mapping={'icon':'Icon','healamt':'HealAmt','focuseffect':'Focus.Effect','focustype':'Focus.Type','focuslevel':'Focus.Level','focuslevel2':'Focus.Level2'}
negatives=0
for row in ROWS:
 item=int(row['before']['id']);guard=bc[item]
 fixture+='{ EQ::ItemData i{}; i.ID='+str(item)+';\n'
 for member,value in re.findall(r'std::strcmp\(i\.([^,]+),((?:"(?:\\.|[^"\\])*")+?)\)==0',guard):
  fixture+='std::strcpy(i.'+member+','+value+');\n'
 for member,value in re.findall(r'i\.([A-Za-z0-9_.\[\]]+)==(-?[0-9.]+)',guard):
  fixture+='i.'+member+'='+value+';\n'
 for field,value in row['after'].items():
  if value!=row['before'][field]:
   assert field in mapping,field
   fixture+='i.'+mapping[field]+'='+str(int(value))+';\n'
 fixture+='assert(NightcapDungeon::CacheMatches(i)==ACCEPT);\n'
 for member in ('Icon','HealAmt','Focus.Effect')+ (('Focus.Type','Focus.Level','Focus.Level2') if int(row['after']['focuseffect'])>0 else ()):
  fixture+='if(ACCEPT){auto bad=i;++bad.'+member+';assert(!NightcapDungeon::CacheMatches(bad));}\n'
  negatives+=1
 fixture+='}\n'
fixture+='}\n'
(dest/'cache_test.cpp').write_text(fixture)
def run(args,label):
 with (dest/(label+'.log')).open('x') as log:
  result=subprocess.run(args,cwd=live/'build/zone',stdout=log,stderr=subprocess.STDOUT)
 assert result.returncode==0,label+' failed; inspect '+str(dest/(label+'.log'))
for label,include,accept in [('cache-before',dest/'old',0),('cache-after',dest/'source',1)]:
 command=base[:1]+['-I'+str(include),'-I'+str(aug/'source')]+base[1:]+['-O0','-UNDEBUG','-DACCEPT='+str(accept),str(dest/'cache_test.cpp'),'-o',str(dest/label)]
 run(command,label+'-compile');run([str(dest/label)],label+'-run')
command=base[:1]+['-I'+str(dest/'source'),'-I'+str(aug/'source')]+base[1:]+['-include',str(aug/'cmake_pch.hxx'),'-c',str(aug/'source/zone/dungeon_service.cpp'),'-o',str(dest/'dungeon_service.cpp.o')]
run(command,'compile')
recipe=live/'build/zone/CMakeFiles/zone.dir/link.txt'
args=shlex.split(recipe.read_text());assert args[0]=='/usr/bin/clang++' and args.count('-o')==1
inputs=json.loads((aug/'link-inputs.json').read_text())
for path,pin in inputs.items():assert sha(Path(path))==pin,'Retained link input changed'
for unit in evidence['compiles']:
 assert sha(aug/(unit['unit']+'.o'))==unit['object_sha256']
 old_arg='CMakeFiles/zone.dir/'+unit['unit']+'.o';assert args.count(old_arg)==1
 args[args.index(old_arg)]=str(aug/(unit['unit']+'.o'))
for label,replace in [('baseline',False),('candidate',True)]:
 command=args.copy();command[command.index('-o')+1]=str(dest/(label+'-zone'))
 if replace:command[command.index(str(aug/'dungeon_service.cpp.o'))]=str(dest/'dungeon_service.cpp.o')
 run(command,label+'-link')
 run(['strip','--strip-debug','-o',str(dest/(label+'-zone.stripped')),str(dest/(label+'-zone'))],label+'-strip')
 if not replace:
  assert sha(dest/(label+'-zone'))==evidence['candidate']['unstripped_sha256']
  assert sha(dest/(label+'-zone.stripped'))=='bc88a4688d722c89f882ddb3328cf0d26867781fea49199ef681abe4f6c51892'
 identity={'__name__':'identity'};exec(IDENTITY,identity)
 assert identity['verify'](dest/(label+'-zone'),dest/(label+'-zone.stripped'))['status']=='PASS'
for path,pin in inputs.items():assert sha(Path(path))==pin
report={'status':'PASS','scope':'Local built candidate only; no installation, deployment or player acceptance',
 'retained_baseline_shipping_sha256':sha(dest/'baseline-zone.stripped'),'candidate_shipping_sha256':sha(dest/'candidate-zone.stripped'),
 'candidate_unstripped_sha256':sha(dest/'candidate-zone'),'contract_sha256':sha(dest/'source/common/dungeon_contract.h'),
 'changed_sql_checks':changed,'schema_checks':len(after['SchemaChecks']),'content_checks':len(after['ContentChecks']),
 'cache_afterimages_accepted':len(ids),'cache_before_rejections':len(ids),'cache_negative_mutations':negatives,
 'unchanged_native_cache_cases':len(bc)-len(ids),'recompiled_units':['zone/dungeon_service.cpp'],
 'retained_link_inputs':len(inputs),'link_inputs_sha256':sha(aug/'link-inputs.json'),'build_directory':str(dest)}
(dest/'evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
'''


def main():
    rows = json.loads((ROOT / 'docs/audits/augments-20261106/item-preimages.json').read_text())
    rows = [r for r in rows if r['zone'] in ('chapterhouse', 'kael')]
    inputs = dict(SOURCE=(ROOT / 'server-mods/code/zone/dungeon_service.cpp').read_text(),
                  HEADER=(ROOT / 'server-mods/code/common/dungeon_contract.h').read_text(), ROWS=rows,
                  IDENTITY=(ROOT / 'tools/elf_runtime_identity.py').read_text())
    prefix = ''.join(f'{k}={v!r}\n' for k, v in inputs.items())
    p = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                       input=prefix+REMOTE, text=True, encoding='utf-8', capture_output=True, timeout=900)
    if p.returncode:
        raise RuntimeError(p.stderr[-5000:])
    report = json.loads(p.stdout)
    (OUT / 'native-build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
