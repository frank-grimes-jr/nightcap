"""Known screenshot values and progression/property contracts."""
import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from thj_item_parity import catalog, snapshot, propose

class ParityItems(unittest.TestCase):
    def test_clean_screenshot_targets_and_reductions(self):
        before=snapshot(); after=propose(before)
        self.assertEqual([after[607869][f] for f in ('ac','hp','mana','endur','spelldmg','healamt')],[150,250,250,125,40,40])
        self.assertEqual([after[628926][f] for f in ('hp','mana','spelldmg','healamt')],[250,150,12,12])
        self.assertEqual([after[640035][f] for f in ('damage','delay','hp','mana','endur')],[80,44,60,50,25])
        self.assertEqual([after[626766][f] for f in ('hp','mana','haste','attack','accuracy')],[200,200,62,15,8])
        self.assertEqual(after[805532]['damage'],40)
        self.assertEqual(after[805532]['proceffect'],before[805532]['proceffect'])
        self.assertEqual([after[608364]['heroic_'+f] for f in ('str','sta','agi','dex','int','wis','cha')],[8]*7)
        self.assertEqual([after[626549][f] for f in ('astr','asta','heroic_str','heroic_sta')],[0,40,0,10])
    def test_no_new_stat_regressions_against_normal_or_lower_tiers(self):
        before=snapshot();after=propose(before)
        for target in catalog()['items']:
            for field,value in target['fields'].items():
                if field in ('delay','range'):continue
                self.assertGreaterEqual(value,before[target['base_id']][field],(target['id'],field))
                for offset in (200000,400000):
                    row=after.get(target['base_id']+offset)
                    if row:self.assertLessEqual(row[field],value,(row['id'],field))
    def test_every_known_field_matches_and_unknowns_survive(self):
        before=snapshot(); original=copy.deepcopy(before); after=propose(before)
        for target in catalog()['items']:
            old=before[target['id']]; new=after[target['id']]
            self.assertTrue(target['evidence'])
            for field,value in target['fields'].items():self.assertEqual(new[field],value,(target['id'],field))
            for field,value in old.items():
                if field not in target['fields']:self.assertEqual(new[field],value,(target['id'],field))
            self.assertEqual(after[target['base_id']],before[target['base_id']])
        self.assertEqual(before,original)
        self.assertEqual(propose(after),after)
    def test_unrelated_pending_effects_and_sockets_survive(self):
        before=snapshot();before[626766]['worneffect']=42840;before[626766]['augslot6type']=8
        after=propose(before)
        self.assertEqual(after[626766]['worneffect'],42840)
        self.assertEqual(after[626766]['augslot6type'],8)
        self.assertNotIn(631224,after) # augmented dagger is not an automatic target
    def test_missing_identity_or_changed_name_fails_closed(self):
        before=snapshot();del before[607869]
        with self.assertRaises(ValueError):propose(before)
        before=snapshot();before[607869]['Name']='Wrong item'
        with self.assertRaises(ValueError):propose(before)

if __name__=='__main__':unittest.main()
