"""Repeat the two pinned 12-fight controls using the fresh diagnostic binary.

Run with container Python from /tmp/nightcap-balance-fresh-20260913 after copying
the four aa-ownership regression input/evidence files and tools/balance as python/.
The established runtime and its binary are not modified.
"""
import contextlib
import gzip
import hashlib
import json
from pathlib import Path
import sys

root = Path('/tmp/nightcap-balance-fresh-20260913')
if Path.cwd().resolve() != root:
    raise SystemExit('Use the separate fresh diagnostic runtime')
sys.path.insert(0, str(root / 'python'))
import pet_controls
from release_pool_controls import summarize

pet_controls.ROOT = root
binary_sha256 = hashlib.sha256((root / 'balance-zone').read_bytes()).hexdigest()
checks = {'binary_sha256': binary_sha256, 'batches': []}
for kind in ('regression', 'source-regression'):
    source = root / ('aa-ownership-' + kind + '-inputs.json')
    reference = root / ('aa-ownership-' + kind + '.json.gz')
    matrix = json.loads(source.read_bytes())
    original_binary = matrix['binary_sha256']
    matrix['binary_sha256'] = binary_sha256
    destination = root / ('fresh-' + kind + '.json.gz')
    input_path = root / ('fresh-' + kind + '-inputs.json')
    if destination.exists() or input_path.exists():
        raise SystemExit('Refusing to overwrite fresh replay evidence')
    input_path.write_bytes((json.dumps(matrix, separators=(',', ':')) + '\n').encode())
    with (root / ('fresh-' + kind + '.log')).open('w') as log:
        with contextlib.redirect_stdout(log):
            pet_controls.run(matrix, destination, summarize)
    actual = json.loads(gzip.decompress(destination.read_bytes()))['runs']
    expected = json.loads(gzip.decompress(reference.read_bytes()))['runs']
    expected_ids = [case['id'] for case in matrix['cases']]
    if (len(expected_ids) != 12 or len(set(expected_ids)) != 12
            or [run['id'] for run in actual] != expected_ids
            or [run['id'] for run in expected] != expected_ids):
        raise SystemExit('Missing, reordered, or duplicated replay cases')
    differences = [a['id'] for a, b in zip(actual, expected) if a != b]
    checks['batches'].append({
        'kind': kind, 'cases': len(actual), 'original_binary_sha256': original_binary,
        'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
        'actual_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'complete_reports_and_raw_hashes_equal': not differences,
        'differences': differences,
    })
    (root / 'fresh-replay-checks.json').write_bytes((json.dumps(checks, indent=2) + '\n').encode())
    print(kind, len(actual), 'cases;', len(differences), 'differences', flush=True)
    if differences:
        raise SystemExit('Fresh-source replay differs; investigate before promotion')
