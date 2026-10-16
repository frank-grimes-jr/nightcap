"""Compile an isolated dungeon candidate, never install or restart a server.

Run inside the local build container after preparing a fresh retained source
copy and overlay. Every input byte is recorded before and after compilation.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('/tmp/nightcap-dungeon-build-20261016')
BASE=Path('/tmp/nightcap-aa-temporary-buffs-build-20261015')

def fingerprint(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}

def run(args,log):
    with (ROOT/log).open('w') as out:
        r=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT)
    if r.returncode:
        print((ROOT/log).read_text()[-16000:],flush=True)
        raise SystemExit(r.returncode)

def main():
    source=ROOT/'source'
    baseline=json.loads((BASE/'manifest.json').read_text())
    assert fingerprint(BASE/'source')==baseline['source_files'], 'Retained AA source drift'
    # Main omits the retained AA class/rank projection. Carry its reviewed
    # implementation and declaration rather than regressing the deployed ABI.
    (source/'zone/aa.cpp').write_bytes((BASE/'source/zone/aa.cpp').read_bytes())
    p=source/'zone/client.h';text=p.read_text()
    if 'bool ReprojectEarnedAAs();' not in text:
        assert text.count('void RefreshNightcapUI();')==1
        text=text.replace('void RefreshNightcapUI();','void RefreshNightcapUI();\n\tbool ReprojectEarnedAAs();')
        p.write_text(text)
    before=fingerprint(source)
    (ROOT/'input-sources.json').write_text(json.dumps(before,indent=2)+'\n')
    build=ROOT/'build'
    run(['cmake','-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
         '-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
         '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
         '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
         '-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],'configure.log')
    print('Configured isolated dungeon build.',flush=True)
    run(['cmake','--build',str(build),'--target','zone','world','shared_memory','-j2'],'build.log')
    assert fingerprint(source)==before, 'Source changed during compilation'
    binaries={}
    for name in ('zone','world','shared_memory'):
        p=build/'bin'/name
        run(['ldd',str(p)],'ldd-'+name+'.log')
        assert 'not found' not in (ROOT/('ldd-'+name+'.log')).read_text()
        binaries[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT/'manifest.json').write_text(json.dumps(dict(status='built_not_installed',source_files=before,
        retained_base_manifest_sha256=hashlib.sha256((BASE/'manifest.json').read_bytes()).hexdigest(),
        binaries=binaries,manual_gameplay_accepted=False),indent=2)+'\n')
    print(json.dumps(binaries),flush=True)

if __name__=='__main__':main()
