import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('zone_hunt_rates', ROOT/'tools/zone_hunt_rates.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RateTests(unittest.TestCase):
    def setUp(self):
        catalog=json.loads((ROOT/'docs/releases/zone-loot-20261009/approved-catalog.json').read_text(encoding='utf-8'))
        self.known=module.zones(catalog)
        self.config=json.loads((ROOT/'config/zone-hunt-rates.json').read_text(encoding='utf-8'))

    def test_every_installed_zone_and_wiki_slug_is_rated(self):
        self.assertEqual(len(self.known),56)  # 48 hunt + 8 access-check rows installed October 9
        self.assertEqual(self.known['hole'],39)
        wiki=json.loads((ROOT/'wiki/catalog.json').read_text(encoding='utf-8'))
        self.assertLessEqual({z['slug'] for z in wiki['zones']},set(self.known))
        sql=module.sql(self.config,self.known)
        self.assertEqual(sql.count(' UPDATE '),56)
        self.assertIn('augment_chance=150, gear_chance=50 WHERE zone_id=39;',sql)
        self.assertLess(sql.index('ALTER TABLE'),sql.index('START TRANSACTION'))

    def test_overrides_merge_and_invalid_values_fail(self):
        c={'default':{'augment_chance':150,'gear_chance':50},'zones':{'hole':{'augment_chance':300}}}
        self.assertEqual(module.rates(c,self.known)['hole'],{'augment_chance':300,'gear_chance':50})
        for bad in ({'nowhere':{}},{'hole':{'augment_chance':10001}},{'hole':{'augment_chance':-1}},
                    {'hole':{'augment_chance':1.5}},{'hole':{'augment_chance':True}},{'hole':{'typo_chance':5}}):
            with self.assertRaises(ValueError,msg=bad):
                module.rates({**c,'zones':bad},self.known)

    def test_committed_sql_matches_config(self):
        committed=(ROOT/'docs/releases/zone-hunt-rates-20261101/rates.sql').read_text(encoding='utf-8')
        self.assertEqual(committed,module.sql(self.config,self.known))

if __name__=='__main__':
    unittest.main()
