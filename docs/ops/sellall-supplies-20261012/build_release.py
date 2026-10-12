"""Compile two changed translation units and link against verified live objects."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import time

BASE=Path('/tmp/nightcap-item-upgrades-release-build-20261012')
INPUT=Path('/tmp/nightcap-sellall-input-20261012')
OUT=Path('/tmp/nightcap-sellall-build-20261012-v3')
CHANGED=['zone/command.cpp','zone/gm_commands/sell_all.cpp']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(json.dumps({'stage':name,'started':time.time()}),flush=True)
    with (OUT/(name+'.log')).open('w') as log:
        result=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print((OUT/(name+'.log')).read_text()[-6000:],flush=True)
        raise RuntimeError(name+' failed')
prior=json.loads((BASE/'manifest.json').read_text())
inputs=json.loads((INPUT/'input.json').read_text())
assert fingerprints(BASE/'source')==prior['source_files'],'Retained production source drift'
assert sha(BASE/'build/bin/zone')==prior['zone_sha256']==inputs['base_binaries']['zone']
assert all(sha(INPUT/n)==h for n,h in inputs['files'].items()),'Input drift'
assert all(sha(BASE/'source'/n)==inputs['base_source_files'][n] for n in CHANGED),'Git baseline differs from live source'
OUT.mkdir(exist_ok=False)
source=OUT/'source'
shutil.copytree(BASE/'source',source,ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
for n in CHANGED: shutil.copyfile(INPUT/n,source/n)
before=fingerprints(source)
assert set(before)==set(prior['source_files'])
assert sorted(n for n,h in before.items() if h!=prior['source_files'][n])==CHANGED
run('regressions',['python3',str(INPUT/'test_sell_all.py'),'--source',str(source/CHANGED[1]),
                   '--policy',str(source/'common/item_trade_policy.h')])
flags={}
for line in (BASE/'build/zone/CMakeFiles/gm_commands_zone.dir/flags.make').read_text().splitlines():
    if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
        key,value=line.split('=',1)
        flags[key.strip()]=shlex.split(value.replace(str(BASE/'source'),str(source)))
link=shlex.split((BASE/'build/zone/CMakeFiles/zone.dir/link.txt').read_text())
commands={}
units=sorted((BASE/'build/zone/CMakeFiles/gm_commands_zone.dir/Unity').glob('*.cxx'))
selected={}
for n in CHANGED:
    matches=[p for p in units if '"'+str(BASE/'source'/n)+'"' in p.read_text()]
    assert len(matches)==1,n
    selected[matches[0]]=None
archive=shlex.split((BASE/'build/zone/CMakeFiles/gm_commands_zone.dir/link.txt').read_text().splitlines()[0])
assert archive[:3]==['/usr/bin/ar','qc','libgm_commands_zone.a']
retained_inputs={str((BASE/'build/zone'/arg).resolve()):sha((BASE/'build/zone'/arg).resolve()) for arg in archive[3:]}
for unit in selected:
    generated=OUT/unit.name
    generated.write_text(unit.read_text().replace(str(BASE/'source'),str(source)))
    target=OUT/(unit.name+'.o')
    args=['/usr/bin/clang++']+flags['CXX_DEFINES']+flags['CXX_INCLUDES']+flags['CXX_FLAGS']+['-c',str(generated),'-o',str(target)]
    run('compile-'+unit.stem,args,BASE/'build')
    object_name=unit.relative_to(BASE/'build/zone').as_posix()+'.o'
    assert archive.count(object_name)==1
    archive[archive.index(object_name)]=str(target)
    commands[unit.name]=args
for i,arg in enumerate(archive[3:],3):
    archive[i]=str((BASE/'build/zone'/arg).resolve())
archive[2]=str(OUT/'libgm_commands_zone.a')
run('archive',archive,BASE/'build/zone')
run('ranlib',['/usr/bin/ranlib',archive[2]])
assert link.count('libgm_commands_zone.a')==1
link[link.index('libgm_commands_zone.a')]=archive[2]
index=link.index('-o')+1
assert (BASE/'build/zone'/link[index]).resolve()==BASE/'build/bin/zone'
link[index]=str(OUT/'zone')
link_inputs={str((BASE/'build/zone'/arg).resolve()):sha((BASE/'build/zone'/arg).resolve())
             for arg in link[1:] if arg.endswith(('.o','.a','.so')) and (BASE/'build/zone'/arg).is_file()}
run('link',link,BASE/'build/zone')
assert all(sha(Path(p))==h for p,h in link_inputs.items()),'Link input drift'
assert all(sha(Path(p))==h for p,h in retained_inputs.items()),'Retained unity objects drift'
assert fingerprints(BASE/'source')==prior['source_files'] and fingerprints(source)==before
assert sha(BASE/'build/bin/zone')==prior['zone_sha256']
assert (OUT/'zone').read_bytes()[:4]==b'\x7fELF'
run('ldd',['ldd',str(OUT/'zone')])
assert 'not found' not in (OUT/'ldd.log').read_text()
manifest={'status':'built_not_installed','source_commit':inputs['source_commit'],
          'base_manifest_sha256':sha(BASE/'manifest.json'),'source_files':before,
          'changed_source_files':CHANGED,'base_binaries':inputs['base_binaries'],
          'binaries':{**inputs['base_binaries'],'zone':sha(OUT/'zone')},
          'compile_commands':commands,'archive_command':archive,'link_command':link,
          'unchanged_link_inputs':link_inputs,'retained_unity_inputs':retained_inputs,
          'regressions':(OUT/'regressions.log').read_text().strip(),
          'world_rule_catalog_changed':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ('status','binaries','regressions','changed_source_files')}),flush=True)
