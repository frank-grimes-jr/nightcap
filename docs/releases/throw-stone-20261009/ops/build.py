"""Fresh zone build over the fingerprinted previously deployed native source."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

BASE = Path('/tmp/nightcap-passive-aa-build-20261004-r2')
INPUT = Path('/tmp/nightcap-throw-stone-input-20261009')
OUT = Path('/tmp/nightcap-throw-stone-build-20261009')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def run(name, args, cwd=None):
    print(json.dumps({'stage': name, 'started': time.time()}), flush=True)
    with (OUT / (name + '.log')).open('w') as log:
        result = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join((OUT / (name + '.log')).read_text().splitlines()[-40:]), flush=True)
        raise RuntimeError(name + ' failed')


prior = json.loads((BASE / 'manifest.json').read_text())
assert fingerprints(BASE / 'source') == prior['source_files'], 'Production source drift'
for name, digest in prior['binaries'].items():
    assert sha(BASE / 'build/bin' / name) == digest, name
OUT.mkdir(exist_ok=False)
source = OUT / 'source'
shutil.copytree(BASE / 'source', source, ignore=shutil.ignore_patterns('.git', 'build', 'build-tests', 'vcpkg'))
changed = json.loads((INPUT / 'changed.json').read_text())
assert changed == ['zone/effects.cpp']
for name in changed:
    p = source / name
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
run('patch-check', ['patch', '--batch', '--forward', '--fuzz=0', '--no-backup-if-mismatch', '--dry-run', '-p1', '-i', str(INPUT / 'changes.patch')], source)
run('patch-apply', ['patch', '--batch', '--forward', '--fuzz=0', '--no-backup-if-mismatch', '-p1', '-i', str(INPUT / 'changes.patch')], source)
before = fingerprints(source)
assert {n for n, h in before.items() if prior['source_files'].get(n) != h} == set(changed)
assert set(before) == set(prior['source_files'])

# Run the real-method fixture against this exact hardened production candidate.
fixture = OUT / 'fixture'
tests = fixture / 'tools/tests'
tests.mkdir(parents=True)
for name in ('test_throw_stone.py', 'test_passive_aa.py'):
    shutil.copyfile(INPUT / name, tests / name)
effects = fixture / 'server-mods/code/zone/effects.cpp'
effects.parent.mkdir(parents=True)
effects.symlink_to(source / 'zone/effects.cpp')
run('tests', ['python3', str(tests / 'test_throw_stone.py'), '--compiler', 'clang++'])
assert '108 checks, 0 failures' in (OUT / 'tests.log').read_text()

run('configure', ['cmake', '-S', str(source), '-B', str(OUT / 'build'), *prior['cmake_flags']])
run('build', ['cmake', '--build', str(OUT / 'build'), '--target', 'zone', '-j', '4'])
assert fingerprints(source) == before, 'Candidate source changed during build'
assert fingerprints(BASE / 'source') == prior['source_files'], 'Baseline source changed'
result = {
    'base_manifest_sha256': sha(BASE / 'manifest.json'),
    'hardening_sha256': prior['hardening_sha256'],
    'source_files': before,
    'binaries': {'zone': sha(OUT / 'build/bin/zone')},
    'unchanged_binaries': {n: h for n, h in prior['binaries'].items() if n != 'zone'},
    'changed_source_files': changed,
    'cmake_flags': prior['cmake_flags'],
    'patch_sha256': sha(INPUT / 'changes.patch'),
    'feature_commit': '8899f6c',
    'native_checks': 108,
    'status': 'built_not_installed',
}
(OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'source_files'}), flush=True)
