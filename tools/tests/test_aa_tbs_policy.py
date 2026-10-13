import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('aa_tbs_policy', ROOT / 'tools/aa_tbs_policy.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'config/aa-policy.json').read_text())
        cls.catalog = json.loads(gzip.decompress((ROOT / cls.config['catalog']).read_bytes()))
        cls.rows = policy.compile_policy(cls.catalog, cls.config)
        cls.by_key = {(r['ability_id'], r['ordinal']): r for r in cls.rows}

    def test_core_caps_and_exact_later_exceptions(self):
        for aid in (28, 33, 34):
            self.assertEqual([self.by_key[aid, n]['level'] for n in (1, 2, 3)], [1, 1, 1])
            self.assertNotIn((aid, 4), self.by_key)
        self.assertEqual({r['ability_id'] for r in self.rows if r['expansion'] > 13}, set(self.config['later_exceptions']))
        for aid in self.config['deferred_abilities']:
            self.assertFalse(any(a == aid for a, _ in self.by_key))

    def test_pet_control_and_shallow_defense(self):
        self.assertEqual(self.by_key[3202, 1]['level'], 1)
        self.assertEqual(self.by_key[195, 3]['level'], 1)
        for aid in (3512, 3818):
            self.assertEqual([self.by_key[aid, n]['level'] for n in (1, 2, 3)], [1, 1, 1])
        self.assertEqual(self.by_key[1403, 1]['level'], 1)
        self.assertEqual(self.by_key[938, 8]['level'], 1)

    def test_prefix_and_dependency_closure(self):
        for row in self.rows:
            if row['ordinal'] > 1:
                self.assertLessEqual(self.by_key[row['ability_id'], row['ordinal'] - 1]['level'], row['level'])
            for aid, count in row['prereqs'].items():
                self.assertLessEqual(self.by_key[int(aid), count]['level'], row['level'])
        self.assertNotIn((341, 1), self.by_key)

    def test_missing_dependency_and_cycle_fail_closed(self):
        tables = {'aa_ability': [{'id': 1, 'enabled': 1, 'first_rank_id': 10, 'classes': 1}],
                  'aa_ranks': [{'id': 10, 'next_id': -1, 'expansion': 3, 'level_req': 1}],
                  'aa_rank_prereqs': [{'rank_id': 10, 'aa_id': 2, 'points': 1}]}
        self.assertEqual(policy.compile_policy(tables, self.config), [])
        tables['aa_rank_prereqs'] = [{'rank_id': 10, 'aa_id': 1, 'points': 1}]
        self.assertEqual(policy.compile_policy(tables, self.config), [])
        tables['aa_ranks'][0]['next_id'] = 10
        with self.assertRaisesRegex(ValueError, 'cycle'):
            policy.compile_policy(tables, self.config)

    def test_entire_legal_pool_available_at_creation(self):
        self.assertEqual(len(self.rows), 1051)
        self.assertEqual(len({r['ability_id'] for r in self.rows}), 394)
        self.assertEqual({r['level'] for r in self.rows}, {1})
        # Content updates cannot silently restore character-level gating.
        high_levels = json.loads(json.dumps(self.catalog))
        for rank in high_levels['aa_ranks']:
            rank['level_req'] = 255
        self.assertEqual(policy.compile_policy(high_levels, self.config), self.rows)

    def test_reviewed_class_depth_preserves_every_prior_legal_rank(self):
        audited = json.loads((ROOT / 'docs/audits/aa-class-ranks-20261013/candidate-policy.json').read_text())
        self.assertEqual(self.rows, policy.compile_policy(self.catalog, audited))
        prior = json.loads((ROOT / 'docs/audits/aa-class-ranks-20261013/baseline-policy.json').read_text())
        old = policy.compile_policy(self.catalog, prior)
        self.assertEqual(len(old), 941)
        self.assertTrue({r['rank_id'] for r in old} <= {r['rank_id'] for r in self.rows})
        for aid in (359,516,541):
            self.assertFalse(any(a == aid for a,_ in self.by_key))
        self.assertIn((75,9), self.by_key)
        self.assertNotIn((75,10), self.by_key)
        self.assertIn((281,9), self.by_key)

    def test_generated_header_is_current(self):
        self.assertEqual((ROOT / 'server-mods/code/common/nightcap_aa_policy.h').read_text(), policy.header(self.rows, self.config, self.catalog))


if __name__ == '__main__':
    unittest.main()
