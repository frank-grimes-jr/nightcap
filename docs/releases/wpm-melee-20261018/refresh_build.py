"""Refresh only this candidate from a verified completed candidate manifest."""
import json
from pathlib import Path
import shutil
from build import ROOT, INPUT, fingerprints, run, sha


def main():
    previous = json.loads((ROOT / 'manifest.json').read_text())
    current = fingerprints(ROOT / 'source')
    failed_inputs = json.loads((ROOT / 'input-sources.json').read_text())
    assert current in (previous['source_files'], failed_inputs), 'Candidate source drift'
    expected = json.loads((INPUT / 'expected.json').read_text())
    for name, digest in expected.items():
        incoming = INPUT / 'source' / name
        assert sha(incoming) == digest, name
        target = ROOT / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or sha(target) != digest:
            shutil.copyfile(incoming, target)
    before = fingerprints(ROOT / 'source')
    # Record inputs before compiling, including a failed attempt for diagnostics.
    (ROOT / 'input-sources.json').write_text(json.dumps(before, indent=2) + '\n')
    run(['cmake', '--build', str(ROOT / 'build'), '--target', 'world', 'zone', 'shared_memory', '-j3'], 'refresh-build')
    for binary in ('world', 'zone', 'shared_memory'):
        run(['ldd', str(ROOT / 'build/bin' / binary)], 'ldd-' + binary)
        assert 'not found' not in (ROOT / ('ldd-' + binary + '.log')).read_text()
    assert fingerprints(ROOT / 'source') == before, 'Inputs changed during build'
    previous.update(source_files=before, requested_sources=expected,
                    zone_sha256=sha(ROOT / 'build/bin/zone'), world_sha256=sha(ROOT / 'build/bin/world'),
                    shared_memory_sha256=sha(ROOT / 'build/bin/shared_memory'))
    (ROOT / 'manifest.json').write_text(json.dumps(previous, indent=2) + '\n')
    print(json.dumps({k:v for k,v in previous.items() if k not in ('source_files','requested_sources')}), flush=True)


if __name__ == '__main__':
    main()
