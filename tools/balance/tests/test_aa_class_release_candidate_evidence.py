import hashlib
from pathlib import Path
import tarfile
import unittest
from aa_policy_preflight import read_json
from aa_class_release_controls import cases,assess
from aa_class_release_extended import cases as extended_cases,assess as assess_extended

class CandidateReleaseEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[3]
        cls.docs=cls.root/'docs/balance'

    def test_same_skill_inputs_fail_before_and_pass_after(self):
        controls=cases(read_json(self.docs/'gear-source-inputs.json'))
        for c in controls: c['input']['aa_ownership_probe']['load_release_skills']=True
        for phase in ('before','after'):
            stem='aa-release-matched-'+phase
            self.assertEqual(read_json(self.docs/(stem+'-inputs.json'))['cases'],controls)
            evidence=read_json(self.docs/(stem+'.json.gz'))
            build=read_json(self.docs/(stem+'-build.json'))
            self.assertEqual(evidence['binary_sha256'],build['binary_sha256'])
            self.assertEqual(len(evidence['cases']),7)
            for case,run in zip(controls,evidence['cases']):
                self.assertEqual(run['id'],case['id'])
                self.assertEqual(assess(case,run['report']),run['assessment'])
                self.assertEqual(run['assessment']['passed'],phase=='after' or case['expected_before_pass'])
            self.assertTrue(evidence['persisted_skill_fixture'])
            self.assertFalse(any(evidence['final']['remaining_rows'].values()))
            self.assertEqual(evidence['final']['failure_trigger_remaining'],0)
            self.assertTrue(all(evidence['final'][k] for k in ('catalog_unchanged','class_values_restored','skills_unchanged')))

    def test_native_skills_refunds_publication_and_stale_state(self):
        controls=extended_cases(read_json(self.docs/'gear-source-inputs.json'))
        self.assertEqual(read_json(self.docs/'aa-release-extended-inputs.json')['cases'],controls)
        evidence=read_json(self.docs/'aa-release-extended.json.gz')
        self.assertEqual(evidence['binary_sha256'],read_json(self.docs/'aa-release-matched-after-build.json')['binary_sha256'])
        self.assertEqual(len(evidence['cases']),20)
        for case,run in zip(controls,evidence['cases']):
            self.assertEqual(case['id'],run['id'])
            self.assertEqual(assess_extended(case,run['report']),run['assessment'])
            self.assertTrue(run['assessment']['passed'],case['id'])
        self.assertFalse(any(evidence['final']['remaining_rows'].values()))
        self.assertEqual(evidence['final']['failure_trigger_remaining'],0)
        self.assertTrue(all(evidence['final'][k] for k in ('catalog_unchanged','classes_restored','skills_restored')))

    def test_purchases_and_grants_still_commit_before_success(self):
        from aa_purchase_controls import cases as purchase_cases,assess as purchase_assess
        controls=purchase_cases(read_json(self.docs/'gear-source-inputs.json'))
        evidence=read_json(self.docs/'aa-release-purchase-regression.json.gz')
        self.assertEqual(read_json(self.docs/'aa-release-purchase-regression-inputs.json')['cases'],controls)
        self.assertEqual(evidence['binary_sha256'],read_json(self.docs/'aa-release-matched-after-build.json')['binary_sha256'])
        self.assertEqual(len(evidence['cases']),13)
        for case,run in zip(controls,evidence['cases']):
            self.assertEqual(purchase_assess(case,run['report']),run['assessment'])
            self.assertTrue(run['assessment']['passed'],case['id'])
        self.assertFalse(any(evidence['final']['remaining_rows'].values()))
        self.assertTrue(evidence['final']['full_catalog_unchanged'])
        self.assertEqual(evidence['final']['failure_trigger_remaining'],0)

    def test_final_build_and_retained_source_bytes(self):
        manifest=read_json(self.docs/'aa-release-candidate-evidence-manifest.json')
        for name,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((self.root/name).read_bytes()).hexdigest(),digest,name)
        checks=read_json(self.docs/'aa-release-review-build-checks.json')
        self.assertEqual(checks['source_files_checked'],2787)
        self.assertEqual(checks['source_mismatches'],[])
        self.assertEqual(checks['build_exit_code'],0)
        self.assertTrue(read_json(self.docs/'aa-release-verified-cpp-checks.json')['all_passed'])
        final=read_json(self.docs/'aa-release-matched-after-build.json')
        with tarfile.open(self.docs/'aa-release-candidate-source.tar.gz') as bundle:
            for name,key in [('native_harness.cpp','harness_sha256'),('native_runtime.cpp','runtime_sha256'),('native_runtime.h','runtime_header_sha256')]:
                raw=bundle.extractfile('tools/balance/'+name).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),final[key])
            for name,digest in checks['overlay'].items():
                raw=bundle.extractfile('server-mods/code/'+name).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),digest,name)

if __name__=='__main__': unittest.main()
