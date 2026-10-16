"""Build class AA depth and Triple Backstab against the fingerprinted live source."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012')
LIVE = Path('/tmp/nightcap-aa-level1-build-20261013')
INPUT = Path('/tmp/nightcap-aa-class-ranks-input-20261013')
OUT = Path('/tmp/nightcap-aa-class-ranks-build-20261013-v2')
CHANGED = ['common/nightcap_aa_policy.h', 'zone/special_attacks.cpp']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def link_inputs(command):
    output = command[command.index('-o') + 1]
    return {str((BASE / 'build/zone' / value).resolve()): sha((BASE / 'build/zone' / value).resolve())
            for value in command[1:] if not value.startswith('-') and value != output
            and (BASE / 'build/zone' / value).is_file()}


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
    assert all(sha(INPUT / name) == value for name, value in expected['files'].items())
    assert all(sha(Path(name)) == value for name, value in prior['final_link_inputs'].items())
    OUT.mkdir(exist_ok=False)
    source = OUT / 'source'
    shutil.copytree(LIVE / 'source', source)
    for name in CHANGED:
        shutil.copyfile(INPUT / name, source / name)
    before = fingerprints(source)
    assert sorted(name for name, value in before.items() if prior['source_files'].get(name) != value) == CHANGED
    assert set(before) == set(prior['source_files'])
    # Prove the only special-attacks semantic change; retain every intervening patch.
    old = (LIVE / 'source/zone/special_attacks.cpp').read_text()
    new = (source / 'zone/special_attacks.cpp').read_text()
    original = '\t\tif (level >= RuleI(Combat, DoubleBackstabLevelRequirement)) {'
    replacement = ('\t\t// A legal earned Triple Backstab AA works from creation. Item/spell bonuses\n'
                   '\t\t// alone retain the native double-backstab level requirement.\n'
                   '\t\tif (level >= RuleI(Combat, DoubleBackstabLevelRequirement) ||\n'
                   '\t\t\t(IsClient() && aabonuses.TripleBackstab > 0)) {')
    assert old.count(original) == 1 and old.replace(original, replacement) == new
    consumers = [p.relative_to(source).as_posix() for p in source.rglob('*.cpp')
                 if 'nightcap_aa_policy.h' in p.read_text(errors='replace')]
    assert consumers == ['zone/aa.cpp'], consumers
    flags = {}
    for line in (BASE / 'build/zone/CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key, value = line.split('=', 1)
            flags[key.strip()] = shlex.split(value.replace(str(BASE / 'source'), str(source)))
    link = list(prior['link_command'])
    commands = {}
    for name in ['aa.cpp', 'special_attacks.cpp']:
        obj = OUT / (name + '.o')
        args = ['/usr/bin/clang++'] + flags['CXX_DEFINES'] + flags['CXX_INCLUDES'] + flags['CXX_FLAGS']
        args += ['-c', str(source / 'zone' / name), '-o', str(obj)]
        run('compile-' + name, args, BASE / 'build')
        matches = [i for i, value in enumerate(link) if value.endswith('/' + name + '.o')]
        assert len(matches) == 1, (name, matches)
        link[matches[0]] = str(obj)
        commands[name] = args
    link[link.index('-o') + 1] = str(OUT / 'zone')
    run('link', link, BASE / 'build/zone')
    assert all(sha(Path(name)) == value for name, value in prior['final_link_inputs'].items())
    assert fingerprints(LIVE / 'source') == prior['source_files'] and fingerprints(source) == before
    run('ldd', ['ldd', str(OUT / 'zone')])
    assert 'not found' not in (OUT / 'ldd.log').read_text()
    for script, name in [('verify_aa_tbs_native.py', 'native-aa'),
                         ('verify_triple_backstab_native.py', 'native-backstab')]:
        run(name, ['python3', str(INPUT / script), str(source), str(OUT / name)])
    final_inputs = link_inputs(link)
    assert len(final_inputs) == len(prior['final_link_inputs'])
    manifest = {'status': 'built_not_installed', 'base_manifest_sha256': sha(LIVE / 'manifest.json'),
                'source_files': before, 'changed_source_files': CHANGED, 'added_source_files': [],
                'binaries': {**prior['binaries'], 'zone': sha(OUT / 'zone')},
                'compile_commands': commands, 'link_command': link,
                'unchanged_link_inputs': prior['final_link_inputs'], 'final_link_inputs': final_inputs}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'zone_sha256': manifest['binaries']['zone']}), flush=True)


if __name__ == '__main__':
    main()
