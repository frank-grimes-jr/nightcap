import copy
import gzip
import json
from pathlib import Path
import unittest

from release_pool_controls import summarize, verify


class SharedPoolNativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.matrix = cls.read('release-pool-inputs.json')
        cls.evidence = cls.read('release-pool.json.gz')
        cls.catalog = cls.read('native-aa-catalog.json')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_108_native_fights_reproduce_shared_pool_results(self):
        self.assertEqual(len(verify(self.matrix, self.evidence, self.catalog)), 108)

    def test_clean_zero_baseline_removes_exactly_the_alaraan_hp(self):
        previous = self.read('pet-support-encounter-regression.json.gz')['runs']+self.read('pet-belly.json.gz')['runs']
        old = {r['report']['builds'][0]['profile']: r['report']['builds'][0] for r in previous
               if r['report']['builds'][0]['aa_stage'] == '0'}
        for run in self.evidence['runs']:
            build = run['report']['builds'][0]
            if build['aa_spent'] == 0:
                self.assertEqual(old[build['profile']]['hp']-build['hp'], 20)
                self.assertEqual(old[build['profile']]['mana'], build['mana'])

    def test_no_unlisted_burst_activation_or_wallet_points(self):
        for run in self.evidence['runs']:
            report = run['report']
            self.assertEqual(report['builds'][0]['aa_remaining'], 0)
            actions = (report['pet_probe']['combat']['activated_aa'] if 'pet_probe' in report
                       else report['encounter']['activated_aa']['actions'])
            self.assertEqual(actions, [])

    def test_changed_purchase_and_false_budget_alias_are_rejected(self):
        case = self.matrix['cases'][0]
        report = copy.deepcopy(next(r['report'] for r in self.evidence['runs'] if r['id'] == case['id']))
        report['builds'][0]['aa_purchases'][0]['rank_id'] = 999999
        with self.assertRaises(ValueError):
            summarize(case, report)
        matrix = copy.deepcopy(self.matrix)
        matrix['allocations'][0]['aliases'][0]['pool_exhausted'] = True
        with self.assertRaisesRegex(ValueError, 'budget aliases'):
            verify(matrix, self.evidence, self.catalog)

    def test_missing_or_duplicated_native_case_is_rejected(self):
        for duplicated in (False, True):
            # Only list membership changes; copying every native trace wastes
            # memory and is unrelated to the missing/duplicate identity guard.
            evidence = dict(self.evidence, runs=list(self.evidence['runs']))
            if duplicated:
                evidence['runs'].append(evidence['runs'][0])
            else:
                evidence['runs'].pop()
            with self.assertRaisesRegex(ValueError, 'Incomplete or duplicate'):
                verify(self.matrix, evidence, self.catalog)
            self.assertEqual(len(self.evidence['runs']), 108)


if __name__ == '__main__':
    unittest.main()
