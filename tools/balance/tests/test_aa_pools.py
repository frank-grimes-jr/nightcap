import json
import gzip
from pathlib import Path
import unittest

from aa_pool_controls import prepare
from active_aa_controls import verify_encounters


DOCS = Path(__file__).resolve().parents[3] / 'docs' / 'balance'


class AAPoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((DOCS / 'preparation-inputs.json').read_text())
        cls.catalog = json.loads((DOCS / 'native-aa-catalog.json').read_text())
        cls.policy = json.loads((DOCS / 'aa-pool-policy.json').read_text())

    def test_early_core_exhaustion_is_explicit_and_preserves_zero_baseline(self):
        matrix, audit = prepare(self.source, self.catalog, self.policy)
        self.assertEqual(len(matrix['cases']), 54)
        early = [a for a in audit['allocations'] if a['policy'] == 'early_core']
        self.assertEqual([a['budget'] for a in early], [0, 100, 200, 500, 'all'])
        self.assertEqual([a['spent'] for a in early[-3:]], [114, 114, 114])
        self.assertTrue(all(a['pool_exhausted'] for a in early[-3:]))
        zero = next(c for c in self.source['cases'] if c['input']['builds'][0]['aa_stage'] == '0')
        control = next(c for c in matrix['cases'] if c['input']['builds'][0]['aa_stage'] == '0')
        self.assertEqual(control['input']['builds'][0]['aa_rank_ids'], zero['input']['builds'][0]['aa_rank_ids'])

    def test_caps_and_exclusions_cannot_leak_via_prerequisites(self):
        matrix, audit = prepare(self.source, self.catalog, self.policy)
        ranks = {r['rank_id']: r for b in self.catalog['builds'] if b['profile'] == 'war-clr-wiz' for r in b['aa_catalog']}
        policies = {p['id']: p for p in self.policy['policies']}
        for allocation in audit['allocations']:
            policy = policies[allocation['policy']]
            for rid in allocation['rank_ids']:
                rank = ranks[rid]
                self.assertNotIn(rank['ability_id'], policy.get('exclude', []))
                if 'caps' in policy and rid not in audit['comparison_free_rank_ids']:
                    self.assertLessEqual(rank['rank'], policy['caps'][str(rank['ability_id'])])
        for c in matrix['cases']:
            original = next(s for s in self.source['cases'] if s['seed'] == c['seed'] and s['input']['encounter']['npc_id'] == c['input']['encounter']['npc_id'])
            self.assertEqual(c['input']['builds'][0]['equipment'], original['input']['builds'][0]['equipment'])
            self.assertEqual(c['input']['encounter'], original['input']['encounter'])

    def test_dependent_ability_removals_are_reported(self):
        _, audit = prepare(self.source, self.catalog, self.policy)
        frenzy = next(a for a in audit['allocations'] if a['policy'] == 'without_frenzied')
        removed = {r['ability_id']: r for r in frenzy['removed_from_unrestricted']}
        self.assertEqual(set(removed), {308, 452, 6106, 9700, 493})
        self.assertEqual(sum(r['cost'] for r in removed.values()), 174)

    def test_native_pool_reports_and_explicit_actual_spend(self):
        matrix = json.loads((DOCS / 'aa-pool-inputs.json').read_text())
        evidence = json.loads(gzip.decompress((DOCS / 'aa-pool-encounters.json.gz').read_bytes()))
        self.assertEqual(len(verify_encounters(matrix, evidence)), 54)
        for run in evidence['runs']:
            if run['summary']['aa_policy'] == 'early_core' and run['summary']['aa_stage'] in ('200','500','all'):
                self.assertEqual(run['summary']['aa_spent'], 114)


if __name__ == '__main__':
    unittest.main()
