"""Build the sole changed native consumer against immutable October18 inputs.

Run inside the local build container with INPUT pointing to the task's staged
header and reviewed aa.cpp. Never installs a binary or changes a running server.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

BASE=Path('/tmp/nightcap-thj-parity-v1')
OUT=Path('/tmp/nightcap-all-class-aa-20261019')
INPUT=Path(os.environ.get('NIGHTCAP_AA_BUILD_INPUT','/tmp/nightcap-all-class-aa-input'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(command,cwd):
    output=command[command.index('-o')+1]
    return {str((cwd/v).resolve()):sha(cwd/v) for v in command[1:]
            if not v.startswith('-') and v!=output and (cwd/v).is_file()}


def run(args,cwd,log):
    with log.open('w') as stream:
        subprocess.run(args,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,check=True)


def verify_baseline():
    manifest=json.loads((BASE/'manifest.json').read_text())
    cwd=BASE/'build/zone'
    command=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
    command[command.index('-o')+1]=str(OUT/'baseline-relink-zone')
    before=inputs(command,cwd)
    run(command,cwd,OUT/'baseline-relink.log')
    assert all(sha(Path(p))==value for p,value in before.items())
    actual=sha(OUT/'baseline-relink-zone')
    assert actual==manifest['zone_sha256'], 'Retained objects no longer reproduce deployed zone'
    result=dict(baseline_zone_sha256=actual,exact_relink=True,link_inputs=before)
    (OUT/'baseline-relink.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    manifest=json.loads((BASE/'manifest.json').read_text())
    assert all(sha(BASE/'source'/name)==value for name,value in manifest['source_files'].items())
    assert sha(INPUT/'aa.cpp')==sha(BASE/'source/zone/aa.cpp'), 'AA implementation drift'
    cwd=BASE/'build/zone'
    command=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
    before_inputs=inputs(command,cwd)
    OUT.mkdir(exist_ok=False)
    verify_baseline()
    shutil.copytree(BASE/'source',OUT/'source')
    shutil.copyfile(INPUT/'nightcap_aa_policy.h',OUT/'source/common/nightcap_aa_policy.h')
    flags={}
    for line in (cwd/'CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            key,value=line.split('=',1)
            flags[key.strip()]=shlex.split(value.replace(str(BASE/'source'),str(OUT/'source')))
    compile_command=['/usr/bin/clang++']+flags['CXX_DEFINES']+flags['CXX_INCLUDES']+flags['CXX_FLAGS']
    compile_command+=['-c',str(OUT/'source/zone/aa.cpp'),'-o',str(OUT/'aa.cpp.o')]
    print('Compiling AA consumer',flush=True)
    run(compile_command,cwd,OUT/'compile.log')
    matches=[i for i,v in enumerate(command) if v.endswith('/aa.cpp.o')]
    assert len(matches)==1
    command[matches[0]]=str(OUT/'aa.cpp.o')
    command[command.index('-o')+1]=str(OUT/'zone')
    print('Linking candidate zone',flush=True)
    run(command,cwd,OUT/'link.log')
    run(['ldd',str(OUT/'zone')],OUT,OUT/'ldd.log')
    assert 'not found' not in (OUT/'ldd.log').read_text()
    assert all(sha(Path(p))==value for p,value in before_inputs.items())
    assert all(sha(BASE/'source'/name)==value for name,value in manifest['source_files'].items())
    source_files={name:sha(OUT/'source'/name) for name in manifest['source_files']}
    assert [name for name,value in source_files.items() if manifest['source_files'][name]!=value]==['common/nightcap_aa_policy.h']
    result=dict(status='built_not_installed',baseline_manifest_sha256=sha(BASE/'manifest.json'),
        source_files=source_files,compile_command=compile_command,link_command=command,
        final_link_inputs=inputs(command,cwd),zone_sha256=sha(OUT/'zone'),
        world_sha256=manifest['world_sha256'],shared_memory_sha256=manifest['shared_memory_sha256'])
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','zone_sha256')}))


if __name__=='__main__':main()
