import gzip
import hashlib
import tarfile
from pathlib import Path
import unittest

from aa_owned_core_controls import cases, verify
from aa_owned_view_controls import assess
from aa_policy_preflight import read_json
from baseline import validate_cpp_summary


class EarnedCoreEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root / 'docs/balance'

    def test_all_six_native_controls_preserve_ownership_and_accounting(self):
        inputs = cases(read_json(self.docs / 'gear-source-inputs.json'))
        self.assertEqual(inputs, read_json(self.docs / 'aa-owned-core-inputs.json')['cases'])
        evidence = read_json(self.docs / 'aa-owned-core-native.json.gz')
        self.assertEqual(len(evidence['cases']), 6)
        self.assertEqual([r['id'] for r in evidence['cases']], [c['id'] for c in inputs])
        for case, result in zip(inputs, evidence['cases']):
            self.assertEqual(verify(case, result['report']), result['check'])
        self.assertTrue(all(assess(inputs[0], evidence['cases'][0]['report']).values()))
        self.assertTrue(evidence['final']['full_catalog_unchanged'])
        self.assertEqual(evidence['final']['remaining_rows'], {
            'account': 0, 'character_data': 0, 'character_alternate_abilities': 0, 'inventory': 0})
        before = read_json(self.docs / 'aa-owned-view-before.json.gz')
        self.assertFalse(before['assessment']['usable_prefix_preserved'])
        self.assertFalse(before['assessment']['earned_plus_expended_points_preserved'])

    def test_charged_fixture_matches_the_captured_full_catalog(self):
        snapshot = read_json(self.docs / 'aa-policy-snapshot.json.gz')
        ability = next(a for a in snapshot['abilities'] if a['first_rank_id'] == 4702)
        rank = next(r for r in snapshot['ranks'] if r['id'] == 4702)
        self.assertEqual(ability['charges'], 1)
        self.assertEqual((rank['cost'], rank['expansion'], rank['next_id']), (3, 12, -1))

    def test_fresh_full_build_and_diagnostic_provenance(self):
        build = read_json(self.docs / 'aa-owned-core-build.json')
        checks = read_json(self.docs / 'aa-owned-core-build-checks.json')
        evidence = read_json(self.docs / 'aa-owned-core-native.json.gz')
        self.assertEqual(build['binary_sha256'], evidence['binary_sha256'])
        self.assertEqual(checks['source_files_checked'], 2787)
        self.assertEqual(checks['source_mismatches'], [])
        self.assertEqual(checks['build_exit_code'], 0)
        self.assertEqual(checks['zone_magic'], '7f454c46')
        self.assertGreater(checks['zone_bytes'], 0)
        with tarfile.open(self.docs / 'aa-owned-core-source.tar.gz') as archive:
            for name, digest in checks['overlay'].items():
                data = archive.extractfile('server-mods/code/' + name).read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            for name, key in [('native_harness.cpp', 'harness_sha256'),
                              ('native_runtime.cpp', 'runtime_sha256'),
                              ('native_runtime.h', 'runtime_header_sha256')]:
                data = archive.extractfile('tools/balance/' + name).read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), build[key])
        log = (self.docs / 'aa-owned-core-cpp-tests.log').read_text(encoding='utf-8')
        self.assertEqual(validate_cpp_summary(log, checks['cpp_exit_code']), 87)
        before = read_json(self.docs / 'aa-owned-view-before-build.json')
        old_harness = gzip.decompress((self.docs / 'aa-owned-view-before-harness.cpp.gz').read_bytes())
        self.assertEqual(hashlib.sha256(old_harness).hexdigest(), before['harness_sha256'])
        manifest = read_json(self.docs / 'aa-owned-core-evidence-manifest.json')
        for name, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.root / name).read_bytes()).hexdigest(), digest, name)
