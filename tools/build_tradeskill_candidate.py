"""Compile an isolated zone candidate from the retained October 13 AA build.

Run inside the development container with --input containing the two overlay
files. Never installs, changes the database, or restarts a service.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012/build/zone')
RETAINED = Path('/tmp/nightcap-aa-class-ranks-build-20261013-v2')
MANIFEST = '28245048bb6b43b4c3f017299786fd03d20e33ded426e9612ac80d8c5a26cd2c'
ORIGINAL = '53cd12b0e8c4e677cfaac87108634086e6c7b53ed1f869c5820c121dde286c8f'
CHANGED = ['zone/tradeskills.cpp', 'common/tradeskill_policy.h']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sha(RETAINED / 'manifest.json') == MANIFEST, 'Retained manifest drift'
    prior = json.loads((RETAINED / 'manifest.json').read_text())
    assert fingerprints(RETAINED / 'source') == prior['source_files'], 'Retained source drift'
    assert prior['source_files']['zone/tradeskills.cpp'] == ORIGINAL
    assert sha(RETAINED / 'zone') == prior['binaries']['zone']
    link = list(prior['link_command'])
    inputs = {str((BASE / arg).resolve()): sha((BASE / arg).resolve())
              for arg in link[1:] if arg.endswith(('.o', '.a', '.so', '.so.5.36'))}
    assert inputs == prior['final_link_inputs'], 'Retained link inputs drift'
    requested = {name: sha(args.input / name) for name in CHANGED}
    args.output.mkdir(exist_ok=False)
    source = args.output / 'source'
    shutil.copytree(RETAINED / 'source', source)
    for name in CHANGED:
        shutil.copyfile(args.input / name, source / name)
    before = fingerprints(source)
    assert sorted(n for n, digest in before.items() if digest != prior['source_files'].get(n)) == sorted(CHANGED)
    assert set(prior['source_files']) <= set(before)
    compile_args = [arg.replace(str(RETAINED / 'source'), str(source))
                    for arg in prior['compile_commands']['aa.cpp']]
    compile_args[compile_args.index('-c') + 1] = str(source / 'zone/tradeskills.cpp')
    obj = args.output / 'tradeskills.cpp.o'
    compile_args[compile_args.index('-o') + 1] = str(obj)
    old_objects = [i for i, arg in enumerate(link) if arg.endswith('/tradeskills.cpp.o')]
    assert len(old_objects) == 1
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
    assert all(sha(Path(path)) == digest for path, digest in inputs.items()), 'Retained inputs changed'
    assert fingerprints(RETAINED / 'source') == prior['source_files']
    assert fingerprints(source) == before
    assert all(sha(args.input / name) == digest for name, digest in requested.items())
    assert sha(RETAINED / 'zone') == prior['binaries']['zone']
    evidence = {'status': 'built_not_installed', 'base_manifest_sha256': MANIFEST,
                'base_zone_sha256': prior['binaries']['zone'], 'original_tradeskills_sha256': ORIGINAL,
                'source_files': before, 'changed_source_files': CHANGED, 'input_files': requested,
                'compile_command': compile_args, 'link_command': link, 'retained_link_inputs': inputs,
                'candidate_object_sha256': sha(obj), 'zone_sha256': sha(args.output / 'zone')}
    (args.output / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({k: evidence[k] for k in ('status', 'zone_sha256', 'input_files')}), flush=True)


if __name__ == '__main__':
    main()
