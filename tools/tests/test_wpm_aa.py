import json
import unittest
import wpm_aa
from aa_tbs_policy import compile_policy


class WPMAA(unittest.TestCase):
    def test_exact_earned_depths_and_dependencies(self):
        config=json.loads((wpm_aa.ROOT/'config/aa-policy.json').read_text())
        rows=compile_policy(wpm_aa.catalog(),config)
        keys={(r['ability_id'],r['ordinal']):r for r in rows}
        for aid,count in wpm_aa.CAPS.items():
            self.assertEqual([n for a,n in keys if a==aid],list(range(1,count+1)),aid)
        self.assertEqual(keys[108,1]['prereqs'][30],3)
        self.assertEqual(keys[131,1]['prereqs'][30],6)
        self.assertEqual(keys[341,6]['prereqs'][30],6)
        self.assertFalse(any(a in (309,914) for a,n in keys))
        self.assertEqual({r['level'] for r in rows},{1})

    def test_no_reassignment_of_existing_aa_ownership_or_costs(self):
        old,new=wpm_aa.baseline(),wpm_aa.catalog()
        for table in ('aa_ability','aa_ranks'):
            by_id={r['id']:r for r in new[table]}
            for row in old[table]:
                after=by_id[row['id']]
                for field in (('id','first_rank_id') if table=='aa_ability' else ('id','cost','prev_id','next_id')):
                    self.assertEqual(row[field],after[field])
        self.assertEqual(next(r for r in old['aa_ability'] if r['id']==914),next(r for r in new['aa_ability'] if r['id']==914))
        self.assertEqual(next(r for r in new['aa_ability'] if r['id']==30200)['classes'],4)

    def test_six_specials_and_no_weapon_skill_bonus(self):
        rows=wpm_aa.catalog()['aa_rank_effects']
        for rank,amount,rate in ((12706,100,30),(12707,200,60)):
            effects=[r for r in rows if r['rank_id']==rank]
            self.assertEqual({r['base2']:r['base1'] for r in effects if r['effect_id']==220},dict.fromkeys(wpm_aa.MONK_SKILLS,amount))
            self.assertEqual([r['base1'] for r in effects if r['effect_id']==428],list(wpm_aa.MONK_SKILLS))
            proc=next(r for r in effects if r['effect_id']==427)
            self.assertEqual((proc['base1'],proc['base2']),(23598,rate))
        self.assertEqual([r['base1'] for r in rows if r['rank_id'] in range(4844,4849)],[20,40,60,80,100])

    def test_client_strings_idempotent_and_unrelated_preserved(self):
        raw=b'100^1^Unrelated\r\n12706^1^Fists of Steel\r\n'
        after=wpm_aa.client_strings(raw)
        self.assertIn(b'100^1^Unrelated\r\n',after)
        self.assertIn(b'12706^1^Way of Steel\r\n',after)
        self.assertEqual(after,wpm_aa.client_strings(after))


if __name__=='__main__':unittest.main()
