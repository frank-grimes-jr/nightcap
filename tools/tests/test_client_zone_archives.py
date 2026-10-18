import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from classic_model_archives import write_pfs
from client_zone_archives import CATALOG, zone_files


class ZoneArchives(unittest.TestCase):
    def test_missing_corrupt_and_wrong_world_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / 'catalog.json'
            archive = root / 'commons.s3d'

            def pin(data):
                catalog.write_text(json.dumps({'schema': 1, 'files': {
                    'commons.s3d': {'sha256': hashlib.sha256(data).hexdigest(), 'world': 'commons.wld'}}}))

            data = write_pfs({'commons.wld': struct.pack('<I', 0x54503d02) + bytes(24)})
            pin(data)
            with self.assertRaises(FileNotFoundError):
                zone_files(root, catalog)
            archive.write_bytes(data)
            self.assertEqual(zone_files(root, catalog), {'commons.s3d': data})
            archive.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
            with self.assertRaisesRegex(ValueError, 'Unsupported zone archive'):
                zone_files(root, catalog)
            wrong = write_pfs({'different.wld': bytes(28)})
            pin(wrong)
            archive.write_bytes(wrong)
            with self.assertRaisesRegex(ValueError, 'zone world'):
                zone_files(root, catalog)

    def test_catalog_covers_audited_routes_and_packager_exactly_once(self):
        root = CATALOG.parents[1]
        spec = json.loads(CATALOG.read_text())['files']
        self.assertEqual(len(spec), 34)
        for zone in ('commons', 'misty', 'tox'):
            self.assertIn(zone + '.s3d', spec)
            self.assertIn(zone + '_obj.s3d', spec)
        source = (root / 'eq-launcher/cmd/nightcap-package/gameplay.go').read_text()
        for name in spec:
            self.assertEqual(source.count('"' + name + '"'), 1, name)


if __name__ == '__main__':
    unittest.main()
