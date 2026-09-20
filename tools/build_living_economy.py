"""Container-only isolated full world/zone build; never installs live binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--overlay', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    base = Path('/home/eqemu/code')
    out = a.output.resolve()
    if out.parent != Path('/tmp') or not out.name.startswith('nightcap-market-'):
        raise ValueError('Build must be in an isolated /tmp/nightcap-market-* directory')
    source = out/'source'
    if not source.exists():
        shutil.copytree(base, source, ignore=shutil.ignore_patterns('.git','build','build-tests','vcpkg'))
    for path in a.overlay.rglob('*'):
        if path.is_file():
            target = source/path.relative_to(a.overlay)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    build = out/'build'
    flags = ['-DCMAKE_BUILD_TYPE=RelWithDebInfo', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
             '-DCMAKE_C_COMPILER=/usr/bin/clang', '-DVCPKG_MANIFEST_INSTALL=OFF', '-DVCPKG_MANIFEST_MODE=OFF',
             '-DCMAKE_TOOLCHAIN_FILE='+str(base/'submodules/vcpkg/scripts/buildsystems/vcpkg.cmake'),
             '-DVCPKG_INSTALLED_DIR='+str(base/'build/vcpkg_installed')]
    for line in Path('/home/eqemu/build-local/CMakeCache.txt').read_text().splitlines():
        if line.startswith('EQEMU_') and (':BOOL=' in line or ':STRING=' in line):
            key, value = line.split('=', 1)
            flags.append('-D'+key.split(':')[0]+'='+value)
    for name, command in [('configure', ['cmake','-S',str(source),'-B',str(build),*flags]),
                          ('build', ['cmake','--build',str(build),'--target','world','zone','-j','4'])]:
        log = out/(name+'.log')
        with log.open('w') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            lines=log.read_text().splitlines()
            print('\n'.join(line for line in lines if 'error:' in line.lower() or 'fatal error' in line.lower()))
            print('\n'.join(lines[-30:]))
            raise RuntimeError(f'{name} failed; full evidence: {log}')
    files = {str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest()
             for f in source.rglob('*') if f.is_file() and 'vcpkg' not in f.relative_to(source).parts}
    outputs = {name:hashlib.sha256((build/'bin'/name).read_bytes()).hexdigest() for name in ('world','zone')}
    (out/'manifest.json').write_text(json.dumps({'source_files':files,'binaries':outputs},indent=2)+'\n')
    print(json.dumps({'status':'built_not_installed','binaries':outputs}))


if __name__ == '__main__': main()
