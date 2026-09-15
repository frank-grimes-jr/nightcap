import copy
import json
from pathlib import Path
import unittest

from pok_hub_migration import desired, OLD_NPCS


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs = Path(__file__).resolve().parents[2] / 'docs/pok'
        cls.before = json.loads((docs/'hub-before.json').read_bytes())
        cls.audit = json.loads((docs/'hub-stock-audit.json').read_bytes())

    def test_hub_preserves_appearance_stock_restrictions_and_one_of_each_service(self):
        after = desired(self.before, self.audit)['rows']
        before = self.before['rows']
        self.assertEqual(after['items'], before['items'])
        self.assertEqual(after['rule_values'], before['rule_values'])
        stock = {r['item']:{k:v for k,v in r.items() if k not in ('merchantid','slot')} for r in before['merchantlist']}
        for row in after['merchantlist']:
            self.assertEqual({k:v for k,v in row.items() if k not in ('merchantid','slot')}, stock[row['item']])
        self.assertEqual(len(after['spawn2']),22)  # 16 class merchants + guide + five services
        self.assertEqual(len({s['spawngroupID'] for s in after['spawn2']}),22)
        self.assertEqual(len([n for n in after['npc_types'] if int(n['id']) not in OLD_NPCS]),16)
        for row in after['npc_types']:
            if int(row['id']) not in OLD_NPCS:
                self.assertEqual(row['class'],'41')
                self.assertEqual(row['npc_faction_id'],'0')
                self.assertEqual(row['findable'],'1')

    def test_generation_rejects_conflicts_changed_stock_and_nonidentical_duplicates(self):
        def move_one_duplicate(s):
            next(r for r in s['rows']['spawn2'] if r['id']=='3266043')['respawntime']='60'
        for mutate in (
            lambda s:s['rows']['npc_types'].append(dict(s['rows']['npc_types'][0],id='997900')),
            lambda s:s['rows']['spawn2'].append(dict(s['rows']['spawn2'][0],id='997900')),
            lambda s:s['rows'].update(merchantlist=[r for r in s['rows']['merchantlist'] if r['item']!=s['rows']['merchantlist'][0]['item']]),
            lambda s:s['rows']['items'][0].update(price='99999999'),
            move_one_duplicate,
            lambda s:s['rows']['spawnentry'][0].update(chance='50'),
        ):
            before = copy.deepcopy(self.before)
            mutate(before)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                desired(before,self.audit)


if __name__ == '__main__':
    unittest.main()
