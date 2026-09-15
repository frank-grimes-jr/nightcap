import difflib
import hashlib
from pathlib import Path
import tarfile
import unittest

from aa_bulk_controls import assess, cases
from aa_policy_preflight import read_json
from baseline import validate_cpp_summary


class AABulkEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root / 'docs/balance'

    def test_eleven_native_controls_and_clean_fixture_restoration(self):
        controls = cases(read_json(self.docs / 'gear-source-inputs.json'))
        for phase in ('before', 'after'):
            stem = 'aa-bulk-' + phase
            self.assertEqual(read_json(self.docs / (stem + '-inputs.json'))['cases'], controls)
            result = read_json(self.docs / (stem + '.json.gz'))
            self.assertEqual(result['binary_sha256'], read_json(self.docs / (stem + '-build.json'))['binary_sha256'])
            self.assertEqual([r['id'] for r in result['cases']], [c['id'] for c in controls])
            for case, native in zip(controls, result['cases']):
                self.assertEqual(assess(case, native['report']), native['assessment'])
                self.assertEqual(native['assessment']['passed'], phase == 'after' or case['expected_before_pass'])
            self.assertTrue(result['final']['full_catalog_unchanged'])
            self.assertEqual(result['final']['remaining_rows'], {
                'account': 0, 'character_data': 0, 'character_alternate_abilities': 0, 'inventory': 0})
            self.assertEqual(result['final']['failure_trigger_remaining'], 0)

    def test_valid_profile_and_previous_removal_reports_are_unchanged(self):
        before = read_json(self.docs / 'aa-bulk-before.json.gz')['cases']
        after = read_json(self.docs / 'aa-bulk-after.json.gz')['cases']
        controls = cases(read_json(self.docs / 'gear-source-inputs.json'))
        for case, old, new in zip(controls, before, after):
            if case['expected_before_pass']:
                self.assertEqual(old['report'], new['report'])
                self.assertEqual(old['native_raw_sha256'], new['native_raw_sha256'])
        snapshot = read_json(self.docs / 'aa-policy-snapshot.json.gz')
        ability = next(a for a in snapshot['abilities'] if a['first_rank_id'] == 5006)
        rank = next(r for r in snapshot['ranks'] if r['id'] == 5006)
        self.assertEqual((ability['grant_only'], rank['cost'], rank['expansion']), (1, 0, 0))

    def test_archived_source_and_fresh_build_provenance(self):
        checks = read_json(self.docs / 'aa-bulk-build-checks.json')
        build = read_json(self.docs / 'aa-bulk-after-build.json')
        self.assertEqual(checks['source_files_checked'], 2787)
        self.assertEqual(checks['source_mismatches'], [])
        self.assertEqual(checks['build_exit_code'], 0)
        self.assertEqual(checks['reload_guard_build_exit_code'], 0)
        self.assertEqual(checks['feedback_build_exit_code'], 0)
        self.assertEqual(checks['zone_magic'], '7f454c46')
        self.assertGreater(checks['zone_bytes'], 0)
        self.assertEqual(validate_cpp_summary((self.docs / 'aa-bulk-cpp-tests.log').read_text(encoding='utf-8'), checks['cpp_exit_code']), 87)
        patch = []
        originals = read_json(self.docs / 'aa-bulk-original-source-manifest.json')
        with tarfile.open(self.docs / 'aa-bulk-source.tar.gz') as archive, \
                tarfile.open(self.docs / 'aa-bulk-original-source.tar.gz') as original:
            for path, digest in checks['overlay'].items():
                candidate = archive.extractfile('server-mods/code/' + path).read()
                before = original.extractfile(path).read()
                self.assertEqual(hashlib.sha256(candidate).hexdigest(), digest)
                self.assertEqual(hashlib.sha256(before).hexdigest(), originals[path])
                patch.extend(difflib.unified_diff(before.decode().replace('\r\n', '\n').splitlines(True),
                                                 candidate.decode().splitlines(True), fromfile='a/' + path, tofile='b/' + path))
            self.assertEqual(hashlib.sha256(archive.extractfile('tools/balance/native_harness.cpp').read()).hexdigest(), build['harness_sha256'])
        self.assertEqual(''.join(patch), (self.docs / 'aa-bulk-server.patch').read_text(encoding='utf-8'))
        self.assertEqual(build['harness_sha256'], read_json(self.docs / 'aa-bulk-before-build.json')['harness_sha256'])
        manifest = read_json(self.docs / 'aa-bulk-evidence-manifest.json')
        for path, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.root / path).read_bytes()).hexdigest(), digest, path)
