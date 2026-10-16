"""Build an isolated zone from the retained tradeskill release; never install it."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

RETAINED = Path('/tmp/nightcap-tradeskill-build-20261013-v2')
BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012/build/zone')
MANIFEST_SHA = 'f11a95ccb772cf25c5c4e718395d3f71738b2858165c7ce7a8f4216a15189e18'
ORIGINAL_SPELLS_SHA = '1f4307d21715aaa6aebd47706076ce1a1ec9c4cce06ca7ff72d003a75c07ae44'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spells', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sha(RETAINED / 'manifest.json') == MANIFEST_SHA, 'Retained manifest drift'
    prior = json.loads((RETAINED / 'manifest.json').read_text())
    assert fingerprints(RETAINED / 'source') == prior['source_files'], 'Retained source drift'
    assert prior['source_files']['zone/spells.cpp'] == ORIGINAL_SPELLS_SHA
    assert sha(RETAINED / 'zone') == prior['zone_sha256'], 'Retained zone drift'
    link = list(prior['link_command'])
    old_objects = [i for i, arg in enumerate(link) if arg.endswith('/spells.cpp.o')]
    assert len(old_objects) == 1, 'Expected one spells object'
    inputs = {str((BASE / arg).resolve()): sha((BASE / arg).resolve())
              for arg in link[1:] if arg.endswith(('.o', '.a', '.so')) or '.so.' in Path(arg).name}
    known_inputs = dict(prior['retained_link_inputs'])
    known_inputs[str(RETAINED / 'tradeskills.cpp.o')] = prior['candidate_object_sha256']
    assert all(known_inputs.get(path) == digest for path, digest in inputs.items()), 'Retained link input drift'
    requested_sha = sha(args.spells)
    args.output.mkdir(exist_ok=False)
    source = args.output / 'source'
    shutil.copytree(RETAINED / 'source', source)
    shutil.copyfile(args.spells, source / 'zone/spells.cpp')
    before = fingerprints(source)
    assert set(before) == set(prior['source_files'])
    assert [name for name in before if before[name] != prior['source_files'][name]] == ['zone/spells.cpp']
    compile_args = [arg.replace(str(RETAINED / 'source'), str(source)) for arg in prior['compile_command']]
    compile_args[compile_args.index('-c') + 1] = str(source / 'zone/spells.cpp')
    obj = args.output / 'spells.cpp.o'
    compile_args[compile_args.index('-o') + 1] = str(obj)
    link[old_objects[0]] = str(obj)
    link[link.index('-o') + 1] = str(args.output / 'zone')
    for name, command in [('compile', compile_args), ('link', link), ('ldd', ['ldd', str(args.output / 'zone')])]:
        print(name, flush=True)
        with (args.output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=BASE, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((args.output / (name + '.log')).read_text()[-12000:], flush=True)
            raise RuntimeError(name + ' failed')
    assert 'not found' not in (args.output / 'ldd.log').read_text()
    assert all(sha(Path(path)) == digest for path, digest in inputs.items()), 'Retained inputs changed during build'
    assert fingerprints(RETAINED / 'source') == prior['source_files']
    assert fingerprints(source) == before
    assert sha(args.spells) == requested_sha
    assert sha(RETAINED / 'zone') == prior['zone_sha256']
    evidence = {'status': 'built_not_installed', 'base_manifest_sha256': MANIFEST_SHA,
                'base_zone_sha256': prior['zone_sha256'], 'original_spells_sha256': ORIGINAL_SPELLS_SHA,
                'changed_source_files': ['zone/spells.cpp'], 'source_files': before,
                'input_spells_sha256': requested_sha, 'compile_command': compile_args,
                'link_command': link, 'retained_link_inputs': inputs,
                'candidate_object_sha256': sha(obj), 'zone_sha256': sha(args.output / 'zone')}
    (args.output / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({k: evidence[k] for k in ('status', 'zone_sha256', 'input_spells_sha256')}), flush=True)


if __name__ == '__main__':
    main()
