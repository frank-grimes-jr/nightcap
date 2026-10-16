"""Protect complete build provenance, including versioned shared libraries."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('aa_class_build', ROOT / 'tools/build_aa_class_ranks_candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class LinkFingerprintTests(unittest.TestCase):
    def test_versioned_libraries_objects_and_archives_are_all_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            cwd = base / 'build/zone'
            cwd.mkdir(parents=True)
            for name in ['aa.cpp.o', 'common.a', 'libperl.so.5.36', 'zone']:
                (cwd / name).write_bytes(name.encode())
            command = ['clang++', 'aa.cpp.o', 'common.a', 'libperl.so.5.36', '-pthread', '-o', 'zone']
            with patch.object(build, 'BASE', base):
                result = build.link_inputs(command)
            self.assertEqual(set(result), {str((cwd / n).resolve()) for n in ['aa.cpp.o', 'common.a', 'libperl.so.5.36']})
            self.assertTrue(all(len(value) == 64 for value in result.values()))


if __name__ == '__main__':
    unittest.main()
