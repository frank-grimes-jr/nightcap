"""Validate owned migration boundaries before compiling any SQL."""
import copy
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hate_layout_migration as layout


class HateLayoutMigration(unittest.TestCase):
    def setUp(self):
        self.before = dict(scopes=copy.deepcopy(layout.SCOPES), rows={t: [] for t in layout.KEYS})

    def test_reservation_is_additive_and_all_patrols_are_owned(self):
        after = layout.desired(self.before)
        self.assertEqual([len(after['rows'][t]) for t in layout.KEYS], [176, 47, 255])
        sql = layout.patch_sql(self.before, after)
        self.assertNotIn('DELETE FROM', sql)
        self.assertNotIn('UPDATE `', sql)
        self.assertNotIn('`npc_types`', sql)
        self.assertNotIn('`spawn2`', sql)
        self.assertIn('ROLLBACK; RESIGNAL;', sql)

    def test_occupied_or_widened_capture_is_rejected(self):
        for table in layout.KEYS:
            before = copy.deepcopy(self.before)
            before['rows'][table] = [{}]
            with self.assertRaisesRegex(ValueError, 'occupied'):
                layout.desired(before)
        self.before['scopes']['grid'] = 'zoneid=186'
        with self.assertRaisesRegex(ValueError, 'scope drift'):
            layout.desired(self.before)

    def test_patch_cannot_write_outside_owned_scopes(self):
        for table, field, value in [('nightcap_dungeon_spawns', 'zone_id', 76),
                                    ('grid', 'id', 9000), ('grid_entries', 'gridid', 9048)]:
            after = layout.desired(self.before)
            after['rows'][table][0][field] = value
            with self.assertRaisesRegex(ValueError, 'Unowned'):
                layout.patch_sql(self.before, after)

    def test_runtime_checks_preserve_original_respawn_policy(self):
        policies = layout.source_policy()
        self.assertEqual(len(policies), 175)
        self.assertEqual({r['variance'] for r in policies}, {0, 77760})
        checks = [c for c in layout.runtime_checks() if '/original-spawn-policy/' in c['label']]
        self.assertEqual(sum(int(c['expected']) for c in checks), 175)

    def test_encounters_keep_source_identity_and_native_ground_route_evidence(self):
        plan=json.loads((layout.HERE/'population.json').read_text())
        public=json.loads((layout.HERE/'public-source.json').read_text())
        navigation=json.loads((layout.HERE/'navigation.json').read_text())
        original={}
        for row in public['spawn']:
            if row['zone']=='hateplane':original.setdefault(row['id'],[]).append(row)
        routes={r['label']:r for r in navigation['routes']}
        for row in plan['rows']:
            if row['npc_id']==998812:continue
            source=original[row['spawn_id']]
            self.assertTrue(any(r['npc_id']==row['npc_id'] for r in source))
            self.assertEqual({r['group_id'] for r in source},{row['group_id']})
            self.assertEqual({r['respawn'] for r in source},{row['respawn']})
            route=routes[str(plan['mapping'][str(row['spawn_id'])])]
            self.assertEqual(route['to'],[row[k] for k in 'xyz'])
        for route in navigation['routes']+navigation['patrols']:
            self.assertFalse(route['partial'])
            self.assertFalse(route['stuck'])
            self.assertGreater(len(route['points']),1)
            self.assertTrue(all(not p['teleport'] and p['position'][2]<15 for p in route['points']))
        self.assertEqual(routes[str(plan['book_target'])]['to'],[plan['book_pose'][k] for k in 'xyz'])


if __name__ == '__main__':
    unittest.main()
