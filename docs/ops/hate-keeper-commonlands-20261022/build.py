"""Reproduce deployed zone, then replace only the Keeper implementation object."""
import hashlib,json,re,shlex,subprocess
from pathlib import Path
BASE=Path('/tmp/nightcap-thj-behaviors-v1')
PRIOR=Path('/tmp/nightcap-classic-rewards-with-handins-v1')
INPUT=Path('/tmp/nightcap-hate-keeper-input')
OUT=Path('/tmp/nightcap-hate-keeper-build-v1')
EXPECTED='8c9b97d53518442f74652518a06cfcfdf2202269ad95f065db57353bc000af31'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,name,cwd):
    print(name,flush=True)
    with (OUT/(name+'.log')).open('w') as f:subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
    prior=json.loads((PRIOR/'manifest.json').read_text())
    assert sha(PRIOR/'zone')==prior['zone_sha256']==EXPECTED
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'manifest.json').exists(),'Completed build is immutable'
    cwd=BASE/'build/zone';target=cwd/'CMakeFiles/zone.dir'
    link=shlex.split((target/'link.txt').read_text());pos=link.index('-o')+1
    replacements={'CMakeFiles/zone.dir/spells.cpp.o':Path('/tmp/nightcap-aa-pacing-million-v2/spells.cpp.o'),
      'CMakeFiles/zone.dir/npc.cpp.o':Path('/tmp/nightcap-quest-handins-build-v1/npc.cpp.o'),
      'CMakeFiles/zone.dir/task_client_state.cpp.o':Path('/tmp/nightcap-quest-handins-build-v1/task_client_state.cpp.o'),
      'CMakeFiles/zone.dir/dungeon_service.cpp.o':Path('/tmp/nightcap-classic-rewards-build-v2/dungeon_service.cpp.o'),
      'liblua_zone.a':Path('/tmp/nightcap-classic-rewards-build-v2/liblua_zone.a'),
      '../bin/libcommon.a':Path('/tmp/nightcap-classic-rewards-build-v2/libcommon.a')}
    for token,path in replacements.items():
        assert sha(path)==prior['combined_inputs'][str(path)]
        link[link.index(token)]=str(path)
    pins={str((cwd/v).resolve()):sha((cwd/v).resolve()) for v in link if not v.startswith('-') and (cwd/v).is_file() and v!=link[pos]}
    link[pos]=str(OUT/'baseline');run(link,'baseline-link',cwd)
    assert sha(OUT/'baseline')==EXPECTED,'Retained objects do not reproduce current production'
    sources={str(p.relative_to(INPUT)):sha(p) for p in INPUT.rglob('*') if p.is_file()}
    for dep in target.glob('cmake_pch*.d'):
        assert not any('/source/'+p in dep.read_text() for p in sources if p.endswith('.h'))
    flags=dict(re.findall(r'^(CXX_\w+) = (.*)$',(target/'flags.make').read_text(),re.M))
    args=['/usr/bin/clang++','-I'+str(INPUT),'-I'+str(INPUT/'zone'),'-I'+str(BASE/'source/zone')]
    for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):args+=shlex.split(flags[key])
    args+=['-Winvalid-pch','-Xclang','-include-pch','-Xclang',str(target/'cmake_pch.hxx.pch'),'-Xclang','-include','-Xclang',str(target/'cmake_pch.hxx'),'-o',str(OUT/'dungeon_service.cpp.o'),'-c',str(INPUT/'zone/dungeon_service.cpp')]
    run(args,'compile-keeper',cwd)
    link[link.index(str(replacements['CMakeFiles/zone.dir/dungeon_service.cpp.o']))]=str(OUT/'dungeon_service.cpp.o')
    link[pos]=str(OUT/'zone');run(link,'candidate-link',cwd)
    run(['ldd',str(OUT/'zone')],'ldd',cwd)
    assert 'not found' not in (OUT/'ldd.log').read_text()
    assert all(sha(Path(p))==h for p,h in pins.items())
    report={'baseline_zone_sha256':EXPECTED,'baseline_reproduced':True,'zone_sha256':sha(OUT/'zone'),'candidate_sources':sources,'retained_inputs':pins,'abi_changed':False,'production_changed':False}
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'baseline_reproduced':True,'zone_sha256':report['zone_sha256']}),flush=True)
if __name__=='__main__':main()
