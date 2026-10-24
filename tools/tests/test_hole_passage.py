import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from hole_passage import plan, generate
from pok_hub_migration import sql_value


class HolePassageTests(unittest.TestCase):
    def setUp(self):
        self.capture = json.loads((ROOT / 'docs/ops/hole-keyless-passage-20261024/production-before.json').read_text(encoding='utf-8-sig'))

    def test_only_entrance_locks_change(self):
        original = copy.deepcopy(self.capture)
        after = plan(self.capture)
        changes = [(old['id'], k, old[k], new[k])
                   for old, new in zip(self.capture['doors'], after['doors'])
                   for k in old if old[k] != new[k]]
        self.assertEqual(changes, [(10599, 'lockpick', 60, 0), (10599, 'keyitem', 6379, 0)])
        self.assertEqual(self.capture, original)

    def test_rejects_drift_and_duplicate_or_missing_target(self):
        for field, value in [('keyitem', 6378), ('lockpick', 61), ('name', 'OTHER'), ('zone', 'hole'), ('version', 1), ('doorid', 4), ('guild', 1)]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.capture)
                next(d for d in data['doors'] if d['id'] == 10599)[field] = value
                with self.assertRaises(ValueError):
                    plan(data)
        for doors in [[], self.capture['doors'] * 2]:
            with self.assertRaises(ValueError):
                plan({'doors': doors})

    def test_forward_and_inverse_have_only_one_update(self):
        forward, rollback = generate(self.capture)
        for sql in (forward, rollback):
            self.assertEqual(sql.count('UPDATE `doors`'), 1)
            self.assertNotIn('DELETE FROM', sql)
            self.assertIn('ROLLBACK; RESIGNAL;', sql)
            self.assertIn('FOR UPDATE', sql)
            self.assertIn('TRIGGERS', sql)
        self.assertIn('`keyitem`=' + sql_value(0), forward)
        self.assertIn('`lockpick`=' + sql_value(0), forward)
        self.assertIn('`keyitem`=' + sql_value(6379), rollback)
        self.assertIn('`lockpick`=' + sql_value(60), rollback)


if __name__ == '__main__':
    unittest.main()
