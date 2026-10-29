"""Door content policy and guarded migration regressions."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from keyless_doors import generate, plan


def fixture():
    return {'doors': [dict(id=i + 1, zone=zone, version=version,
                          keyitem=key, lockpick=pick, guild=guild,
                          triggertype=trigger, dest_zone='target', nokeyring=1)
                      for i, (zone, version, key, pick, guild, trigger) in enumerate([
                          ('befallen', 0, 123, 200, 0, 0),
                          ('paineel', 0, 6378, 0, 0, 0),
                          ('hole', 1, 0, 60, 0, 0),
                          ('other', -1, 456, -1, 7, 255),
                          ('free', 0, 0, 0, 0, 0)])]}


class KeylessDoorsTests(unittest.TestCase):
    def test_every_zone_and_version_loses_both_lock_fields_only(self):
        before = fixture()
        saved = copy.deepcopy(before)
        after = plan(before)
        self.assertEqual(before, saved)
        for old, new in zip(before['doors'], after['doors']):
            self.assertEqual(new, {**old, 'keyitem': 0, 'lockpick': 0})
        self.assertEqual(after['doors'][-1], before['doors'][-1])

    def test_sql_guards_new_locked_rows_and_captured_ids_in_both_directions(self):
        forward, inverse = generate(fixture())
        for sql in (forward, inverse):
            self.assertIn('`keyitem` <> 0 OR `lockpick` <> 0 OR `id` IN (1,2,3,4)', sql)
            self.assertIn('FOR UPDATE', sql)
            self.assertIn('ROLLBACK; RESIGNAL;', sql)
            self.assertNotIn('UPDATE `doors` SET `guild`', sql)
            self.assertNotIn('DELETE FROM', sql)
        self.assertIn('UPDATE `doors` SET `keyitem`=', forward)
        self.assertIn('UPDATE `doors` SET `keyitem`=', inverse)

    def test_already_unlocked_capture_is_a_noop(self):
        self.assertEqual(generate(plan(fixture())), ('-- No locked doors.\n',) * 2)

    def test_duplicate_ids_and_bad_lock_values_reject(self):
        bad = fixture()
        bad['doors'].append(copy.deepcopy(bad['doors'][0]))
        with self.assertRaises(ValueError):
            plan(bad)
        for field in ('id', 'keyitem', 'lockpick'):
            for value in (None, -32769, '0 OR 1=1', True, 2147483648):
                bad = fixture()
                bad['doors'][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    plan(bad)


if __name__ == '__main__':
    unittest.main()
