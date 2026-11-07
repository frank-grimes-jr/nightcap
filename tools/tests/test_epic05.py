import copy
import json
from pathlib import Path
import unittest

from epic05 import ROOT, load_catalog, validate, task_rows, spell_rows, migration_sql, client_spells, perl_data, era_eligible


class Epic05Content(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def test_campaign_has_three_shared_chapters_and_five_class_free_paths(self):
        validate(self.catalog)
        tasks, activities = task_rows(self.catalog)
        self.assertEqual(len(tasks), 8)
        self.assertEqual(len(self.catalog['paths']), 5)
        self.assertEqual({p['key'] for p in self.catalog['paths']},
                         {'guardian', 'striker', 'arcanist', 'warden', 'binder'})
        self.assertTrue(all(t['repeatable'] == 0 and t['type'] == 2 for t in tasks))
        self.assertTrue(all(not t['reward_id_list'] and not t['cash_reward'] for t in tasks))
        self.assertEqual(len({(a['taskid'], a['activityid']) for a in activities}), len(activities))
        self.assertTrue(all(a['goalcount'] == 1 for a in activities))

    def test_native_numeric_spell_descriptions_are_nonnull(self):
        for row in spell_rows(self.catalog):
            self.assertEqual(row['typedescnum'],0)
            self.assertEqual(row['effectdescnum'],0)

    def test_path_finale_is_after_both_field_objectives(self):
        _, activities = task_rows(self.catalog)
        for path in self.catalog['paths']:
            steps = [a for a in activities if a['taskid'] == path['task']]
            self.assertEqual([a['step'] for a in steps], [0, 0, 1])
            self.assertTrue(all(a['activitytype'] == 2 for a in steps))
            self.assertTrue(all(a['npc_match_list'].isdigit() for a in steps))

    def test_spawn_gates_and_checked_in_content(self):
        snapshot = json.loads((ROOT/'docs/adventure-journal/content-snapshot.json').read_text())
        row = copy.deepcopy(snapshot['npcs'][0])
        self.assertTrue(era_eligible(row))
        for prefix in ('spawn', 'entry'):
            for key, val in [('_min_expansion',4),('_content_flags','future'),('_content_flags_disabled','classic')]:
                broken = dict(row, **{prefix+key:val})
                self.assertFalse(era_eligible(broken))
        for key, val in [('condition',1),('chance',0),('min_time',1),('max_time',1)]:
            self.assertFalse(era_eligible(dict(row, **{key:val})))
        self.assertEqual((ROOT/'docs/adventure-journal/setup.sql').read_text(), migration_sql(self.catalog))
        self.assertEqual((ROOT/'server-mods/plugins/epic05_data.pl').read_text(), perl_data(self.catalog))

    def test_reward_and_spell_ranges_are_safe_and_never_learnable(self):
        self.assertLessEqual(self.catalog['item']['id'], 0xFFFFF)
        for row in spell_rows(self.catalog):
            self.assertLess(row['id'], 45000)
            self.assertTrue(all(row['classes' + str(c)] == 255 for c in range(1, 17)))
            self.assertEqual(row['persistdeath'], 0)
            self.assertEqual(row['not_extendable'], 1)
            self.assertLessEqual(row['buffduration'], 3)

    def test_reject_duplicate_task_and_cross_era_objectives(self):
        broken = copy.deepcopy(self.catalog)
        broken['paths'][0]['task'] = broken['shared'][0]['task']
        with self.assertRaises(ValueError): validate(broken)
        broken = copy.deepcopy(self.catalog)
        broken['paths'][0]['objectives'][0]['era'] = 1
        with self.assertRaises(ValueError): validate(broken)

    def test_setup_is_additive_disabled_and_rejects_occupied_ids(self):
        sql = migration_sql(self.catalog)
        self.assertIn('SIGNAL SQLSTATE', sql)
        self.assertIn('ROLLBACK', sql)
        self.assertIn('START TRANSACTION', sql)
        self.assertIn('native_contract', sql)
        self.assertNotIn('REPLACE INTO', sql)
        self.assertNotIn('INSERT IGNORE', sql)
        self.assertNotIn('ON DUPLICATE', sql)
        self.assertNotIn('DELETE FROM', sql)
        self.assertNotIn('UPDATE rule_values', sql)

    def test_client_additions_preserve_existing_bytes_and_are_idempotent(self):
        fields = ['0'] * 237
        fields[0], fields[1] = '1', 'Unrelated Spell'
        source = ('^'.join(fields) + '\r\n').encode('latin1')
        result = client_spells(source, self.catalog)
        self.assertTrue(result.startswith(source))
        self.assertEqual(client_spells(result, self.catalog), result)
        self.assertEqual(len(result.splitlines()), 7)
        self.assertTrue(all(len(line.split(b'^')) == 237 for line in result.splitlines()))

    def test_client_rejects_conflicting_custom_spell_or_malformed_source(self):
        fields = ['0'] * 237
        fields[0], fields[1] = str(self.catalog['invoke_spell']), 'Somebody elses spell'
        with self.assertRaises(ValueError):
            client_spells(('^'.join(fields) + '\n').encode(), self.catalog)
        with self.assertRaises(ValueError): client_spells(b'1^truncated\n', self.catalog)
        with self.assertRaises(ValueError): client_spells(b'', self.catalog)


if __name__ == '__main__':
    unittest.main()
