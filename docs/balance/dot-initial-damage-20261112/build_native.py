"""Isolated compile/link validation; never installs or starts a game binary.

Run inside the local build container with --candidate pointing at the reviewed
spell_effects.cpp. Retains the full Quick Buff Client-layout-compatible inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    full = Path('/tmp/nightcap-quick-buff-full-20261112-v1')
    shipping = Path('/tmp/nightcap-quick-buff-hotkey-20261112-v2')
    proof = json.loads((shipping / 'native-build.json').read_text())
    assert proof['status'] == 'PASS'
    out = args.output.resolve()
    assert out.parent == Path('/tmp') and not out.exists()
    out.mkdir()
    original = (shipping / 'source/zone/spell_effects.cpp').read_text().encode()
    candidate = args.candidate.read_text().encode()
    guard = b'''\t\t\t\t// Instant player DoTs deal damage on ticks, without a separate landing hit.
\t\t\t\t// Keep positive HP effects and non-player casting on their native paths.
\t\t\t\tif (effect_value < 0 && caster && caster->IsInstantCastDot(spell_id)) {
\t\t\t\t\tbreak;
\t\t\t\t}
'''
    assert candidate.count(guard) == 1 and candidate.replace(guard, b'') == original
    for name, expected in proof['retained_link_inputs'].items():
        assert digest(name) == expected, name
    source = out / 'source'
    shutil.copytree(shipping / 'source', source, symlinks=True)
    (source / 'zone/spell_effects.cpp').write_bytes(candidate)
    build = full / 'build/zone'
    flags = {}
    for line in (build / 'CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key, value = line.split(' = ', 1)
            flags[key] = shlex.split(value.replace(str(full / 'source'), str(source)))
    obj = out / 'spell_effects.cpp.o'
    command = ['/usr/bin/clang++', *flags['CXX_DEFINES'], *flags['CXX_INCLUDES'],
               *flags['CXX_FLAGS'], '-MD', '-MF', str(out / 'spell_effects.cpp.d'),
               '-c', str(source / 'zone/spell_effects.cpp'), '-o', str(obj)]
    subprocess.run(command, check=True)
    link = shlex.split((build / 'CMakeFiles/zone.dir/link.txt').read_text())
    for i, token in enumerate(link):
        if token.endswith(('.o', '.a')):
            link[i] = str((build / token).resolve())
            if token in ('CMakeFiles/zone.dir/aa.cpp.o', 'CMakeFiles/zone.dir/spells.cpp.o'):
                link[i] = str(shipping / Path(token).name)
    output_index = link.index('-o') + 1
    input_index = link.index(str(build / 'CMakeFiles/zone.dir/spell_effects.cpp.o'))
    inputs = {p: digest(p) for p in link if p.endswith(('.o', '.a'))}
    hashes = {}
    for mode in ('baseline', 'candidate'):
        binary = out / (mode + '-zone')
        link[output_index] = str(binary)
        if mode == 'candidate':
            link[input_index] = str(obj)
        subprocess.run(link, cwd=build, check=True)
        subprocess.run(['strip', '--strip-debug', '-o', str(binary) + '.stripped', str(binary)], check=True)
        hashes[mode] = digest(str(binary) + '.stripped')
        if mode == 'baseline':
            assert hashes[mode] == proof['shipping']['candidate-zone'], hashes
    assert all(digest(p) == expected for p, expected in inputs.items())
    result = {'status': 'PASS', 'scope': 'isolated full translation-unit compile and zone link; not deployed or player accepted',
              'baseline_reproduced': True, 'binary_sha256': hashes,
              'candidate_source_sha256': digest(args.candidate),
              'baseline_source_sha256': hashlib.sha256(original).hexdigest(),
              'source_delta': ['zone/spell_effects.cpp'], 'compile_command': command,
              'retained_inputs': inputs, 'candidate_object_sha256': digest(obj)}
    (out / 'native-build.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('compile_command', 'retained_inputs')}))


if __name__ == '__main__':
    main()
