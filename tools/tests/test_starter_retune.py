from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import legacy_items as items
from gear_progression import comparable
from starter_retune import propose


class StarterRetuneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture=json.loads((ROOT/'docs/items/starter-retune-reference.json').read_text(encoding='utf-8'))

    def test_bronze_chest_stays_below_entry_and_endgame(self):
        starter,dungeon=propose(self.capture,items())
        self.assertEqual([starter[4204+t*200000]['ac'] for t in range(4)],[6,7,8,9])
        self.assertEqual([r['values']['ac'] for r in dungeon if r['source']=='completion' and r['design']==1 and r['quality']=='Normal'],[12,16,20,24])

    def test_all_sizes_and_every_comparable_normal_reward_beat_starter_ascended(self):
        starter,dungeon=propose(self.capture,items())
        for family in self.capture['families']:
            asc=starter[family['id']+600000]
            matches=[r['values'] for r in dungeon if r['quality']=='Normal' and comparable(asc,r['values'])]
            self.assertTrue(matches,family['name'])
            for target in matches:
                if asc['damage']:
                    self.assertLess(asc['damage']*target['delay'],target['damage']*asc['delay'])
                else:self.assertLess(asc['ac'],target['ac'])
        self.assertEqual([starter[i]['ac'] for i in (4204,4216,4228)],[6,6,6])

    def test_weapon_damage_increases_every_quality_with_unchanged_delay(self):
        starter,_=propose(self.capture,items())
        for family in self.capture['families']:
            base=family['tiers'][0]
            if not base['damage']:continue
            rows=[starter[base['id']+q*200000] for q in range(4)]
            self.assertEqual([r['damage']-rows[0]['damage'] for r in rows],[0,1,2,3])
            self.assertTrue(all(r['delay']==base['delay'] for r in rows))

    def test_only_explicit_stats_change_and_inputs_are_immutable(self):
        source=items();before=deepcopy((self.capture,source))
        starter,dungeon=propose(self.capture,source)
        self.assertEqual((self.capture,source),before)
        self.assertEqual(len(starter),836)
        allowed={'ac','damage','hp','mana','endur','astr','asta','aagi','adex','aint','awis','acha',
                 'fr','cr','mr','pr','dr','regen','manaregen','enduranceregen','attack','accuracy',
                 'spelldmg','healamt','heroic_str','heroic_sta','heroic_agi','heroic_dex',
                 'heroic_int','heroic_wis','heroic_cha'}
        for family in self.capture['families']:
            for old in family['tiers']:
                self.assertTrue({k for k,v in old.items() if starter[old['id']][k]!=v}<=allowed)
                for key in ('id','Name','classes','races','deity','slots','delay','reqlevel','reclevel','itemtype'):
                    self.assertEqual(starter[old['id']][key],old[key])
        for old,new in zip(source,dungeon):
            self.assertEqual(old.keys(),new.keys())
            self.assertTrue({k for k,v in old['values'].items() if new['values'][k]!=v}<=
                            {'ac','damage','endur','spelldmg','healamt'})
            self.assertEqual({k:v for k,v in old.items() if k!='values'},
                             {k:v for k,v in new.items() if k!='values'})
            if old['values']['itemclass']==1:self.assertEqual(old,new)

    def test_spell_bonuses_and_heroics_are_bounded_on_starter_gear(self):
        starter,_=propose(self.capture,items())
        for row in starter.values():
            self.assertLessEqual(row['spelldmg'],3)
            self.assertLessEqual(row['healamt'],3)
            self.assertTrue(all(v==0 for k,v in row.items() if k.startswith('heroic_')))

    def test_rejects_unknown_profiles_duplicate_ids_and_mismatched_tiers(self):
        for mutation in ('profile','duplicate','name'):
            data=deepcopy(self.capture)
            if mutation=='profile':data['families'][0]['profile']='cultural'
            elif mutation=='duplicate':data['families'].append(deepcopy(data['families'][0]))
            else:data['families'][0]['tiers'][3]['Name']='Other'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):propose(data,items())

    def test_cannot_replace_reviewed_family_with_cultural_armor(self):
        data=deepcopy(self.capture)
        family=data['families'][0]
        family['id']=4427
        family['name']='Dwarven Plate Boots'
        for quality,row in enumerate(family['tiers']):
            row['id']=4427+quality*200000
            row['Name']=family['name']+(' ('+('Normal','Polished','Exalted','Ascended')[quality]+')' if quality else '')
        with self.assertRaises(ValueError):propose(data,items())

    def test_cannot_mislabel_bronze_as_rusty(self):
        data=deepcopy(self.capture)
        next(f for f in data['families'] if f['id']==5027)['profile']='rusty'
        with self.assertRaises(ValueError):propose(data,items())


if __name__=='__main__':unittest.main()
