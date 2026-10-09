"""Build the exact public payload; never archive the repository or private data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'index.html', 'site-assets/site.css', 'site-assets/moon.svg',
    'site-assets/traders-at-dusk.png', 'site-assets/master-of-three.png',
)
FORBIDDEN = re.compile(r'ever\s*quest|\beq\b|eqemu|rof2|macroquest', re.I)


def package(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Use a new package path; existing releases are immutable')
    hashes = {}
    for name in FILES:
        data = (ROOT / name).read_bytes()
        if not name.endswith('.png') and FORBIDDEN.search(data.decode('utf-8-sig')):
            raise ValueError(f'Brand restriction failed: {name}')
        hashes[name] = hashlib.sha256(data).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(destination, 'x:gz') as archive:
        for name in FILES:
            archive.add(ROOT / name, arcname=name, recursive=False)
    manifest = destination.with_suffix('.json')
    manifest.write_text(json.dumps(hashes, indent=2) + '\n', encoding='utf-8')
    return hashes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.destination), indent=2))
