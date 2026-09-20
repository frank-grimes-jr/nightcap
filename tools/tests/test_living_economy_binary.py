import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_living_economy_binary import verify_world
from build_living_economy import stage_source, source_fingerprints


class WorldArtifact(unittest.TestCase):
    def test_build_directory_cannot_reuse_stale_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            base=root/'base';base.mkdir()
            overlay=root/'overlay';overlay.mkdir()
            (base/'main.cpp').write_text('base')
            (overlay/'main.cpp').write_text('reviewed')
            out=root/'release'
            source=stage_source(base,overlay,out)
            self.assertEqual((source/'main.cpp').read_text(),'reviewed')
            before=source_fingerprints(source)
            (source/'main.cpp').write_text('changed during build')
            self.assertNotEqual(source_fingerprints(source),before)
            with self.assertRaises(FileExistsError):
                stage_source(base,overlay,out)
            self.assertEqual((source/'main.cpp').read_text(),'changed during build')

    def test_current_contract(self):
        verify_world(b'\x7fELF\x00CALL nightcap_market_rotate({},{},{})\x00')

    def test_stale_and_missing_contracts(self):
        for data in (
            b'\x7fELF\x00CALL nightcap_market_rotate({})\x00',
            b'\x7fELF\x00unrelated world',
            b'CALL nightcap_market_rotate({},{},{})\x00',
            b'\x7fELF\x00CALL nightcap_market_rotate({},{},{})\x00CALL nightcap_market_rotate({})\x00',
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                verify_world(data)
