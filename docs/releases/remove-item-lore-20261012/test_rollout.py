import ast
import hashlib
import mmap
from pathlib import Path
import struct
import tempfile
import types
import unittest


class CacheVerificationTests(unittest.TestCase):
    def test_cache_policy_preservation_and_corruption(self):
        tree = ast.parse(Path(__file__).with_name('rollout.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cache')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'data/server/shared/items'
            path.parent.mkdir(parents=True)
            count, n, size = 3, 2, 1332
            start = 16 + count * 4
            data = bytearray(20 + count * 4 + n * size)
            struct.pack_into('<IIII', data, 0, len(data) - 8, count, n, n)
            for index, (item, lore) in enumerate(((1, -1), (2, 1000))):
                struct.pack_into('<I', data, 16 + item * 4, index)
                struct.pack_into('<I', data, start + index * size + 440, item)
                struct.pack_into('<i', data, start + index * size + 464, lore)
                data[start + index * size + 468] = 1
            r = types.SimpleNamespace(ROOT=root, sql=lambda _: '1\t-1\n2\t1000\n')
            namespace = dict(r=r, hashlib=hashlib, mmap=mmap, struct=struct)
            exec(compile(ast.Module(body=[function], type_ignores=[]), 'cache', 'exec'), namespace)
            cache = namespace['cache']
            path.write_bytes(data)
            before = cache(False)
            with self.assertRaises(AssertionError):
                cache(True)
            for index in range(n):
                data[start + index * size + 464:start + index * size + 469] = b'\x00' * 5
            path.write_bytes(data)
            after = cache(True)
            self.assertEqual(after['effective_lore_items'], 0)
            self.assertEqual(before['non_lore_fields_sha256'], after['non_lore_fields_sha256'])
            data[start + 100] = 7  # A non-LORE item field must affect the preservation digest.
            path.write_bytes(data)
            self.assertNotEqual(after['non_lore_fields_sha256'], cache(True)['non_lore_fields_sha256'])
            struct.pack_into('<I', data, start + 440, 999)
            path.write_bytes(data)
            with self.assertRaises(AssertionError):
                cache(True)


if __name__ == '__main__':
    unittest.main()
