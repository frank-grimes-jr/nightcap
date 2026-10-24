"""Budget boundaries, unchanged earned identities, and planar click contracts."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import items,existing_items,DUNGEONS
from classic_dungeon_rewards import CLICKS,DESIGNS

class ClassicRewards(unittest.TestCase):
    def test_old_definitions_change_only_magic(self):
        old=existing_items();new=items()[:330]
        self.assertEqual(sum(r['values']['magic']==0 for r in old),220)
        for a,b in zip(old,new):
            a['values']['magic']=1
            self.assertEqual(a,b)

    def test_new_designs_stay_in_their_dungeon_budget(self):
        shared={(r['band'],r['design'],r['quality']):r['values'] for r in items()[:288]}
        names=set()
        for row in items()[330:]:
            v=row['values'];t=shared[row['band'],row['template'],row['quality']]
            names.add(v['Name'])
            for k in ('hp','mana','endur','ac','damage','delay','spelldmg','healamt','bagslots','bagwr'):
                self.assertEqual(v[k],t[k],(v['Name'],k))
            for fields in (('astr','asta','aagi','adex','aint','awis','acha'),('mr','fr','cr','pr','dr')):
                self.assertEqual(sum(v[k] for k in fields),sum(t[k] for k in fields))
            self.assertEqual(v['reclevel'],row['band'])
            self.assertTrue(all(v[k]==0 for k in v if k.startswith('heroic_')))
            for k in ('haste','regen','manaregen','enduranceregen'):self.assertEqual(v[k],0)
            for k in ('proceffect','worneffect','focuseffect'):self.assertEqual(v[k],-1)
        self.assertEqual(len(names),96)
        self.assertEqual(set(DESIGNS),{d[0] for d in DUNGEONS[7:]}|{'chapterhouse','kael'})

    def test_planar_utility_is_equipped_and_tiers_share_cooldown(self):
        data=items()[330:]
        clicks=[r for r in data if r['values']['clickeffect']>0]
        self.assertEqual(len(clicks),6)
        for key,(spell,name,reuse,group) in CLICKS.items():
            pair=[r['values'] for r in clicks if (r['source'],r['design'])==key]
            self.assertEqual(len(pair),2)
            for v in pair:
                self.assertEqual((v['clickeffect'],v['clickname'],v['recastdelay'],v['recasttype']),(spell,name,reuse,group))
                self.assertEqual((v['clicktype'],v['clicklevel'],v['clicklevel2'],v['reqlevel']),(4,46,46,46))
                self.assertEqual((v['casttime'],v['casttime_'],v['maxcharges']),(10000,10000,-1))
                self.assertGreaterEqual(100+group,100);self.assertLessEqual(100+group,200)
                self.assertEqual(v['loregroup'],0)
        self.assertEqual(len({r['values']['lore'] for r in data if r['source'] not in ('chapterhouse','kael')}),42)
        self.assertEqual(len({r['values']['lore'] for r in data if r['source']=='chapterhouse'}),3)
        self.assertEqual(len({r['values']['lore'] for r in data if r['source']=='kael'}),3)

if __name__=='__main__':unittest.main()
