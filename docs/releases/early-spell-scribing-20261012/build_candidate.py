"""Build an isolated zone from the retained sell-all release; never install it."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git', 'build', 'build-tests', 'vcpkg'}.intersection(p.relative_to(root).parts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retained', type=Path, default=Path('/tmp/nightcap-sellall-build-20261012-v3'))
    parser.add_argument('--base', type=Path, default=Path('/tmp/nightcap-item-upgrades-release-build-20261012'))
    args = parser.parse_args()
    prior = json.loads((args.retained / 'manifest.json').read_text())
    inputs = json.loads((args.input / 'input.json').read_text())
    changed = ['zone/client_process.cpp', 'zone/effects.cpp']
    assert fingerprints(args.retained / 'source') == prior['source_files'], 'Retained source drift'
    assert sha(args.retained / 'zone') == prior['binaries']['zone'], 'Retained binary drift'
    for group in ('unchanged_link_inputs', 'retained_unity_inputs'):
        assert all(sha(Path(p)) == h for p, h in prior[group].items()), group
    for name in changed:
        retained = (args.retained / 'source' / name).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(retained).hexdigest() == inputs['baseline'][name], 'Git/live source mismatch: ' + name
        assert sha(args.input / name) == inputs['candidate'][name], 'Input drift'
    args.output.mkdir(exist_ok=False)
    source = args.output / 'source'
    shutil.copytree(args.retained / 'source', source)
    for name in changed:
        shutil.copyfile(args.input / name, source / name)
    before = fingerprints(source)
    assert sorted(n for n, h in before.items() if h != prior['source_files'][n]) == changed

    def run(name, command):
        print(name, flush=True)
        with (args.output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=args.base / 'build/zone', stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((args.output / (name + '.log')).read_text()[-6000:], flush=True)
            raise RuntimeError(name + ' failed')

    flags = {}
    for line in (args.base / 'build/zone/CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =', 'CXX_FLAGS =')):
            key, value = line.split('=', 1)
            flags[key.strip()] = shlex.split(value.replace(str(args.base / 'source'), str(source)))
    link = list(prior['link_command'])
    old_inputs = {str((args.base / 'build/zone' / arg).resolve()): sha((args.base / 'build/zone' / arg).resolve())
                  for arg in link[1:] if arg.endswith(('.o', '.a', '.so')) and (args.base / 'build/zone' / arg).is_file()}
    commands = []
    for name in changed:
        target = args.output / (Path(name).name + '.o')
        command = ['/usr/bin/clang++'] + flags['CXX_DEFINES'] + flags['CXX_INCLUDES'] + flags['CXX_FLAGS']
        command += ['-c', str(source / name), '-o', str(target)]
        run('compile-' + Path(name).stem, command)
        commands.append(command)
        old_object = 'CMakeFiles/zone.dir/' + Path(name).name + '.o'
        assert link.count(old_object) == 1
        link[link.index(old_object)] = str(target)
    link[link.index('-o') + 1] = str(args.output / 'zone')
    run('link', link)
    run('ldd', ['ldd', str(args.output / 'zone')])
    assert 'not found' not in (args.output / 'ldd.log').read_text()
    assert all(sha(Path(p)) == h for p, h in old_inputs.items()), 'Retained object drift'
    assert fingerprints(source) == before
    assert fingerprints(args.retained / 'source') == prior['source_files']
    assert sha(args.retained / 'zone') == prior['binaries']['zone']
    result = {'status': 'built_not_installed', 'baseline_commit': inputs['baseline_commit'],
              'base_manifest_sha256': sha(args.retained / 'manifest.json'),
              'base_binaries': prior['binaries'], 'zone_sha256': sha(args.output / 'zone'),
              'changed_source_files': changed, 'source_files': before,
              'compile_commands': commands, 'link_command': link, 'unchanged_link_inputs': old_inputs}
    (args.output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'zone_sha256': result['zone_sha256']}), flush=True)


if __name__ == '__main__':
    main()
