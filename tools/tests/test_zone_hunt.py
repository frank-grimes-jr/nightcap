import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('zone_hunt', ROOT/'tools/zone_hunt.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog=json.loads((ROOT/'docs/releases/zone-loot-20261009/approved-catalog.json').read_text())

    def test_approved_items_and_probabilities(self):
        items=module.items(self.catalog)
        self.assertEqual(len(items),448)
        self.assertEqual(len({i['id'] for i in items}),448)
        self.assertTrue(all(940000 <= i['id'] < 941000 for i in items))
        self.assertEqual({i['tier'] for i in items},{0,1,2,3})
        self.assertEqual(module.QUALITY,[6000,3000,800,200])
        self.assertEqual(module.FAMILY_CHANCE,50)  # out of 10000
        asc=[i for i in items if i['kind']=='Augment' and i['tier']==3]
        self.assertEqual(max(i['values']['heroic_int'] for i in asc),10)
        self.assertTrue(all(i['values']['slots']==921732 for i in asc))

    def test_native_sources_fail_closed(self):
        z={'zoneidnumber':5,'short_name':'highpass','npc':18,'status':'Access check'}
        n=dict(id='123',npcID='5001',zone='highpass',level='20',name='an_orc',
               version='0',merchant_id='0',**{'class':'1'}, min_expansion='-1',max_expansion='-1',
               content_flags='NULL',content_flags_disabled='NULL',respawntime='360',chance='100',
               bodytype='1',special_abilities='',_condition='0')
        self.assertFalse(module.eligible(z,n,set()))
        z['status']='Hunt draft'
        self.assertTrue(module.eligible(z,n,set()))
        for patch in ({'merchant_id':'2'},{'class':'20'},{'level':'17'},{'version':'1'},
                      {'npcID':'999521'},{'name':'Guard_Bob'},{'min_expansion':'1'},
                      {'name':'an_orc_guard'},{'respawntime':'1'},{'special_abilities':'19,1'}):
            self.assertFalse(module.eligible(z,n|patch,set()),patch)
        self.assertFalse(module.eligible(z,n,{'highpass/an_orc.pl'}))
        self.assertFalse(module.eligible(z,n,{'global/5001.lua'}))

    def test_sockets_preserve_and_limit(self):
        row={'id':'123','slots':'4','reqlevel':'0','reclevel':'0','augtype':'0'}
        row.update({f'augslot{i}type':('7' if i==1 else '0') for i in range(1,7)})
        row.update({f'augslot{i}visible':'1' for i in range(1,7)})
        self.assertEqual(module.socket_change(row,{123})['socket'],2)
        self.assertIsNone(module.socket_change(row,set()))
        self.assertIsNone(module.socket_change(row|{'slots':str(4|32768)},{123}))
        self.assertIsNone(module.socket_change(row|{'augslot2type':'22'},{123}))
        self.assertIsNone(module.socket_change(row|{f'augslot{i}type':'7' for i in range(1,7)},{123}))

if __name__=='__main__': unittest.main()
