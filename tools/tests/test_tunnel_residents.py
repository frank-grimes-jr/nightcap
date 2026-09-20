import sys
import json
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_residents import RESIDENTS, RINGS, visual_rows, validate


class TunnelResidents(unittest.TestCase):
    def test_exact_identities_and_roles(self):
        self.assertEqual([r['name'] for r in RESIDENTS],['Sortre_Blackdragon','Camil_Swiftwolf',
            'Rekk_Diver','Nalin_Shadowbane','Trift','Khalure_Ser`Tiras'])
        self.assertEqual([(r['race'],r['class']) for r in RESIDENTS],[(6,1),(5,3),(11,9),(5,3),(1,1),(4,6)])
        self.assertEqual(RESIDENTS[4]['level'],12)
        self.assertEqual(RESIDENTS[0]['weapons'],[5500,5500])
        self.assertEqual(RESIDENTS[1]['weapons'],[5403,9004])
        self.assertEqual(RESIDENTS[2]['weapons'],[7001,7001])
        self.assertEqual(RESIDENTS[3]['weapons'],[5504,0])
        self.assertEqual(RESIDENTS[5]['armor'][-1],4407)

    def test_armor_and_black_chain_are_persistent_not_loot(self):
        items={item:{'id':item,'material':3,'color':0xFFABCDEF,'idfile':'IT87'}
               for r in RESIDENTS for item in r['armor']+r['weapons'] if item}
        for r in RESIDENTS:
            npc,tint=visual_rows(r,items)
            self.assertEqual(npc['loottable_id'],0)
            self.assertEqual(npc['skip_global_loot'],1)
            self.assertEqual(npc['merchant_id'],0)
            self.assertEqual(npc['armortint_id'],r['id'])
            self.assertEqual(npc['d_melee_texture2'],87 if r['weapons'][1] else 0)
            if r['name']=='Rekk_Diver':
                self.assertEqual(npc['texture'],2)
                self.assertEqual((tint['red2c'],tint['grn2c'],tint['blu2c']),(12,12,12))
            else:
                self.assertEqual(tint['red2c'],0xAB)

    def test_classic_rings_and_later_era_gates(self):
        classic={r['zone'] for r in RINGS if r['era']==0}
        self.assertEqual(classic,{'northkarana','commons','tox','butcher','lavastorm','sro','feerrott','steamfont','misty'})
        self.assertFalse(classic & {'commonlands','toxxulia','southro','mistythicket'})
        by_zone={r['zone']:r for r in RINGS}
        self.assertEqual(by_zone['dreadlands']['era'],1)
        self.assertEqual(by_zone['qrg']['era'],2)
        self.assertEqual((by_zone['commons']['x'],by_zone['commons']['y']),(1427,478))

    def test_reject_invalid_catalog(self):
        validate(RESIDENTS,RINGS)
        with self.assertRaises(ValueError): validate(RESIDENTS+[RESIDENTS[0]],RINGS)
        with self.assertRaises(ValueError): validate(RESIDENTS,[{**RINGS[0],'era':-1}])

    def test_generated_rollback_matches_fixed_precision_and_rejects_tint_references(self):
        package=Path(__file__).resolve().parents[2]/'docs/economy/residents'
        source=json.loads((package/'source.json').read_text())
        for spawn in source['after']['spawn2']:
            for field in ('x','y','z','heading'):
                self.assertRegex(spawn[field],r'^-?\d+\.\d{6}$')
        sql=(package/'forward.sql').read_text()
        self.assertIn('FROM npc_types WHERE armortint_id BETWEEN 999520 AND 999525 FOR UPDATE',sql)
        self.assertIn("COLUMN_TYPE='float(14,6)'",sql)

if __name__=='__main__': unittest.main()
