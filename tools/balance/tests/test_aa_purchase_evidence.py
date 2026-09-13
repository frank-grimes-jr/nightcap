import difflib
import hashlib
from pathlib import Path
import tarfile
import unittest

from aa_purchase_controls import assess, cases
from aa_policy_preflight import read_json
from baseline import validate_cpp_summary


class AAPurchaseEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root / 'docs/balance'

    def test_native_purchase_grant_events_rollback_and_cleanup(self):
        controls = cases(read_json(self.docs / 'gear-source-inputs.json'))
        self.assertEqual(len(controls), 13)
        self.assertEqual(sum(len(c['expected']) for c in controls), 52)
        for phase in ('before', 'after'):
            stem = 'aa-purchase-' + phase
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

    def test_unchanged_rejection_controls_and_same_diagnostic_adapters(self):
        before = read_json(self.docs / 'aa-purchase-before.json.gz')['cases']
        after = read_json(self.docs / 'aa-purchase-after.json.gz')['cases']
        controls = cases(read_json(self.docs / 'gear-source-inputs.json'))
        for case, old, new in zip(controls, before, after):
            if case['expected_before_pass']:
                self.assertEqual(old['report'], new['report'])
                self.assertEqual(old['native_raw_sha256'], new['native_raw_sha256'])
        old = read_json(self.docs / 'aa-purchase-before-build.json')
        new = read_json(self.docs / 'aa-purchase-after-build.json')
        for key in ('harness_sha256', 'runtime_sha256', 'runtime_header_sha256'):
            self.assertEqual(old[key], new[key])

    def test_fresh_build_source_patch_and_evidence_hashes(self):
        checks = read_json(self.docs / 'aa-purchase-build-checks.json')
        full = read_json(self.docs / 'aa-purchase-full-source-manifest.json')
        expected = read_json(self.docs / 'aa-bulk-full-source-manifest.json')
        expected.update(checks['overlay'])
        self.assertEqual(full, expected)
        self.assertEqual(checks['source_files_checked'], 2787)
        self.assertEqual(checks['source_mismatches'], [])
        self.assertEqual(checks['build_exit_code'], 0)
        self.assertEqual(checks['zone_magic'], '7f454c46')
        self.assertGreater(checks['zone_bytes'], 0)
        self.assertEqual(validate_cpp_summary((self.docs / 'aa-purchase-cpp-tests.log').read_text(encoding='utf-8'), checks['cpp_exit_code']), 87)
        originals = read_json(self.docs / 'aa-purchase-original-source-manifest.json')
        build = read_json(self.docs / 'aa-purchase-after-build.json')
        patch = []
        with tarfile.open(self.docs / 'aa-purchase-source.tar.gz') as archive, \
                tarfile.open(self.docs / 'aa-purchase-original-source.tar.gz') as original:
            for path, digest in checks['overlay'].items():
                new = archive.extractfile('server-mods/code/' + path).read()
                old = original.extractfile(path).read()
                self.assertEqual(hashlib.sha256(new).hexdigest(), digest)
                self.assertEqual(hashlib.sha256(old).hexdigest(), originals[path])
                patch.extend(difflib.unified_diff(old.decode().replace('\r\n', '\n').splitlines(True), new.decode().splitlines(True), fromfile='a/' + path, tofile='b/' + path))
            for name, key in [('native_harness.cpp','harness_sha256'), ('native_runtime.cpp','runtime_sha256'), ('native_runtime.h','runtime_header_sha256')]:
                self.assertEqual(hashlib.sha256(archive.extractfile('tools/balance/' + name).read()).hexdigest(), build[key])
        self.assertEqual(''.join(patch), (self.docs / 'aa-purchase-server.patch').read_text(encoding='utf-8'))
        for name, digest in read_json(self.docs / 'aa-purchase-evidence-manifest.json')['files'].items():
            self.assertEqual(hashlib.sha256((self.root / name).read_bytes()).hexdigest(), digest, name)
