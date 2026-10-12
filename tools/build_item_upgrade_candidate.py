"""Build a release candidate inside the local development container; never install it.

The input directory contains input.json, five code files, the quest and SQL.
input.json records the expected retained baseline and exact Git candidate bytes.
The retained food/drink release manifest must still describe its source tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

FILES = (
    'common/item_upgrade_policy.h', 'zone/advanced_loot_inventory.cpp',
    'zone/advanced_loot_inventory.h', 'zone/client_packet.cpp',
    'zone/zone_hunt_forge.cpp',
)
PAYLOADS = ('quests/ecommons/999820.pl', 'sql/install.sql', 'sql/activate.sql', 'sql/rollback.sql')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def tree_fingerprints(root):
    paths = list(root.rglob('*'))
    assert not any(p.is_symlink() for p in paths), f'Symlink in {root}'
    return {p.relative_to(root).as_posix(): digest(p) for p in paths if p.is_file()}


def verify_payloads(folder, expected):
    assert set(expected) == set(PAYLOADS), 'Unexpected payload scope'
    actual = {}
    for name in ('quests', 'sql'):
        actual.update({name + '/' + path: value for path, value in tree_fingerprints(folder / name).items()})
    assert actual == expected, 'Payload changed or has unexpected files'


def verify_archive(package, expected):
    with tarfile.open(package, 'r:gz') as archive:
        members = archive.getmembers()
        assert len(members) == len(expected) and {m.name for m in members} == set(expected)
        assert all(m.isfile() for m in members), 'Non-file archive member'
        for member in members:
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == expected[member.name], member.name


def run(command, cwd, log):
    with log.open('w') as output:
        result = subprocess.run(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text()[-12000:], flush=True)
        raise RuntimeError(f'{command[0]} failed: {result.returncode}; see {log}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package-only', action='store_true',
                        help='Verify and repackage an already completed matching build without recompiling')
    args = parser.parse_args()
    metadata = json.loads((args.input / 'input.json').read_text())
    assert set(metadata['files']) == set(FILES), 'Unexpected source scope'
    baseline_manifest = args.baseline / 'manifest.json'
    baseline = json.loads(baseline_manifest.read_text())
    assert tree_fingerprints(args.baseline / 'source') == baseline['source_files'], 'Baseline source drift'
    verify_payloads(args.input, metadata['payloads'])
    for name, expected in metadata['files'].items():
        old = args.baseline / 'source' / name
        assert (normalized_digest(old) if old.exists() else None) == expected['base'], name
        assert digest(args.input / 'code' / name) == expected['candidate'], name
    source = args.output / 'source'
    fingerprints = dict(baseline['source_files'])
    fingerprints.update({name: metadata['files'][name]['candidate'] for name in FILES})
    if not args.package_only:
        args.output.mkdir(exist_ok=False)
        shutil.copytree(args.baseline / 'source', source, symlinks=True)
        for name in FILES:
            (source / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.input / 'code' / name, source / name)
    assert tree_fingerprints(source) == fingerprints, 'Candidate is not the exact scoped overlay'
    build = args.output / 'build'
    command = ['cmake', '-S', str(source), '-B', str(build),
               '-DCMAKE_BUILD_TYPE=RelWithDebInfo', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
               '-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
               '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
               '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed',
               '-DVCPKG_MANIFEST_MODE=OFF', '-DEQEMU_BUILD_PERL=ON', '-DEQEMU_BUILD_LUA=ON']
    binary = build / 'bin/zone'
    if args.package_only:
        prior = json.loads((args.output / 'manifest.json').read_text())
        assert prior['status'] == 'passed' and prior['candidate_commit'] == metadata['candidate_commit']
        assert prior['source_files'] == fingerprints and prior['zone_sha256'] == digest(binary)
        assert prior['baseline_manifest_sha256'] == digest(baseline_manifest)
        assert prior['configure_command'] == command
    else:
        run(command, args.output, args.output / 'configure.log')
        print('Baseline verified; isolated release build configured.', flush=True)
        run(['cmake', '--build', str(build), '--target', 'zone', '-j2'],
            args.output, args.output / 'build.log')
    assert tree_fingerprints(source) == fingerprints, 'Source changed during build'
    run(['ldd', str(binary)], args.output, args.output / 'ldd.log')
    assert 'not found' not in (args.output / 'ldd.log').read_text(), 'Unresolved runtime library'
    manifest = {'status': 'passed', 'scope': 'Complete linked zone build; not installed or accepted in game',
                'candidate_commit': metadata['candidate_commit'],
                'payload_commit': metadata.get('payload_commit', metadata['candidate_commit']),
                'baseline_manifest_sha256': digest(baseline_manifest),
                'zone_sha256': digest(binary), 'zone_bytes': binary.stat().st_size,
                'changed_sources': metadata['files'], 'source_files': fingerprints,
                'payloads': metadata['payloads'], 'complete_source_membership_verified': True,
                'configure_command': command, 'build_command': 'cmake --build build --target zone -j2',
                'world_rule_catalog_changed': False}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    verify_payloads(args.input, metadata['payloads'])
    package = args.output / 'item-upgrades-candidate-verified.tar.gz'
    with tarfile.open(package, 'w:gz') as archive:
        archive.add(binary, arcname='bin/zone')
        archive.add(args.output / 'manifest.json', arcname='manifest.json')
        for name in PAYLOADS:
            archive.add(args.input / name, arcname=name)
    verify_archive(package, {'bin/zone': manifest['zone_sha256'],
                            'manifest.json': digest(args.output / 'manifest.json'), **metadata['payloads']})
    summary = {key: value for key, value in manifest.items() if key != 'source_files'}
    summary.update(package_sha256=digest(package), package_bytes=package.stat().st_size)
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Complete zone link, runtime library resolution and candidate packaging passed.', flush=True)


if __name__ == '__main__':
    main()
