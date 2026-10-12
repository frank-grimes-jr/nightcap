"""Candidate provenance checks reject changed or unexpected payload members."""
import hashlib
import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('builder', Path(__file__).parents[1] / 'build_item_upgrade_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackageTests(unittest.TestCase):
    def test_payload_drift_and_extras(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in builder.PAYLOADS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode())
            expected = {name: builder.digest(root / name) for name in builder.PAYLOADS}
            builder.verify_payloads(root, expected)
            extra = root / 'sql/unapproved.sql'
            extra.write_text('unexpected')
            with self.assertRaises(AssertionError): builder.verify_payloads(root, expected)
            extra.unlink()
            (root / 'sql/install.sql').write_text('changed')
            with self.assertRaises(AssertionError): builder.verify_payloads(root, expected)

    def test_source_membership_includes_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'expected.cpp').write_text('original')
            before = builder.tree_fingerprints(root)
            (root / 'extra.cpp').write_text('unexpected')
            self.assertNotEqual(builder.tree_fingerprints(root), before)

    def test_archive_members_and_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / 'payload'
            payload.write_bytes(b'expected')
            bundle = root / 'bundle.tar.gz'
            expected = {'payload': hashlib.sha256(b'expected').hexdigest()}
            with tarfile.open(bundle, 'w:gz') as archive: archive.add(payload, arcname='payload')
            builder.verify_archive(bundle, expected)
            with self.assertRaises(AssertionError): builder.verify_archive(bundle, {'payload': 'wrong'})
            with tarfile.open(bundle, 'w:gz') as archive:
                archive.add(payload, arcname='payload')
                archive.add(payload, arcname='extra')
            with self.assertRaises(AssertionError): builder.verify_archive(bundle, expected)


if __name__ == '__main__':
    unittest.main()
