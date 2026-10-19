"""Behavioral contracts for the sourced custom AA candidate."""
import unittest
import thj_behavior_content as content
from aa_tbs_policy import compile_policy

class Content(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=content.snapshot()['tables']
        cls.after,cls.policy=content.prepare()
        cls.spells={r['id']:r for r in cls.after['spells_new']}
        cls.abilities={r['id']:r for r in cls.after['aa_ability']}
        cls.ranks={r['id']:r for r in cls.after['aa_ranks']}

    def test_silent_casting_and_retirement(self):
        self.assertEqual(self.abilities[500]['classes'],sum(1<<(n-1) for n in (2,3,4,5,6,8,10,11,12,13,14,15)))
        for rid in range(1404,1409):self.assertEqual(self.ranks[rid]['recast_time'],60)
        for sid in range(8054,8059):
            self.assertEqual((self.spells[sid]['buffdurationformula'],self.spells[sid]['buffduration'],self.spells[sid]['suspendable']),(4,600,1))
        permitted={r['ability_id'] for r in compile_policy(self.after,self.policy)}
        self.assertFalse({25,252,8300}&permitted)
        self.assertIn(500,permitted)

    def test_warrior_behavior_and_short_duration(self):
        s=self.spells[23528]
        self.assertEqual((s['effectid1'],s['effect_base_value1'],s['effect_limit_value1']),(185,100,-1))
        self.assertEqual((s['buffdurationformula'],s['buffduration']),(4,2))
        self.assertEqual(self.ranks[10546]['recast_time'],60)
        gut=self.spells[12802]
        effects=[(gut['effectid'+str(i)],gut['effect_base_value'+str(i)],gut['effect_limit_value'+str(i)]) for i in range(1,13)]
        self.assertIn((197,50,-1),effects)
        self.assertIn((79,-1,0),effects)
        self.assertEqual(gut['buffduration'],2)

    def test_group_valor_and_separate_dimensional_identity(self):
        self.assertEqual(self.spells[2775]['targettype'],41)
        self.assertEqual(self.spells[2775]['effectid1'],79)
        original=next(a for a in self.before['aa_ability'] if a['id']==492)
        self.assertEqual(self.abilities[492],original)
        self.assertEqual(self.abilities[30201]['classes'],2048)
        self.assertEqual(self.abilities[30201]['first_rank_id'],43220)

    def test_explicit_mage_focus_overrides(self):
        for sid,value in ((5915,100),(11064,150)):
            self.assertEqual(self.spells[sid]['effect_base_value1'],value)
            self.assertEqual(self.spells[sid]['effect_limit_value1'],value)

    def test_no_character_rows_or_unrelated_content_in_sql_groups(self):
        groups=content.groups()
        self.assertTrue(groups)
        self.assertTrue({g['table'] for g in groups}<={'spells_new','aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs'})
        self.assertEqual(len(groups),len({(g['table'],tuple(g['key'].items())) for g in groups}))
        for group in groups:
            for row in group['after']:
                self.assertTrue(all(row[k]==v for k,v in group['key'].items()))

    def test_paid_starter_and_existing_rank_prefixes(self):
        for aid in (harm:=600,207,174):
            old=[a for a in self.before['aa_ability'] if a['id']==aid]
            if old:self.assertEqual(old[0],self.abilities[aid])
        for old in self.before['aa_ranks']:
            if old['id'] in self.ranks:self.assertEqual(old['cost'],self.ranks[old['id']]['cost'])

if __name__=='__main__':unittest.main()
