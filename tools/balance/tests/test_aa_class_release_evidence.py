import hashlib
from pathlib import Path
import tarfile
import unittest

from aa_class_release_controls import cases,assess
from aa_policy_preflight import read_json


class ClassReleaseEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[3]
        cls.docs=cls.root/'docs/balance'

    def test_native_before_failures_are_reproducible_and_clone_is_restored(self):
        controls=cases(read_json(self.docs/'gear-source-inputs.json'))
        self.assertEqual(len(controls),7)
        self.assertEqual(sum(len(c['expected']) for c in controls),36)
        self.assertEqual(read_json(self.docs/'aa-release-before-inputs.json')['cases'],controls)
        result=read_json(self.docs/'aa-release-before.json.gz')
        self.assertEqual([r['id'] for r in result['cases']],[c['id'] for c in controls])
        for case,native in zip(controls,result['cases']):
            self.assertEqual(assess(case,native['report']),native['assessment'])
            self.assertEqual(native['assessment']['passed'],case['expected_before_pass'])
            self.assertTrue(all(not s['client_data_loaded'] for s in native['report']['aa_ownership_probe']['steps']))
        by_id={r['id']:r for r in result['cases']}
        for identity,wallet in [('release-full-earned-wizard',47),('release-partially-usable-wizard',35),('release-suspended-wizard',17)]:
            released=next(s for s in by_id[identity]['report']['aa_ownership_probe']['steps'] if s['operation']=='release_third')
            self.assertEqual(released['earned_rank_count'],6)
            self.assertEqual(released['unspent_points'],wallet)
            self.assertEqual(released['stored'],[{'first_rank_id':267,'rank_count':6,'charges':0}])
        for identity,hits in [('failed-class-write-preserves-entire-character',1),('failed-point-write-preserves-entire-character',0)]:
            step=by_id[identity]['report']['aa_ownership_probe']['steps'][1]
            self.assertEqual(step['injected_release_failures'],hits)
        final=result['final']
        self.assertFalse(any(final['remaining_rows'].values()))
        self.assertTrue(final['catalog_unchanged'] and final['class_values_restored'] and final['skills_unchanged'])
        self.assertEqual(final['failure_trigger_remaining'],0)

    def test_diagnostic_and_evidence_bytes_are_pinned(self):
        build=read_json(self.docs/'aa-release-before-build.json')
        self.assertEqual(build['binary_sha256'],read_json(self.docs/'aa-release-before.json.gz')['binary_sha256'])
        with tarfile.open(self.docs/'aa-release-before-source.tar.gz') as archive:
            for name,key in [('native_harness.cpp','harness_sha256'),('native_runtime.cpp','runtime_sha256'),('native_runtime.h','runtime_header_sha256')]:
                raw=archive.extractfile('tools/balance/'+name).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),build[key])
        manifest=read_json(self.docs/'aa-release-before-evidence-manifest.json')
        for name,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.root/name).read_bytes()).hexdigest(),digest,name)


if __name__=='__main__': unittest.main()
