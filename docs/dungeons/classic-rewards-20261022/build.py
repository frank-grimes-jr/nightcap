"""Build the candidate from reproduced current objects; never install it."""
import hashlib
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

BASE=Path('/tmp/nightcap-thj-behaviors-v1')
AA=Path('/tmp/nightcap-aa-pacing-million-v2')
INPUT=Path('/tmp/nightcap-classic-rewards-input')
OUT=Path('/tmp/nightcap-classic-rewards-build-v2')
REUSE_LUA=Path('/tmp/nightcap-classic-rewards-no-reuse')
EXPECTED='5dd5a6558c837ff2e4724edcd12afcabd2e846379a9ca7b8a6e57e7715600f7b'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run(args,name,cwd):
    print(name,flush=True)
    with (OUT/(name+'.log')).open('w') as f:
        result=subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError((OUT/(name+'.log')).read_text()[-7000:])

def main():
    OUT.mkdir(exist_ok=False)
    expected=json.loads((INPUT/'input-manifest.json').read_text())
    for path,digest in expected['baseline_sources'].items():
        assert sha(BASE/'source'/path)==digest,path+' baseline drift'
    for path,digest in expected['candidate_sources'].items():
        assert sha(INPUT/path)==digest,path+' candidate drift'
    assert sha(AA/'zone')==EXPECTED
    cwd=BASE/'build/zone';target=cwd/'CMakeFiles/zone.dir'
    link=shlex.split((target/'link.txt').read_text());output=link.index('-o')+1
    link[link.index('CMakeFiles/zone.dir/spells.cpp.o')]=str(AA/'spells.cpp.o')
    inputs={str((cwd/x).resolve()):sha((cwd/x).resolve()) for x in link
        if not x.startswith('-') and x!=link[output] and (cwd/x).is_file()}
    original=list(link);original[output]=str(OUT/'zone-baseline')
    run(original,'baseline-link',cwd);assert sha(OUT/'zone-baseline')==EXPECTED
    flags=dict(re.findall(r'^(CXX_\w+) = (.*)$',(target/'flags.make').read_text(),re.M))
    # These implementation changes do not modify ItemData, rules or any ABI.
    # No changed header may have been cached inside the retained precompiled header.
    dependency=(target/'cmake_pch.hxx.gch.d')
    candidates=list(target.glob('cmake_pch*.d'))
    for dep in candidates:
        text=dep.read_text()
        assert not any('/source/'+p in text for p in expected['candidate_sources'] if p.endswith('.h')),dep
    for name in ('dungeon_service.cpp',):
        args=['/usr/bin/clang++','-I'+str(INPUT),'-I'+str(INPUT/'zone'),'-I'+str(BASE/'source/zone')]
        for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):args+=shlex.split(flags[key])
        args+=['-Winvalid-pch','-Xclang','-include-pch','-Xclang',str(target/'cmake_pch.hxx.pch'),
               '-Xclang','-include','-Xclang',str(target/'cmake_pch.hxx'),'-o',str(OUT/(name+'.o')),'-c',str(INPUT/'zone'/name)]
        run(args,'compile-'+name,cwd)
        link[link.index('CMakeFiles/zone.dir/'+name+'.o')]=str(OUT/(name+'.o'))
    # Lua is a separate static archive built from unity translation units.
    # Rebuild its original unit and replace that member in a private copy.
    lua_target=cwd/'CMakeFiles/lua_zone.dir'
    unity=next(p for p in (lua_target/'Unity').glob('*.cxx') if 'lua_general.cpp' in p.read_text())
    unity_text=unity.read_text()
    for source in re.findall(r'#include "([^"]+)"',unity_text):
        inputs[source]=sha(Path(source))
    candidate_unity=OUT/unity.name
    candidate_unity.write_text(unity_text.replace(str(BASE/'source/zone/lua_general.cpp'),str(INPUT/'zone/lua_general.cpp')))
    lua_flags=dict(re.findall(r'^(CXX_\w+) = (.*)$',(lua_target/'flags.make').read_text(),re.M))
    args=['/usr/bin/clang++','-I'+str(INPUT),'-I'+str(INPUT/'zone'),'-I'+str(BASE/'source/zone')]
    for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):args+=shlex.split(lua_flags[key])
    lua_object=OUT/(unity.name+'.o')
    args+=['-o',str(lua_object),'-c',str(candidate_unity)]
    archive=OUT/'liblua_zone.a'
    reused=False
    if (REUSE_LUA/'manifest.json').exists():
        previous=json.loads((REUSE_LUA/'manifest.json').read_text())
        assert previous['baseline_zone_sha256']==EXPECTED and previous['retained_inputs_unchanged']
        for path,digest in expected['candidate_sources'].items():
            if path not in ('zone/dungeon_service.cpp','common/dungeon_contract.h'):
                assert previous['candidate_sources'][path]==digest,'Lua input changed: '+path
        # Reuse only after proving the changed content contract is not included
        # in the Lua unity translation unit. Other candidate inputs match exactly.
        dependency_args=args[:args.index('-o')]+['-MM','-MF',str(OUT/'lua-dependencies.d'),str(candidate_unity)]
        run(dependency_args,'lua-dependencies',cwd)
        assert 'dungeon_contract.h' not in (OUT/'lua-dependencies.d').read_text()
        shutil.copyfile(REUSE_LUA/'liblua_zone.a',archive);reused=True
    else:
        run(args,'compile-lua-unity',cwd)
        shutil.copyfile(cwd/'liblua_zone.a',archive)
        run(['/usr/bin/ar','r',str(archive),str(lua_object)],'lua-archive',cwd)
        run(['/usr/bin/ranlib',str(archive)],'lua-index',cwd)
    link[link.index('liblua_zone.a')]=str(archive)
    common_cwd=BASE/'build/common';common_target=common_cwd/'CMakeFiles/common.dir'
    for dep in common_target.glob('cmake_pch*.d'):
        assert not any('/source/'+p in dep.read_text() for p in expected['candidate_sources'] if p.endswith('.h'))
    common_flags=dict(re.findall(r'^(CXX_\w+) = (.*)$',(common_target/'flags.make').read_text(),re.M))
    common_args=['/usr/bin/clang++','-I'+str(INPUT),'-I'+str(BASE/'source/common')]
    for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS'):common_args+=shlex.split(common_flags[key])
    common_args+=['-Winvalid-pch','-Xclang','-include-pch','-Xclang',str(common_target/'cmake_pch.hxx.pch'),
                  '-Xclang','-include','-Xclang',str(common_target/'cmake_pch.hxx'),
                  '-o',str(OUT/'shareddb.cpp.o'),'-c',str(INPUT/'common/shareddb.cpp')]
    run(common_args,'compile-shareddb',common_cwd)
    common_archive=OUT/'libcommon.a';shutil.copyfile(BASE/'build/bin/libcommon.a',common_archive)
    run(['/usr/bin/ar','r',str(common_archive),str(OUT/'shareddb.cpp.o')],'common-archive',common_cwd)
    run(['/usr/bin/ranlib',str(common_archive)],'common-index',common_cwd)
    link[link.index('../bin/libcommon.a')]=str(common_archive)
    link[output]=str(OUT/'zone');run(link,'candidate-link',cwd)
    binary_hashes={}
    for binary,baseline_hash in [('world','0b321c9fba510a42381abe5c167d6db94c02cf913dd50a86d6105b68dbd37b95'),('shared_memory','6d71c7e72c4a10f9d5eeb753ff29a3d589151ce1c81a32a7f564dec9c9fd967c')]:
        directory=BASE/'build'/binary
        command=shlex.split((directory/'CMakeFiles'/(binary+'.dir')/'link.txt').read_text())
        for value in command:
            path=(directory/value).resolve()
            if not value.startswith('-') and path.is_file():inputs[str(path)]=sha(path)
        pos=command.index('-o')+1;command[pos]=str(OUT/(binary+'-baseline'))
        run(command,binary+'-baseline-link',directory)
        assert sha(OUT/(binary+'-baseline'))==baseline_hash
        command[command.index('../bin/libcommon.a')]=str(common_archive);command[pos]=str(OUT/binary)
        run(command,binary+'-candidate-link',directory)
        run(['ldd',str(OUT/binary)],binary+'-ldd',directory)
        assert 'not found' not in (OUT/(binary+'-ldd.log')).read_text()
        binary_hashes[binary]={'baseline':baseline_hash,'candidate':sha(OUT/binary)}
    run(['ldd',str(OUT/'zone')],'ldd',cwd)
    assert 'not found' not in (OUT/'ldd.log').read_text()
    assert all(sha(Path(p))==h for p,h in inputs.items())
    evidence={'status':'built_not_installed','baseline_zone_sha256':EXPECTED,
        'baseline_reproduced':True,'zone_sha256':sha(OUT/'zone'),
        'candidate_sources':expected['candidate_sources'],'retained_inputs_unchanged':True,
        'lua_archive_sha256':sha(archive),'reused_lua_archive_from':str(REUSE_LUA) if reused else None,
        'other_binaries':binary_hashes,'common_archive_sha256':sha(common_archive),'abi_changed':False,'production_changed':False,'owner_gameplay_accepted':False}
    (OUT/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence),flush=True)

if __name__=='__main__':main()
