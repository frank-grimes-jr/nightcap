import hashlib
from pathlib import Path
import tarfile
import unittest

from aa_removal_controls import assess, cases
from aa_policy_preflight import read_json
from baseline import validate_cpp_summary


class AARemovalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root / 'docs/balance'

    def test_native_before_failures_and_after_acceptance_cover_all_four_cases(self):
        controls = cases(read_json(self.docs / 'gear-source-inputs.json'))
        for phase, passes in [('before', False), ('after', True)]:
            stem = 'aa-removal-' + phase
            self.assertEqual(read_json(self.docs / (stem + '-inputs.json'))['cases'], controls)
            result = read_json(self.docs / (stem + '.json.gz'))
            self.assertEqual(result['binary_sha256'], read_json(self.docs / (stem + '-build.json'))['binary_sha256'])
            self.assertEqual([r['id'] for r in result['cases']], [c['id'] for c in controls])
            for case, native in zip(controls, result['cases']):
                self.assertEqual(assess(case, native['report']), native['assessment'])
                self.assertEqual(native['assessment']['passed'], passes)
            self.assertTrue(result['final']['full_catalog_unchanged'])
            self.assertEqual(result['final']['remaining_rows'], {
                'account': 0, 'character_data': 0, 'character_alternate_abilities': 0, 'inventory': 0})
            self.assertEqual(result['final']['failure_trigger_remaining'], 0)

    def test_prior_charge_resurrection_and_inflated_spent_total_are_reproduced(self):
        before = read_json(self.docs / 'aa-removal-before.json.gz')['cases'][2]
        steps = before['report']['aa_ownership_probe']['steps']
        self.assertEqual([s['effective_rank_count'] for s in steps], [1, 0, 0, 1, 0, 0, 1])
        self.assertEqual([s['spent_points'] for s in steps], [8, 11, 11, 11, 14, 14, 14])
        snapshot = read_json(self.docs / 'aa-policy-snapshot.json.gz')
        ranks = {r['id']: r for r in snapshot['ranks']}
        charged = [a for a in snapshot['abilities'] if a['charges'] > 0]
        self.assertTrue(charged)
        # In this captured full catalog each charged family has one rank/charge;
        # preserving native rank cost therefore also preserves its full cost.
        for ability in charged:
            self.assertEqual(ability['charges'], 1)
            self.assertEqual(ranks[ability['first_rank_id']]['next_id'], -1)

    def test_archived_source_and_fresh_build_provenance(self):
        checks = read_json(self.docs / 'aa-removal-build-checks.json')
        build = read_json(self.docs / 'aa-removal-after-build.json')
        self.assertEqual(checks['source_files_checked'], 2787)
        self.assertEqual(checks['source_mismatches'], [])
        self.assertEqual(checks['build_exit_code'], 0)
        self.assertEqual(checks['zone_magic'], '7f454c46')
        self.assertGreater(checks['zone_bytes'], 0)
        log = (self.docs / 'aa-removal-cpp-tests.log').read_text(encoding='utf-8')
        self.assertEqual(validate_cpp_summary(log, checks['cpp_exit_code']), 87)
        with tarfile.open(self.docs / 'aa-removal-source.tar.gz') as archive:
            for path, digest in checks['overlay'].items():
                self.assertEqual(hashlib.sha256(archive.extractfile('server-mods/code/' + path).read()).hexdigest(), digest)
            self.assertEqual(hashlib.sha256(archive.extractfile('tools/balance/native_harness.cpp').read()).hexdigest(), build['harness_sha256'])
        self.assertEqual(build['harness_sha256'], read_json(self.docs / 'aa-removal-before-build.json')['harness_sha256'])
        manifest = read_json(self.docs / 'aa-removal-evidence-manifest.json')
        for path, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.root / path).read_bytes()).hexdigest(), digest, path)
