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
            self.assertEqual([self.by_key[aid, n]['level'] for n in (1, 2, 3)], [1, 20, 30])
            self.assertNotIn((aid, 4), self.by_key)
        self.assertEqual({r['ability_id'] for r in self.rows if r['expansion'] > 13}, set(self.config['later_exceptions']))
        for aid in self.config['deferred_abilities']:
            self.assertFalse(any(a == aid for a, _ in self.by_key))

    def test_pet_control_and_shallow_defense(self):
        self.assertEqual(self.by_key[3202, 1]['level'], 20)
        self.assertEqual(self.by_key[195, 3]['level'], 20)
        for aid in (3512, 3818):
            self.assertEqual([self.by_key[aid, n]['level'] for n in (1, 2, 3)], [30, 40, 50])
        self.assertEqual(self.by_key[1403, 1]['level'], 50)
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

    def test_generated_header_is_current(self):
        self.assertEqual((ROOT / 'server-mods/code/common/nightcap_aa_policy.h').read_text(), policy.header(self.rows, self.config, self.catalog))


if __name__ == '__main__':
    unittest.main()
