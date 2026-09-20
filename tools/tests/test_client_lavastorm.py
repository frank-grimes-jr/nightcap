import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from client_lavastorm import lavastorm_files


class ClassicLavastorm(unittest.TestCase):
    def test_pinned_assets_are_read_only_and_reject_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            client=root/'client';client.mkdir()
            terrain=root/'lavastorm.s3d';terrain.write_bytes(b'classic terrain')
            objects=client/'lavastorm_obj.s3d';objects.write_bytes(b'classic objects')
            data={'lavastorm.s3d':terrain.read_bytes(),'lavastorm_obj.s3d':objects.read_bytes()}
            pins={name:hashlib.sha256(raw).hexdigest() for name,raw in data.items()}
            with patch('client_lavastorm.PINNED',pins):
                self.assertEqual(lavastorm_files(terrain,client),data)
                self.assertEqual(terrain.read_bytes(),data['lavastorm.s3d'])
                self.assertFalse((client/'lavastorm.s3d').exists())
                for path in (terrain,objects):
                    original=path.read_bytes()
                    path.write_bytes(b'changed')
                    with self.assertRaises(ValueError):
                        lavastorm_files(terrain,client)
                    path.write_bytes(original)
                terrain.unlink()
                with self.assertRaises(FileNotFoundError):
                    lavastorm_files(terrain,client)
