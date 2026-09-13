from pathlib import Path
import unittest

from aa_policy_preflight import build_preflight, read_json
from release_pool_controls import allocation_plan


class AAPolicyEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs = Path(__file__).resolve().parents[3] / 'docs/balance'
        cls.snapshot = read_json(docs / 'aa-policy-snapshot.json.gz')
        cls.spec = read_json(docs / 'aa-release-candidates.json')
        cls.catalog = read_json(docs / 'native-aa-catalog.json')
        cls.report = read_json(docs / 'aa-policy-preflight.json')

    def test_stored_report_regenerates_from_full_database_snapshot(self):
        self.assertEqual(build_preflight(self.snapshot, self.spec), self.report)
        self.assertEqual(self.report['source_counts'], {
            'abilities': 1570, 'ranks': 6655, 'prerequisites': 2525, 'purchases': 196})

    def test_every_saved_purchase_is_accounted_for_without_character_identity_join(self):
        identities = {(p['id'], p['aa_id']) for p in self.snapshot['purchases']}
        for policy, counts in zip(self.report['policies'], (
                {'above_cap': 6, 'outside_pool': 163, 'retained': 27},
                {'above_cap': 4, 'outside_pool': 163, 'retained': 29})):
            self.assertEqual(policy['purchase_counts'], counts)
            rows = policy['purchase_impact']
            self.assertEqual(len(rows), len(identities))
            self.assertEqual({(r['character_id'], r['saved_first_rank_id']) for r in rows}, identities)
            self.assertEqual(len(policy['affected_character_ids']), 10)

    def test_compiled_caps_preserve_every_native_calculator_allocation(self):
        pools = {p['id']: set(p['allowed_rank_ids']) for p in self.report['policies']}
        for allocation in allocation_plan(self.catalog, self.spec):
            for alias in allocation['aliases']:
                self.assertLessEqual(set(allocation['rank_ids']), pools[alias['policy']])
        self.assertEqual({k: len(v) for k, v in pools.items()}, {'launch_core': 61, 'later_core': 109})
        self.assertLessEqual(pools['launch_core'], pools['later_core'])
        self.assertTrue(all(p['prerequisites_closed'] for p in self.report['policies']))

    def test_selected_rank_identity_cost_and_dependencies_match_native_catalog(self):
        catalogs = [{r['rank_id']: r for r in b['aa_catalog']} for b in self.catalog['builds']]
        for policy in self.report['policies']:
            for row in policy['ranks']:
                matches = [c[row['rank_id']] for c in catalogs if row['rank_id'] in c]
                self.assertTrue(matches, row['rank_id'])
                for native in matches:
                    for key in ('ability_id', 'rank', 'cost', 'level_req'):
                        self.assertEqual(row[key], native[key])
                    self.assertEqual(row['native_expansion'], native['expansion'])
                    self.assertEqual(row['prerequisites'], [
                        {'ability_id': p['ability_id'], 'ranks': p['ranks']}
                        for p in sorted(native['prereqs'], key=lambda p: p['ability_id'])])


if __name__ == '__main__':
    unittest.main()
