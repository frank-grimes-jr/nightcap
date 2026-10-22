"""Build one implementation-only correction from the authenticated current THJ behavior release."""
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path

BASE = Path('/tmp/nightcap-thj-behaviors-v1')
ROOT = Path('/tmp/nightcap-aa-pacing-million-v2')
INPUT = Path('/tmp/nightcap-aa-pacing-million-input/spells.cpp')
EXPECTED_BASE = '5983172545de3fc8731e228355561527890c787140616ff95c2a602b37b1525a'


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
    assert sha(BASE / 'build/bin/zone') == baseline['zone_sha256'] == EXPECTED_BASE
    assert fingerprints(BASE / 'source') == baseline['source_files']
    old = (BASE / 'source/zone/spells.cpp').read_text()
    before = 'if (IsDisciplineBuff(spell_id) || spells[spell_id].short_buff_box || IsAARelatedBuffSpell(spell_id)) {'
    after = 'if (IsDisciplineBuff(spell_id) || spells[spell_id].short_buff_box ||\n\t\t\tIsEffectInSpell(spell_id, SpellEffect::PercentXPIncrease) || IsAARelatedBuffSpell(spell_id)) {'
    assert old.count(before) == 1
    expected = old.replace(before, after).replace('// The previous blanket policy persisted temporary buffs as permanent.', '// Temporary AA effects and XP boosts must not inherit ordinary buff permanence.\n\t\t\t// The previous blanket policy persisted temporary buffs as permanent.')
    assert INPUT.read_text() == expected, 'Unexpected implementation delta'
    ROOT.mkdir(exist_ok=False)
    source = ROOT / 'spells.cpp'
    source.write_text(expected)
    cwd = BASE / 'build/zone'
    target = cwd / 'CMakeFiles/zone.dir'
    link = shlex.split((target / 'link.txt').read_text())
    output_index = link.index('-o') + 1
    inputs = {str((cwd / arg).resolve()): sha((cwd / arg).resolve()) for arg in link
              if not arg.startswith('-') and (cwd / arg).is_file() and arg != link[output_index]}
    assert len(inputs) > 100
    original_link = list(link)
    original_link[output_index] = str(ROOT / 'zone-baseline')
    run(original_link, 'baseline-link', cwd)
    assert sha(ROOT / 'zone-baseline') == EXPECTED_BASE, 'Retained link inputs do not reproduce baseline'
    flags = dict(re.findall(r'^(CXX_\w+) = (.*)$', (target / 'flags.make').read_text(), re.M))
    compile_args = ['/usr/bin/clang++', '-I' + str(BASE / 'source/zone')]
    for key in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS'):
        compile_args += shlex.split(flags[key])
    compile_args += ['-Winvalid-pch', '-Xclang', '-include-pch', '-Xclang', str(target / 'cmake_pch.hxx.pch'),
                     '-Xclang', '-include', '-Xclang', str(target / 'cmake_pch.hxx'),
                     '-o', str(ROOT / 'spells.cpp.o'), '-c', str(source)]
    run(compile_args, 'compile', cwd)
    object_name = 'CMakeFiles/zone.dir/spells.cpp.o'
    assert link.count(object_name) == 1
    link[link.index(object_name)] = str(ROOT / 'spells.cpp.o')
    link[output_index] = str(ROOT / 'zone')
    run(link, 'candidate-link', cwd)
    run(['ldd', str(ROOT / 'zone')], 'ldd', cwd)
    assert 'not found' not in (ROOT / 'ldd.log').read_text()
    assert all(sha(Path(p)) == digest for p, digest in inputs.items())
    assert fingerprints(BASE / 'source') == baseline['source_files']
    assert sha(BASE / 'build/bin/zone') == EXPECTED_BASE
    result = {'status': 'built_not_installed', 'baseline_zone_sha256': EXPECTED_BASE,
              'baseline_reproduced': True, 'retained_inputs': inputs,
              'baseline_manifest_sha256': sha(BASE / 'final-manifest.json'),
              'changed_sources': {'zone/spells.cpp': sha(source)},
              'zone_sha256': sha(ROOT / 'zone'), 'abi_changed': False,
              'owner_gameplay_accepted': False}
    (ROOT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'retained_inputs'}), flush=True)


if __name__ == '__main__':
    main()
