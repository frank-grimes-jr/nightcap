import difflib
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import unittest


class ServerCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.package = cls.root / 'docs/releases/server-fixes-20260913'
        cls.manifest = json.loads((cls.package / 'source-manifest.json').read_bytes())

    def test_exact_original_and_candidate_source_hashes_match_all_five_files(self):
        expected = {'zone/' + n + '.cpp' for n in ('spells', 'attack', 'mob', 'client_packet', 'aa')}
        self.assertEqual({r['path'] for r in self.manifest['files']}, expected)
        with tarfile.open(self.package / 'original-source.tar.gz') as archive:
            self.assertEqual(set(archive.getnames()), expected)
            for row in self.manifest['files']:
                original = archive.extractfile(row['path']).read()
                candidate = (self.root / 'server-mods/code' / row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(original).hexdigest(), row['original_sha256'])
                self.assertEqual(hashlib.sha256(candidate).hexdigest(), row['candidate_sha256'])

    def test_review_patch_reproduces_exact_normalized_source_changes(self):
        patch = []
        with tarfile.open(self.package / 'original-source.tar.gz') as archive:
            for row in self.manifest['files']:
                original = archive.extractfile(row['path']).read().decode().replace('\r\n', '\n')
                candidate = (self.root / 'server-mods/code' / row['path']).read_text(encoding='utf-8')
                patch.extend(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True),
                                                 fromfile='a/' + row['path'], tofile='b/' + row['path']))
        self.assertEqual(''.join(patch), (self.package / 'server-fixes.patch').read_text(encoding='utf-8'))

    def test_fresh_build_replays_match_all_24_pinned_native_reports(self):
        checks = json.loads((self.package / 'fresh-replay-checks.json').read_bytes())
        build = json.loads((self.package / 'build-checks.json').read_bytes())
        self.assertEqual(build['source_files_checked'], 2787)
        self.assertEqual(build['source_mismatches'], [])
        self.assertEqual(build['build_exit_code'], 0)
        self.assertEqual(build['cpp_tests_passed'], 87)
        self.assertGreater(build['zone_bytes'], 0)
        self.assertEqual(build['zone_magic'], '7f454c46')
        self.assertEqual(len(build['zone_sha256']), 64)
        sources = json.loads((self.package / 'full-source-manifest.json').read_bytes())
        for row in self.manifest['files']:
            self.assertEqual(sources[row['path']], row['candidate_sha256'])
        manifest = json.loads((self.package / 'diagnostic-build-manifest.json').read_bytes())
        self.assertEqual(checks['binary_sha256'], manifest['binary_sha256'])
        self.assertEqual([b['kind'] for b in checks['batches']], ['regression', 'source-regression'])
        for batch in checks['batches']:
            kind = batch['kind']
            actual_raw = (self.package / ('fresh-' + kind + '.json.gz')).read_bytes()
            reference_raw = (self.root / 'docs/balance' / ('aa-ownership-' + kind + '.json.gz')).read_bytes()
            self.assertEqual(hashlib.sha256(actual_raw).hexdigest(), batch['actual_sha256'])
            self.assertEqual(hashlib.sha256(reference_raw).hexdigest(), batch['reference_sha256'])
            actual = json.loads(gzip.decompress(actual_raw))['runs']
            reference = json.loads(gzip.decompress(reference_raw))['runs']
            self.assertEqual(len(actual), 12)
            self.assertEqual(len({r['id'] for r in actual}), 12)
            self.assertEqual(actual, reference)
            self.assertTrue(batch['complete_reports_and_raw_hashes_equal'])
            self.assertEqual(batch['differences'], [])


if __name__ == '__main__':
    unittest.main()
