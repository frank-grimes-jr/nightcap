"""Reject unrelated changes when widening Guise class masks in the item cache."""
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
import release

class CacheVerification(unittest.TestCase):
    def test_only_class_bytes_may_change(self):
        release.op = SimpleNamespace(
            m={"layout": {"size": 16, "ID": 0, "Classes": 4, "Races": 8}},
            stock={1: None},
            sha=lambda path: "test-digest")
        def cache(classes, other=10):
            header = struct.pack("<IIIIII", 52, 2, 2, 2, 0, 1)
            control = struct.pack("<IIII", 0, 1, 1, other)
            guise = struct.pack("<IIII", 1, classes, 65535, 590)
            return header + control + guise + b"\0" * 4
        with tempfile.TemporaryDirectory() as folder:
            old, new = [Path(folder) / name for name in ("old", "new")]
            old.write_bytes(cache(384))
            new.write_bytes(cache(65535))
            result = release.cache_check(old, new)
            self.assertEqual((result["changed"], result["unchanged"]), (1, 1))
            new.write_bytes(cache(65535, other=11))
            with self.assertRaisesRegex(AssertionError, "Unrelated"):
                release.cache_check(old, new)
            changed = bytearray(cache(65535))
            struct.pack_into("<I", changed, 24 + 16 + 12, 591)
            new.write_bytes(changed)
            with self.assertRaisesRegex(AssertionError, "Unexpected Guise"):
                release.cache_check(old, new)

if __name__ == "__main__":
    unittest.main()
