import unittest
from tier_spell_scaling import quality, stamp, scaled_stat, plan, migration_sql

def item(**values):
    return dict(id=199001, Name='Fixture Cap', slots=4, itemclass=0, bagslots=0,
                ac=0, hp=0, mana=0, astr=0, asta=0, adex=0, aagi=0,
                aint=0, awis=0, acha=0, damage=0, delay=0, itemtype=10,
                spelldmg=0, healamt=0, **values)

class TierSpellScaling(unittest.TestCase):
    def test_weak_cloth_does_not_get_endgame_stamp(self):
        cap=item(); cap['ac']=2
        self.assertEqual([stamp(cap, v) for v in (5,12,20)], [0,0,0])

    def test_progression_and_weapons(self):
        base=item(); base.update(hp=50)
        self.assertEqual([stamp(base,v) for v in (5,12,20)], [2,6,10])
        base.update(hp=1000, mana=900)
        self.assertEqual(stamp(base,20),20)
        base=item(); base.update(damage=1,delay=20,itemtype=0)
        self.assertEqual(stamp(base,20),1)
        base.update(damage=100, itemtype=19)
        self.assertEqual(stamp(base,20),20)
        base['itemtype']=10
        self.assertEqual(quality(base),0)

    def test_no_compounding_or_negative_stat_laundering(self):
        base=item(); base.update(hp=-100,mana=-100,ac=-10,aint=-20)
        self.assertEqual(stamp(base,20),0)
        self.assertEqual(scaled_stat(-5,135,20),-5)
        self.assertEqual(scaled_stat(10,135,4),18)
        self.assertEqual(scaled_stat(0,135,4),4)
        base.update(hp=50,mana=50,aint=25,ac=50)
        self.assertEqual(stamp(base,20),10)

    def test_bags_and_non_common_items_are_excluded(self):
        base=item(); base.update(hp=100,bagslots=10)
        self.assertEqual(stamp(base,20),0)
        base.update(bagslots=0,itemclass=1)
        self.assertEqual(stamp(base,20),0)
        base.update(itemclass=0,slots=0)
        self.assertEqual(stamp(base,20),0)

    def test_plan_rejects_collisions_and_emits_exact_two_column_rollback(self):
        base=item(); base['ac']=2
        tier=dict(base,id=799001,Name='Fixture Cap (Ascended)',spelldmg=20,healamt=20)
        rows=plan([base,tier])
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['new'],[0,0])
        self.assertEqual(rows[0]['old'],[20,20])
        sql=migration_sql(rows)
        self.assertIn('ROLLBACK',sql)
        self.assertIn('FOR UPDATE',sql)
        self.assertIn('SIGNAL SQLSTATE',sql)
        self.assertNotIn('DELETE FROM items',sql)
        tier['Name']='Unrelated item'
        with self.assertRaises(ValueError): plan([base,tier])

    def test_plan_rejects_missing_base_duplicate_and_unknown_stats(self):
        base=item(); base['ac']=2
        tier=dict(base,id=799001,Name='Fixture Cap (Ascended)',spelldmg=20,healamt=20)
        with self.assertRaisesRegex(ValueError,'Missing base'): plan([tier])
        with self.assertRaisesRegex(ValueError,'Duplicate'): plan([base,base,tier])
        tier['healamt']=19
        with self.assertRaisesRegex(ValueError,'Unexpected existing'): plan([base,tier])

if __name__=='__main__': unittest.main()
