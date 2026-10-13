"""Build in the local Linux container from retained production source/objects.

Never installs binaries or changes services. Input is a separately staged directory.
"""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012')
LIVE = Path('/tmp/nightcap-sellall-build-20261012-v3')
INPUT = Path('/tmp/nightcap-trainer-input-20261012')
OUT = Path('/tmp/nightcap-trainer-build-20261012-v2')
# Retain the concurrently promoted early-scribing change in client_process/effects.
CHANGED = ['zone/client.cpp', 'zone/client.h', 'zone/client_process.cpp', 'zone/effects.cpp']


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
    prior = json.loads((LIVE / 'manifest.json').read_text())
    expected = json.loads((INPUT / 'input.json').read_text())
    assert fingerprints(LIVE / 'source') == prior['source_files'], 'Retained source drift'
    assert sha(LIVE / 'zone') == prior['binaries']['zone'] == expected['live_zone_sha256']
    assert all(sha(INPUT / n) == h for n, h in expected['files'].items()), 'Input drift'
    for name in CHANGED:
        assert (LIVE / 'source' / name).read_text() == (INPUT / 'baseline' / name).read_text(), name
    # Only an additional nonvirtual method declaration; no Client layout/vtable change.
    before_header = (INPUT / 'baseline/zone/client.h').read_text()
    after_header = (INPUT / 'zone/client.h').read_text()
    assert after_header.replace('\tvoid CheckTrainerHail(NPC* trainer, const char* message);\n', '') == before_header
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
    link = list(prior['link_command'])
    retained = {str((BASE / 'build/zone' / arg).resolve()): sha((BASE / 'build/zone' / arg).resolve())
                for arg in link[1:] if arg.endswith(('.o', '.a', '.so')) and (BASE / 'build/zone' / arg).is_file()}
    assert retained == prior['unchanged_link_inputs'], 'Link inputs differ from the deployed build evidence'
    commands = {}
    for name in ['client.cpp', 'client_process.cpp', 'effects.cpp']:
        obj = OUT / (name + '.o')
        args = ['/usr/bin/clang++'] + flags['CXX_DEFINES'] + flags['CXX_INCLUDES'] + flags['CXX_FLAGS']
        args += ['-c', str(source / 'zone' / name), '-o', str(obj)]
        # No stale precompiled header: read the candidate declaration directly.
        run('compile-' + name, args, BASE / 'build')
        old = 'CMakeFiles/zone.dir/' + name + '.o'
        assert link.count(old) == 1
        link[link.index(old)] = str(obj)
        commands[name] = args
    link[link.index('-o') + 1] = str(OUT / 'zone')
    run('link', link, BASE / 'build/zone')
    assert all(sha(Path(p)) == h for p, h in retained.items()), 'Retained object drift'
    assert fingerprints(LIVE / 'source') == prior['source_files'] and fingerprints(source) == before
    assert sha(LIVE / 'zone') == expected['live_zone_sha256']
    run('ldd', ['ldd', str(OUT / 'zone')])
    assert 'not found' not in (OUT / 'ldd.log').read_text()
    manifest = {'status': 'built_not_installed', 'base_manifest_sha256': sha(LIVE / 'manifest.json'),
                'source_files': before, 'changed_source_files': CHANGED,
                'binaries': {**prior['binaries'], 'zone': sha(OUT / 'zone')},
                'compile_commands': commands, 'link_command': link,
                'unchanged_link_inputs': retained}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'binaries': manifest['binaries']}), flush=True)


if __name__ == '__main__':
    main()
