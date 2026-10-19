"""Build an isolated paired world/zone candidate from verified retained sources."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASE = Path('/tmp/nightcap-cooldown-identities-build-v1')
ROOT = Path('/tmp/nightcap-thj-pet-scaling-v1')
INPUT = Path('/tmp/nightcap-thj-pet-input')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '.git' not in p.parts}


def run(command, label):
    print(label, flush=True)
    with (ROOT / (label + '.log')).open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((ROOT / (label + '.log')).read_text()[-16000:], flush=True)
        raise RuntimeError(label)


def main():
    prior = json.loads((BASE / 'manifest.json').read_text())
    baseline = fingerprints(BASE / 'source')
    assert baseline == prior['source_files'], 'Retained source drift'
    expected = json.loads((INPUT / 'expected.json').read_text())
    ROOT.mkdir(exist_ok=False)
    source = ROOT / 'source'
    shutil.copytree(BASE / 'source', source)
    for name, digest in expected.items():
        incoming = INPUT / 'source' / name
        assert sha(incoming) == digest, name
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(incoming, target)
    before = fingerprints(source)
    (ROOT / 'input-sources.json').write_text(json.dumps(before, indent=2) + '\n')
    run(['cmake', '-S', str(source), '-B', str(ROOT / 'build'), '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
         '-DCMAKE_CXX_COMPILER=/usr/bin/clang++', '-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
         '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
         '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed', '-DVCPKG_MANIFEST_MODE=OFF',
         '-DEQEMU_BUILD_PERL=ON', '-DEQEMU_BUILD_LUA=ON'], 'configure')
    run(['cmake', '--build', str(ROOT / 'build'), '--target', 'world', 'zone', '-j3'], 'build')
    for binary in ('world', 'zone'):
        run(['ldd', str(ROOT / 'build/bin' / binary)], 'ldd-' + binary)
        assert 'not found' not in (ROOT / ('ldd-' + binary + '.log')).read_text()
    assert fingerprints(source) == before, 'Inputs changed during build'
    assert fingerprints(BASE / 'source') == baseline, 'Retained source changed'
    result = {'status': 'built_not_installed', 'source_files': before, 'requested_sources': expected,
              'baseline_manifest_sha256': sha(BASE / 'manifest.json'),
              'production_zone_sha256': '29b8093147ffbc4c0d387a4e3fa55a3a041dbb9ae7da731b493b21601a6dec2f',
              'zone_sha256': sha(ROOT / 'build/bin/zone'), 'world_sha256': sha(ROOT / 'build/bin/world'),
              'owner_gameplay_accepted': False}
    (ROOT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('source_files', 'requested_sources')}), flush=True)


if __name__ == '__main__':
    main()
