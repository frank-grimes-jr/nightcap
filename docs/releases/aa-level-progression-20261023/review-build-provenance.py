"""Read-only audit of retained build provenance; never configures or builds.

Run from Windows: python -B review-build-provenance.py
Requires read access to local akk-stack-eqemu-server-1. JSON goes to stdout.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
MANIFESTS = [
    ('docs/releases/thj-behaviors-20261019/native-build-manifest.json', '/tmp/nightcap-thj-behaviors-v1/final-manifest.json'),
    ('docs/releases/aa-pacing-million-20261021/native-build-manifest.json', '/tmp/nightcap-aa-pacing-million-v2/manifest.json'),
    ('docs/dungeons/classic-rewards-20261022/build-manifest.json', '/tmp/nightcap-classic-rewards-build-v2/manifest.json'),
    ('docs/releases/quest-tier-handins-20261022/native-build-manifest.json', '/tmp/nightcap-quest-handins-build-v1/manifest.json'),
    ('docs/ops/hate-keeper-commonlands-20261022/build-manifest.json', '/tmp/nightcap-hate-keeper-build-v1/manifest.json'),
]
ALLOWED = sorted(['common/aa_progression.h', 'common/ruletypes.h', 'zone/client.cpp',
                  'zone/client.h', 'zone/exp.cpp', 'zone/zonedb.cpp', 'zone/gm_commands/aa_exp.cpp'])

def digest(data):
    return hashlib.sha256(data).hexdigest()

CODE = r'''
import datetime, hashlib, json, pathlib, sys
P = pathlib.Path
request = json.load(sys.stdin)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
normalized = lambda p: hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
records = []
for name, expected in request['manifests'].items():
    p = P(name)
    assert normalized(p) == expected, ('retained manifest mismatch', name)
    records.append({'path': name, 'sha256': sha(p), 'repository_normalized_sha256': expected})
base = P('/tmp/nightcap-thj-behaviors-v1')
m = json.loads((base/'final-manifest.json').read_text())
assert all(sha(base/'source'/n) == h for n,h in m['source_files'].items()), 'THJ source drift'
paths = {n: base/'source'/n for n in m['source_files']}
overlays = []
for root, source, key, flat in [
    ('/tmp/nightcap-aa-pacing-million-v2', '/tmp/nightcap-aa-pacing-million-v2', 'changed_sources', True),
    ('/tmp/nightcap-classic-rewards-build-v2', '/tmp/nightcap-classic-rewards-input', 'candidate_sources', False),
    ('/tmp/nightcap-quest-handins-build-v1', '/tmp/nightcap-quest-handins-build-v1/source', 'candidate_sources', False),
    ('/tmp/nightcap-hate-keeper-build-v1', '/tmp/nightcap-hate-keeper-input', 'candidate_sources', False),
]:
    mm = json.loads((P(root)/'manifest.json').read_text())
    entries = {}
    for n,h in mm[key].items():
        p = P(source)/(P(n).name if flat else n)
        assert sha(p) == h, ('overlay source drift', str(p))
        paths[n] = p
        entries[n] = {'path': str(p), 'sha256': h}
    overlays.append({'manifest': root+'/manifest.json', 'hash_key': key, 'sources': entries})
keeper = json.loads(P('/tmp/nightcap-hate-keeper-build-v1/manifest.json').read_text())
assert all(sha(P(n)) == h for n,h in keeper['retained_inputs'].items()), 'retained object drift'
zone = sha(P('/tmp/nightcap-hate-keeper-build-v1/zone'))
world = sha(P('/tmp/nightcap-classic-rewards-build-v2/world'))
shared = sha(P('/tmp/nightcap-classic-rewards-build-v2/shared_memory'))
assert zone == keeper['zone_sha256'] == '1d4ef362639722b7eaddc49ae2883e2c5abcefc7c5d958f622cfb048308b995f'
classic = json.loads(P('/tmp/nightcap-classic-rewards-build-v2/manifest.json').read_text())
assert world == classic['other_binaries']['world']['candidate']
assert shared == classic['other_binaries']['shared_memory']['candidate']
diff = sorted(n for n,h in request['checkout_normalized'].items() if n not in paths or normalized(paths[n]) != h)
assert diff == request['allowed_changes'], ('unexpected checkout source drift', diff)
cache_path = base/'build/CMakeCache.txt'
keys = ('CMAKE_BUILD_TYPE:', 'CMAKE_CXX_COMPILER:', 'CMAKE_CXX_COMPILER_LAUNCHER:',
        'CMAKE_GENERATOR:', 'CMAKE_MAKE_PROGRAM:', 'CMAKE_TOOLCHAIN_FILE:',
        'VCPKG_INSTALLED_DIR:', 'VCPKG_MANIFEST_MODE:', 'VCPKG_TARGET_TRIPLET:', 'EQEMU_')
cache = [line for line in cache_path.read_text().splitlines()
         if line.startswith(keys) and '-ADVANCED:' not in line]
deps = {}
for name in ['/usr/bin/clang++', '/usr/bin/ccache',
             '/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
             '/home/eqemu/code/build/vcpkg_installed/vcpkg/status']:
    p = P(name); assert p.is_file(), ('missing build dependency', name)
    deps[name] = {'resolved': str(p.resolve()), 'sha256': sha(p)}
assembled = {n:sha(p) for n,p in sorted(paths.items())}
report = {
    'status':'read_only_provenance_pass', 'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'production_probed':False, 'build_executed':False,
    'base_source':str(base/'source'), 'base_hash_key':'source_files',
    'manifests':records, 'ordered_overlays':overlays,
    'assembled_source_count':len(paths),
    'assembled_source_map_sha256':hashlib.sha256(json.dumps(assembled,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'retained_inputs_verified':len(keeper['retained_inputs']),
    'retained_binaries':{'zone':zone,'world':world,'shared_memory':shared},
    'checkout_comparison':'CRLF normalized to LF only', 'checkout_delta':diff,
    'checkout_delta_raw_sha256':{n:request['checkout_raw'][n] for n in diff},
    'cmake_cache_path':str(cache_path), 'cmake_cache_sha256':sha(cache_path),
    'cmake_cache_options':cache, 'dependencies':deps,
    'fresh_configure_command':['cmake','-S','<fresh-source>','-B','<fresh-build>',
      '-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
      '-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
      '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
      '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
      '-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],
    'fresh_build_command':['cmake','--build','<fresh-build>','--target','world','zone','shared_memory','-j2'],
    'boundary':'Authenticates retained local baseline and overlays, not fresh production state or future build outputs. Rebuild PCH and all rule-dependent objects in a fresh build directory.'
}
print(json.dumps(report,indent=2))
'''

def main():
    raw = {p.relative_to(ROOT/'server-mods/code').as_posix():p.read_bytes()
           for p in (ROOT/'server-mods/code').rglob('*') if p.is_file()}
    request = {
        'manifests':{remote:digest((ROOT/local).read_bytes().replace(b'\r\n',b'\n')) for local,remote in MANIFESTS},
        'checkout_normalized':{n:digest(b.replace(b'\r\n',b'\n')) for n,b in raw.items()},
        'checkout_raw':{n:digest(b) for n,b in raw.items()}, 'allowed_changes':ALLOWED,
    }
    result = subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',CODE],
                            input=json.dumps(request),text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr + result.stdout)
    print(result.stdout,end='')

if __name__ == '__main__':
    main()
