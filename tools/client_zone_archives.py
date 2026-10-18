"""Validate reviewed Classic travel archives before signed client packaging."""
import hashlib
import json
import struct
from pathlib import Path

from classic_model_archives import read_pfs

CATALOG = Path(__file__).resolve().parents[1] / 'assets/client-zone-archives.json'


def zone_files(client, catalog=CATALOG):
    """Read only; never modify the source client or accept unreviewed bytes."""
    spec = json.loads(catalog.read_text())
    if spec['schema'] != 1:
        raise ValueError('Unsupported zone archive catalog')
    files = {}
    for name, entry in spec['files'].items():
        if Path(name).name != name or not name.endswith('.s3d'):
            raise ValueError('Invalid zone archive path')
        data = (client / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Unsupported zone archive: ' + name)
        contents = read_pfs(data)
        world = contents.get(entry['world'], b'')
        if len(world) < 28 or struct.unpack_from('<I', world)[0] != 0x54503d02:
            raise ValueError('Missing or invalid zone world: ' + name)
        files[name] = data
    return files
