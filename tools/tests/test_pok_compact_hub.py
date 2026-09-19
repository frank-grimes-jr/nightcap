import copy
import math
import unittest
import pok_compact_hub as hub


def fixture():
    rows = {t: [] for t in hub.KEYS}
    for npc in hub.PLAN:
        rows['npc_types'].append({'id': str(npc), 'race': '14', 'gender': '2', 'size': '6',
                                  'texture': '0', 'helmtexture': '0', 'face': '1', 'merchant_id': str(npc), 'name': 'Unchanged'})
        rows['spawn2'].append({'id': str(npc+100), 'spawngroupID': str(npc), 'zone': 'poknowledge', 'version': '0',
                               'pathgrid': '0', 'x': '100', 'y': '100', 'z': '-158.875000', 'heading': '0'})
        rows['spawngroup'].append({'id': str(npc), 'name': 'Unchanged'})
        rows['spawnentry'].append({'spawngroupID': str(npc), 'npcID': str(npc), 'chance': '100'})
    return {'rows': rows, 'scopes': hub.scopes(), 'schemas': {t: {'create': 'ENGINE=InnoDB'} for t in rows}}


class CompactHub(unittest.TestCase):
    def test_every_service_is_close_and_arrival_is_clear(self):
        points = [(p['x'], p['y']) for p in hub.PLAN.values()]
        self.assertEqual(len(points), 22)
        self.assertEqual(len(set(points)), 22)
        for x, y in points:
            self.assertLessEqual(math.dist((x,y), hub.ARRIVAL), 68)
            self.assertGreaterEqual(math.dist((x,y), hub.ARRIVAL), 12)
        for i, first in enumerate(points):
            for second in points[i+1:]:
                self.assertGreaterEqual(math.dist(first, second), 16)

    def test_only_positions_and_visuals_change(self):
        before = fixture()
        after = hub.desired(before)
        self.assertNotEqual(before['rows']['spawn2'], after['rows']['spawn2'])
        for table in ('merchantlist','spawngroup','spawnentry'):
            self.assertEqual(before['rows'][table], after['rows'][table])
        for old,new in zip(before['rows']['npc_types'], after['rows']['npc_types']):
            self.assertEqual({k:v for k,v in old.items() if k not in hub.VISUAL_FIELDS},
                             {k:v for k,v in new.items() if k not in hub.VISUAL_FIELDS})

    def test_unexpected_spawn_topology_refused(self):
        for mutate in (lambda rows: rows['spawn2'].append(copy.deepcopy(rows['spawn2'][0])),
                       lambda rows: rows['spawn2'][0].update(zone='qeynos'),
                       lambda rows: rows['spawnentry'][0].update(chance='50')):
            snapshot = fixture(); mutate(snapshot['rows'])
            with self.assertRaises(ValueError): hub.desired(snapshot)

    def test_heading_preimages_match_mariadb_float32_storage(self):
        after = hub.desired(fixture())
        headings = {int(row['spawngroupID']):row['heading'] for row in after['rows']['spawn2']}
        for text in headings.values():
            stored = hub.struct.unpack('f',hub.struct.pack('f',float(text)))[0]
            self.assertEqual(text, f'{stored:.6f}')

    def test_saved_state_scope_excludes_corpses_and_other_instances(self):
        snapshot = fixture()
        scope = snapshot['scopes']['zone_state_spawns']
        self.assertIn('zone_id=202 AND instance_id=0 AND is_corpse=0', scope)
        snapshot['rows']['zone_state_spawns'] = [{'id':'7','zone_id':'202','instance_id':'0','is_corpse':'0',
                                                 'npc_id':'999220','spawngroup_id':'999220','spawn2_id':'999320'}]
        after = hub.desired(snapshot)
        self.assertEqual(after['rows']['zone_state_spawns'], [])
        sql = hub.patch_sql(snapshot, after)
        self.assertIn('START TRANSACTION', sql)
        self.assertIn('FOR UPDATE', sql)
        self.assertIn('DELETE FROM `zone_state_spawns`', sql)
        self.assertIn('ROLLBACK;', sql)
        self.assertNotIn('DELETE FROM `merchantlist`', sql)


if __name__ == '__main__': unittest.main()
