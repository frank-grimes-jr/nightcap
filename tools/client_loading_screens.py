"""Build the complete RoF2 loading gallery outside the read-only source client.

Requires Pillow. Emits baseline RGB JPEGs without cropping the approved artwork.
The pinned RoF2 executable enumerates uifiles/default/loadscreens/loadscreen*.jpg
and uses Resources/loadscreen.jpg as its fallback, independently of the UI skin.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/nightcap/loading-screens/2026-09-20'
SOURCES = (
    '01-traders-at-dusk.png', '02-lanterns-of-the-canopy.png',
    '03-the-ashen-gate.png', '04-the-last-campfire.png',
    '05-the-four-spires.png', '06-the-orc-frontier.png',
    '07-the-sunken-sanctum.png', '08-the-ember-vault.png',
    '09-dark-elf-paladin-soulfire.png', '10-gnome-master-of-three.png',
)


def targets():
    return {'resources/loadscreen.jpg': SOURCES[-1]} | {
        f'uifiles/default/loadscreens/loadscreen{i:02}.jpg': SOURCES[(i-1) % 10]
        for i in range(1, 56)
    }


def loading_files(art=ART):
    art = Path(art)
    images, source_hashes = {}, {}
    for name in SOURCES:
        raw = (art / name).read_bytes()
        source_hashes[name] = hashlib.sha256(raw).hexdigest()
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            if im.format != 'PNG' or im.size != (1672, 941):
                raise ValueError(f'Unexpected approved artwork: {name}')
            encoded = io.BytesIO()
            im.convert('RGB').save(encoded, 'JPEG', quality=95, subsampling=0,
                                   progressive=False, optimize=False)
            images[name] = encoded.getvalue()
    files, records = {}, {}
    for name, source in targets().items():
        data = images[source]
        files[name] = data
        records[name] = {'source': source, 'size': len(data),
                       'sha256': hashlib.sha256(data).hexdigest()}
    audit = {'schema': 1, 'dimensions': [1672, 941], 'encoding': 'baseline RGB JPEG',
             'sources': source_hashes, 'files': records}
    return files, audit


def generate(output, art=ART):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory; never write into a client.')
    files, audit = loading_files(art)
    output.mkdir(parents=True)
    for name, data in files.items():
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    (output / 'loading-screens.json').write_text(json.dumps(audit, indent=2)+'\n')
    return audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit = generate(args.output)
    print(json.dumps({'files': len(audit['files']), 'artworks': len(audit['sources']),
                      'bytes': sum(f['size'] for f in audit['files'].values())}))
