"""Isolated AA zone build from retained production source and verified link inputs."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012')
LIVE = Path('/tmp/nightcap-trainer-build-20261012-v2')
INPUT = Path('/tmp/nightcap-aa-input-20261013-v2')
OUT = Path('/tmp/nightcap-aa-build-20261013-v2')
CHANGED = ['zone/aa.cpp', 'zone/client.h', 'zone/exp.cpp']
ADDED = ['common/nightcap_aa_policy.h']


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
    before_header = (INPUT / 'baseline/zone/client.h').read_text()
    assert (INPUT / 'zone/client.h').read_text().replace('\tbool ReprojectEarnedAAs();\n', '') == before_header
    OUT.mkdir(exist_ok=False)
    source = OUT / 'source'
    shutil.copytree(LIVE / 'source', source)
    for name in CHANGED + ADDED:
        shutil.copyfile(INPUT / name, source / name)
    before = fingerprints(source)
    assert sorted(n for n, h in before.items() if n in prior['source_files'] and h != prior['source_files'][n]) == CHANGED
    assert set(before) - set(prior['source_files']) == set(ADDED)
    assert not set(prior['source_files']) - set(before)
    flags = {}
    for line in (BASE / 'build/zone/CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key, value = line.split('=', 1)
            flags[key.strip()] = shlex.split(value.replace(str(BASE / 'source'), str(source)))
    link = list(prior['link_command'])
    retained = {str((BASE / 'build/zone' / arg).resolve()): sha((BASE / 'build/zone' / arg).resolve())
                for arg in link[1:] if arg.endswith(('.o', '.a', '.so')) and (BASE / 'build/zone' / arg).is_file()}
    # The previous builder recorded inherited objects before replacing its three
    # TUs. Recompile those three using their original source/flags and compare
    # object bytes; every other link input must match its recorded hash.
    for path, value in retained.items():
        if path in prior['unchanged_link_inputs']:
            assert prior['unchanged_link_inputs'][path] == value, path
        else:
            name = Path(path).name.removesuffix('.o')
            command = list(prior['compile_commands'][name])
            assert command[command.index('-o') + 1] == path
            command[command.index('-o') + 1] = str(OUT / ('verified-' + name + '.o'))
            verified = Path('/tmp/nightcap-aa-build-20261013') / ('verified-' + name + '.o')
            if verified.is_file() and sha(verified) == value:
                shutil.copyfile(verified, command[command.index('-o') + 1])
            else:
                run('verify-retained-' + name, command, BASE / 'build')
            assert sha(Path(command[command.index('-o') + 1])) == value, path
    commands = {}
    for name in ['aa.cpp', 'exp.cpp']:
        obj = OUT / (name + '.o')
        args = ['/usr/bin/clang++'] + flags['CXX_DEFINES'] + flags['CXX_INCLUDES'] + flags['CXX_FLAGS']
        args += ['-c', str(source / 'zone' / name), '-o', str(obj)]
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
    run('native-policy-tests', ['python3', str(INPUT / 'verify_aa_tbs_native.py'), str(source), str(OUT / 'native-tests')])
    final_inputs = {str((BASE / 'build/zone' / arg).resolve()): sha((BASE / 'build/zone' / arg).resolve())
                    for arg in link[1:] if arg.endswith(('.o', '.a', '.so')) and (BASE / 'build/zone' / arg).is_file()}
    manifest = {'status': 'built_not_installed', 'base_manifest_sha256': sha(LIVE / 'manifest.json'),
                'source_files': before, 'changed_source_files': CHANGED, 'added_source_files': ADDED,
                'binaries': {**prior['binaries'], 'zone': sha(OUT / 'zone')},
                'compile_commands': commands, 'link_command': link,
                'unchanged_link_inputs': retained, 'final_link_inputs': final_inputs}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'binaries': manifest['binaries']}), flush=True)


if __name__ == '__main__':
    main()
