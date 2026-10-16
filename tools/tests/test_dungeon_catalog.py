import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import items, DUNGEONS

class DungeonCatalogTests(unittest.TestCase):
    def test_catalog_contract(self):
        data=items()
        self.assertEqual(len(data),330)
        self.assertEqual({x['id'] for x in data},set(range(960000,960330)))
        for row in data:
            i=row['values']
            self.assertLess(i['id'],1048576)
            self.assertLess(len(i['Name']),64)
            for key,value in {'nodrop':1,'norent':1,'attuneable':0,'loregroup':0,'price':0,'sellrate':0}.items():
                self.assertEqual(i[key],value,(i['id'],key))
            if i['itemclass']==1:
                self.assertLessEqual(i['bagslots'],10);self.assertLessEqual(i['bagwr'],100)
                self.assertIn(i['bagslots'],(2,4,6,8,10))
        for start in range(0,288,3):
            family=[x['values'] for x in data[start:start+3]]
            self.assertEqual(len({i.get('delay',0) for i in family}),1)
            for k in ('damage','ac','hp','mana','bagslots','bagwr'):
                values=[i.get(k,0) for i in family]
                self.assertEqual(values,sorted(values))
    def test_boss_exclusives_are_three_designs_and_only_raid_quality(self):
        for dungeon in DUNGEONS:
            data=[r for r in items() if r['source']==dungeon[0]]
            self.assertEqual(len(data),6)
            self.assertEqual({r['quality'] for r in data},{'Polished','Ascended'})
            self.assertEqual({r['design'] for r in data},{0,1,2})
    def test_ct_closure_is_isolated_and_preserves_doors(self):
        donor=json.loads((ROOT/'docs/dungeons/classic-ct.json').read_text())
        a=json.loads((ROOT/'docs/dungeons/classic-ct-adapted.json').read_text())
        self.assertNotIn('spawn2',a['tables']);self.assertNotIn('doors',a['tables'])
        self.assertEqual(len(a['tables']['nightcap_dungeon_spawns']),188)
        self.assertEqual(len(a['roster']),6)
        self.assertEqual(a['roster'][-1]['donor_npc_id'],48500)
        self.assertFalse({r['spellid'] for r in a['tables']['npc_spells_entries']} & {1419,1445,2551,2554})
        avatar=next(n for n in a['tables']['npc_types'] if n['id']==a['roster'][-1]['npc_id'])
        self.assertEqual((avatar['level'],avatar['hp'],avatar['mindmg'],avatar['maxdmg']),(39,3000,16,80))
        native=json.loads((ROOT/'docs/dungeons/local-content.json').read_text())
        native={d['doorid']:d for d in native['doors'] if d['zone']=='cazicthule'}
        for d in donor['doors']:
            for field in ('name','pos_x','pos_y','pos_z','heading','opentype','keyitem','lockpick','dest_zone','triggerdoor'):
                self.assertEqual(d[field],native[d['doorid']][field])

if __name__=='__main__':unittest.main()
