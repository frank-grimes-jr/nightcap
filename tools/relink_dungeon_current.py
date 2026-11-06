"""Preserve the newer deployed augment-report archive in the Keeper candidate; never install."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/dungeons/readiness-20261106'
REMOTE = r'''
from pathlib import Path
import difflib,hashlib,json,shlex,subprocess
aug=Path('/tmp/nightcap-augment-audit-20261106-v2')
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
current=Path('/tmp/nightcap-augment-item-window-20261106-v4')
candidate=Path('/tmp/nightcap-dungeon-readiness-20261106-v2')
dest=Path('/tmp/nightcap-dungeon-readiness-current-20261106-v1')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((candidate/'evidence.json').read_text());assert prior['status']=='PASS'
assert sha(candidate/'source/common/dungeon_contract.h')==HEADER_SHA
assert sha(candidate/'candidate-zone.stripped')==prior['candidate_shipping_sha256']
evidence=json.loads((current/'evidence.json').read_text());assert evidence['status']=='PASS'
assert evidence['candidate_zone']=='3fc2b901c98dfc2816298a051f3462a6db0a724ccfa649ff213da3d840186588'
for name,pin in evidence['afterimages'].items():
 assert sha(current/'source'/name)==pin
 actual=(current/'source'/name).read_bytes().replace(b'\r\n',b'\n').decode()
 assert actual==SOURCES[name],name+'\n'+''.join(difflib.unified_diff(SOURCES[name].splitlines(True),actual.splitlines(True)))[:2000]
archive=current/'libgm_commands_zone.a';base_archive=old/'build/zone/libgm_commands_zone.a'
members=lambda p:subprocess.check_output(['ar','t',str(p)],text=True).splitlines()
assert members(archive)==members(base_archive) and len(members(archive))==12
changed=[]
for name in members(archive):
 before=subprocess.check_output(['ar','p',str(base_archive),name]);after=subprocess.check_output(['ar','p',str(archive),name])
 if before!=after:
  changed.append(name);assert hashlib.sha256(after).hexdigest()==evidence['compiled'][0]['object_sha256']
assert changed==['unity_1_cxx.cxx.o']
pins=json.loads((aug/'link-inputs.json').read_text())
assert sha(aug/'link-inputs.json')==prior['link_inputs_sha256']
for name,pin in pins.items():assert sha(Path(name))==pin
augmentation=json.loads((aug/'linked-evidence.json').read_text())
for unit in augmentation['compiles']:assert sha(aug/(unit['unit']+'.o'))==unit['object_sha256']
dest.mkdir(exist_ok=False)
zone=old/'build/zone';args=shlex.split((zone/'CMakeFiles/zone.dir/link.txt').read_text())
for unit in augmentation['compiles']:
 name='CMakeFiles/zone.dir/'+unit['unit']+'.o';assert args.count(name)==1;args[args.index(name)]=str(aug/(unit['unit']+'.o'))
indices=[i for i,a in enumerate(args) if a.endswith('libgm_commands_zone.a')];assert len(indices)==1
args[indices[0]]=str(archive)
for label,replace in [('baseline',False),('candidate',True)]:
 command=args.copy();command[command.index('-o')+1]=str(dest/(label+'-zone'))
 if replace:command[command.index(str(aug/'dungeon_service.cpp.o'))]=str(candidate/'dungeon_service.cpp.o')
 with (dest/(label+'-link.log')).open('x') as log:result=subprocess.run(command,cwd=zone,stdout=log,stderr=subprocess.STDOUT)
 assert result.returncode==0,label+' link failed'
 subprocess.run(['strip','--strip-debug','-o',str(dest/(label+'-zone.stripped')),str(dest/(label+'-zone'))],check=True)
 if not replace:
  assert sha(dest/(label+'-zone'))==sha(current/'candidate-zone')
  assert sha(dest/(label+'-zone.stripped'))==evidence['candidate_zone']
 identity={'__name__':'identity'};exec(IDENTITY,identity)
 assert identity['verify'](dest/(label+'-zone'),dest/(label+'-zone.stripped'))['status']=='PASS'
for name,pin in pins.items():assert sha(Path(name))==pin
report={**prior,'retained_baseline_shipping_sha256':sha(dest/'baseline-zone.stripped'),
 'candidate_shipping_sha256':sha(dest/'candidate-zone.stripped'),'candidate_unstripped_sha256':sha(dest/'candidate-zone'),
 'build_directory':str(dest),'dungeon_object_sha256':sha(candidate/'dungeon_service.cpp.o'),
 'preserved_command_archive_sha256':sha(archive),'preserved_command_members':12,
 'preserved_command_source_sha256':evidence['afterimages'],
 'reviewed_mirror_difference':'command.h only: itemxp/factions prototype order; exact retained order is preserved',
 'scope':'Local Keeper candidate preserves the latest deployed augment Description/report release; no install, restart or player acceptance'}
(dest/'evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
'''

if __name__ == '__main__':
    names = ('zone/command.cpp', 'zone/command.h', 'zone/gm_commands/nightcapui.cpp')
    import hashlib
    sources = {n: (ROOT / 'server-mods/code' / n).read_text(encoding='utf-8') for n in names}
    # Inspected retained/main diff: declaration order only, no signature change.
    declarations = 'void command_factions(Client *c, const Seperator *sep);\nvoid command_itemxp(Client *c, const Seperator *sep);'
    retained = 'void command_itemxp(Client *c, const Seperator *sep);\nvoid command_factions(Client *c, const Seperator *sep);'
    assert sources['zone/command.h'].count(declarations)==1
    sources['zone/command.h'] = sources['zone/command.h'].replace(declarations,retained)
    inputs = dict(SOURCES=sources,
                  HEADER_SHA=hashlib.sha256((ROOT / 'server-mods/code/common/dungeon_contract.h').read_bytes()).hexdigest(),
                  IDENTITY=(ROOT / 'tools/elf_runtime_identity.py').read_text())
    prefix = ''.join(f'{k}={v!r}\n' for k, v in inputs.items())
    p = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                       input=prefix+REMOTE, text=True, encoding='utf-8', capture_output=True, timeout=600)
    if p.returncode:
        raise RuntimeError(p.stderr[-3000:])
    report = json.loads(p.stdout)
    (OUT / 'native-build-current.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
