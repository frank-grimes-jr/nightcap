"""Corruption controls for the native cache verifier; no services accessed."""
import struct
import tempfile
import unittest
from pathlib import Path
import cache_check


class CacheChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'items'
        self.layout = dict(item_size=1332, offsets=dict(ID=440, Races=588))
        self.rows = [[0,0,16448,62219,8192,0], [1,0,65535,65536,8192,0],
                     [2,0,0,1,8192,0], [3,0,64,1,0,1]]

    def fixture(self, enabled=False):
        data = bytearray(20+4*4+1332*4)
        struct.pack_into('<IIII', data, 0, len(data)-8, 4, 4, 4)
        for ident, _, _, races, _, _ in self.rows:
            struct.pack_into('<I', data, 16+ident*4, ident)
            start = 32+ident*1332
            struct.pack_into('<I', data, start+440, ident)
            struct.pack_into('<I', data, start+588, 65535 if enabled and ident in (0,3) else races)
        return data

    def verify(self, data, enabled=False):
        self.path.write_bytes(data)
        return cache_check.verify(self.path, self.rows, self.layout, enabled)

    def test_only_expected_races_can_differ(self):
        old = self.verify(self.fixture())
        new = self.verify(self.fixture(True), True)
        self.assertEqual(old['preserved_fields_sha256'], new['preserved_fields_sha256'])
        self.assertNotEqual(old['cache_sha256'], new['cache_sha256'])
        data = self.fixture(True);data[32+600] = 1
        self.assertNotEqual(new['preserved_fields_sha256'], self.verify(data, True)['preserved_fields_sha256'])

    def test_nonplayer_race_widening_is_rejected(self):
        data = self.fixture(True)
        struct.pack_into('<I', data, 32+1332+588, 65535)
        with self.assertRaises(AssertionError):self.verify(data, True)

    def test_missing_projection_is_rejected(self):
        with self.assertRaises(AssertionError):self.verify(self.fixture(), True)

    def test_lookup_corruption_is_rejected(self):
        data = self.fixture(True);struct.pack_into('<I', data, 16, 1)
        with self.assertRaises(AssertionError):self.verify(data, True)


if __name__ == '__main__':
    unittest.main()
