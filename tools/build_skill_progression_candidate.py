"""Rebuild every zone TU after replacing the deployed inline primary skill cap.

Only reads retained production inputs and writes an isolated candidate directory.
No installation, database mutation, or service restart is performed here.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012')
LIVE = Path('/tmp/nightcap-trainer-build-20261012-v2')
INPUT = Path('/tmp/nightcap-skills-input-20261013')
OUT = Path('/tmp/nightcap-skills-build-20261013-v2')
CHANGED = ['zone/client.cpp', 'zone/client.h', 'zone/mob.cpp']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def run(name, args, cwd=None):
    print(name, flush=True)
    with (OUT / (name + '.log')).open('w') as log:
        result = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((OUT / (name + '.log')).read_text()[-7000:], flush=True)
        raise RuntimeError(name + ' failed')


def main():
    expected = json.loads((INPUT / 'input.json').read_text())
    assert sha(LIVE / 'manifest.json') == expected['live_manifest_sha256']
    prior = json.loads((LIVE / 'manifest.json').read_text())
    assert fingerprints(LIVE / 'source') == prior['source_files'], 'Retained source drift'
    assert sha(LIVE / 'zone') == prior['binaries']['zone'] == expected['live_zone_sha256']
    assert all(sha(INPUT / n) == h for n, h in expected['files'].items()), 'Input drift'
    for name, digest in prior['unchanged_link_inputs'].items():
        assert sha(Path(name)) == digest, 'Prior retained input drift: ' + name
    link = list(prior['link_command'])
    retained = {str((BASE / 'build/zone' / arg).resolve()): sha((BASE / 'build/zone' / arg).resolve())
                for arg in link[1:] if arg.endswith(('.o', '.a', '.so'))}
    assert retained == expected['link_inputs'], 'Current link input drift'
    OUT.mkdir(exist_ok=False)
    source = OUT / 'source'
    shutil.copytree(LIVE / 'source', source)
    for name in CHANGED:
        shutil.copyfile(INPUT / name, source / name)
    before = fingerprints(source)
    assert sorted(n for n, h in before.items() if h != prior['source_files'][n]) == CHANGED
    assert set(before) == set(prior['source_files'])
    flags = {}
    for line in (BASE / 'build/zone/CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key, value = line.split('=', 1)
            flags[key.strip()] = shlex.split(value.replace(str(BASE / 'source'), str(source)))
    # Several TUs depend on declarations provided by CMake's PCH includes.
    # Regenerate it against candidate headers; never reuse the retained PCH.
    pch = OUT / 'cmake_pch.hxx'
    pch.write_text((BASE / 'build/zone/CMakeFiles/zone.dir/cmake_pch.hxx').read_text()
                   .replace(str(BASE / 'source'), str(source)))
    compiler = ['/usr/bin/clang++'] + flags['CXX_DEFINES'] + flags['CXX_INCLUDES'] + flags['CXX_FLAGS']
    pch_command = compiler + ['-x', 'c++-header', str(pch), '-o', str(pch) + '.pch']
    run('compile-pch', pch_command, BASE / 'build')
    commands = {}
    for index, arg in enumerate(link):
        if not arg.endswith('.o'):
            continue
        # Every object in the retained link is a zone TU, including CLI/sidecar.
        name = arg.removeprefix('CMakeFiles/zone.dir/') if not Path(arg).is_absolute() else Path(arg).name
        assert name.endswith('.cpp.o') and '..' not in Path(name).parts
        cpp = name[:-2]
        assert (source / 'zone' / cpp).is_file(), cpp
        obj = OUT / 'objects' / name
        obj.parent.mkdir(parents=True, exist_ok=True)
        args = compiler + ['-include-pch', str(pch) + '.pch']
        args += ['-c', str(source / 'zone' / cpp), '-o', str(obj)]
        assert cpp not in commands
        commands[cpp] = args
        link[index] = str(obj)
    assert len(commands) == 126, 'Unexpected zone link topology'
    # No reused zone objects or stale PCH: all callers see the new declaration.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(run, 'compile-' + name.replace('/', '_'), args, BASE / 'build')
                for name, args in commands.items()]
        try:
            for job in as_completed(jobs):
                job.result()
        except BaseException:
            for job in jobs:
                job.cancel()
            raise
    link[link.index('-o') + 1] = str(OUT / 'zone')
    run('link', link, BASE / 'build/zone')
    assert all(sha(Path(p)) == h for p, h in retained.items()), 'Retained input drift'
    assert fingerprints(LIVE / 'source') == prior['source_files'] and fingerprints(source) == before
    assert sha(LIVE / 'zone') == expected['live_zone_sha256']
    run('ldd', ['ldd', str(OUT / 'zone')])
    assert 'not found' not in (OUT / 'ldd.log').read_text()
    manifest = {'status': 'built_not_installed', 'base_manifest_sha256': sha(LIVE / 'manifest.json'),
                'source_files': before, 'changed_source_files': CHANGED,
                'binaries': {**prior['binaries'], 'zone': sha(OUT / 'zone')},
                'compile_commands': commands, 'pch_command': pch_command,
                'pch_sha256': sha(Path(str(pch) + '.pch')), 'link_command': link,
                'unchanged_link_inputs': retained,
                'candidate_objects': {name: sha(Path(args[-1])) for name, args in commands.items()}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'binaries': manifest['binaries']}), flush=True)


if __name__ == '__main__':
    main()
