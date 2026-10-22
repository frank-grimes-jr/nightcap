"""Build the two hand-in implementation changes over the authenticated live zone.

Run inside the local build container. Never installs or restarts anything.
"""
import hashlib
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

BASE = Path('/tmp/nightcap-thj-behaviors-v1')
CURRENT = Path('/tmp/nightcap-aa-pacing-million-v2')
INPUT = Path('/tmp/nightcap-quest-handins')
ROOT = Path('/tmp/nightcap-quest-handins-build-v1')
EXPECTED = '5dd5a6558c837ff2e4724edcd12afcabd2e846379a9ca7b8a6e57e7715600f7b'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '.git' not in p.parts}


def run(args, name, cwd):
    print(name, flush=True)
    with (ROOT / (name + '.log')).open('x') as log:
        result = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError((ROOT / (name + '.log')).read_text()[-8000:])


def main():
    baseline = json.loads((BASE / 'final-manifest.json').read_text())
    current = json.loads((CURRENT / 'manifest.json').read_text())
    inputs = json.loads((INPUT / 'native-input.json').read_text())
    assert sha(CURRENT / 'zone') == current['zone_sha256'] == EXPECTED
    assert fingerprints(BASE / 'source') == baseline['source_files']
    assert all(sha(Path(p)) == digest for p, digest in current['retained_inputs'].items())
    assert sha(CURRENT / 'spells.cpp') == current['changed_sources']['zone/spells.cpp']
    for path, digest in inputs['base_sources'].items():
        assert sha(BASE / 'source' / path) == digest, ('base source drift', path)
    for path, digest in inputs['candidate_sources'].items():
        assert sha(INPUT / 'server-mods/code' / path) == digest, ('candidate drift', path)
    ROOT.mkdir(exist_ok=False)
    for path in inputs['candidate_sources']:
        target = ROOT / 'source' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(INPUT / 'server-mods/code' / path, target)
    cwd = BASE / 'build/zone'
    target = cwd / 'CMakeFiles/zone.dir'
    link = shlex.split((target / 'link.txt').read_text())
    link[link.index('CMakeFiles/zone.dir/spells.cpp.o')] = str(CURRENT / 'spells.cpp.o')
    output_index = link.index('-o') + 1
    retained = {str((cwd / arg).resolve()): sha((cwd / arg).resolve()) for arg in link
                if not arg.startswith('-') and (cwd / arg).is_file() and arg != link[output_index]}
    assert len(retained) > 100
    link[output_index] = str(ROOT / 'zone-baseline')
    run(link, 'baseline-link', cwd)
    assert sha(ROOT / 'zone-baseline') == EXPECTED, 'Current production baseline not reproduced'
    flags = dict(re.findall(r'^(CXX_\w+) = (.*)$', (target / 'flags.make').read_text(), re.M))
    for name in ('npc.cpp', 'task_client_state.cpp'):
        args = ['/usr/bin/clang++', '-I' + str(ROOT / 'source'), '-I' + str(BASE / 'source/zone')]
        for key in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS'):
            args += shlex.split(flags[key])
        args += ['-Winvalid-pch', '-Xclang', '-include-pch', '-Xclang', str(target / 'cmake_pch.hxx.pch'),
                 '-Xclang', '-include', '-Xclang', str(target / 'cmake_pch.hxx'),
                 '-o', str(ROOT / (name + '.o')), '-c', str(ROOT / 'source/zone' / name)]
        run(args, 'compile-' + name, cwd)
        link[link.index('CMakeFiles/zone.dir/' + name + '.o')] = str(ROOT / (name + '.o'))
    link[output_index] = str(ROOT / 'zone')
    run(link, 'candidate-link', cwd)
    run(['ldd', str(ROOT / 'zone')], 'ldd', cwd)
    assert 'not found' not in (ROOT / 'ldd.log').read_text()
    assert all(sha(Path(p)) == digest for p, digest in retained.items())
    assert fingerprints(BASE / 'source') == baseline['source_files']
    result = {'status': 'built_not_installed', 'baseline_reproduced': True,
              'baseline_zone_sha256': EXPECTED, 'zone_sha256': sha(ROOT / 'zone'),
              'retained_inputs': retained, 'candidate_sources': inputs['candidate_sources'],
              'abi_changed': False, 'client_or_cache_changes': False, 'owner_gameplay_accepted': False}
    (ROOT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'retained_inputs'}), flush=True)


if __name__ == '__main__':
    main()
