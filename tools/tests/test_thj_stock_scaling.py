import unittest
import thj_stock_scaling as s
class StockScaling(unittest.TestCase):
    def test_all_observed_fields_and_progression(self):
        for base_id,observed in s.observed().items():
            base=s.stock().get(base_id) or s.thj_item_parity.snapshot()[base_id];top=s.top_target(base)
            for field,value in observed['fields'].items():self.assertEqual(top[field],value,(base_id,field))
            for tier in (1,2):
                target=s.tier_target(base,tier)
                for field,value in target.items():self.assertGreaterEqual(value,int(base[field]));self.assertLessEqual(value,top[field])
    def test_unobserved_stock_preserves_sparse_fields_and_negative_penalties(self):
        base=dict(next(iter(s.stock().values())));base.update(id=199999,astr=-5,aint=10,awis=30,adex=5,spelldmg=0,healamt=0,accuracy=0,haste=21,attack=17,endur=33)
        top=s.top_target(base)
        self.assertEqual((top['astr'],top['spelldmg'],top['healamt'],top['accuracy'],top['haste'],top['attack'],top['endur']),(-5,30,60,3,32,17,33))
        self.assertEqual(s.tier_target(base,1)['heroic_wis'],base['heroic_wis'])
    def test_native_stat_bounds_reject_overflow(self):
        base=dict(next(iter(s.stock().values())));base.update(id=199999,astr=64)
        with self.assertRaisesRegex(ValueError,'overflow'):s.top_target(base)
        base['astr']=63;self.assertEqual(s.top_target(base)['astr'],126)
    def test_starters_and_unmatched_families_are_excluded(self):
        self.assertFalse(s.starter_retune.APPROVED_IDS & s.stock().keys())
        pairs,audit=s.plan({});self.assertFalse(pairs);self.assertEqual(len(audit['excluded_families']),len(s.stock().keys()-s.EPICS))
    def test_full_row_effect_and_socket_preservation_and_custom_normal_exclusion(self):
        base=dict(next(iter(s.stock().values())));ident=base['id'];current={ident:dict(base)}
        for offset,label,_ in s.TIERS:current[ident+offset]=dict(base,id=ident+offset,Name=base['Name']+' ('+label+')',focuseffect=43200,augslot1type=7)
        pairs,audit=s.plan(current)
        for old,new in pairs:self.assertEqual(new['focuseffect'],43200);self.assertEqual(new['augslot1type'],7)
        self.assertEqual(current[ident],base)
        current[ident]['hp']+=1
        self.assertFalse(s.plan(current)[0])
if __name__=='__main__':unittest.main()
