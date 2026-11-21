import json,unittest
from catalog import HERE,FIELDS,changes,generate
from analyze import load
from coverage import routes as active

class CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load();cls.targets=changes()
    def test_targets_are_existing_active_stock_drops_at_all_qualities(self):
        routes={r['item'] for r in active(self.data)}
        bases={key%200000 for key in self.targets}
        self.assertEqual(len(bases),119);self.assertEqual(len(self.targets),476)
        self.assertTrue(bases<=routes)
        for key,(r,old,new) in self.targets.items():
            changed={f for f,a,b in zip(FIELDS,old,new) if a!=b}
            self.assertTrue(changed and changed<={'focuseffect','focustype','worneffect','worntype'})
            if old[4:]!=new[4:]:self.assertEqual(old[4:],(-1,0,0,0));self.assertEqual(new[5:],(6,0,0))
            if old[:4]!=new[:4]:self.assertIn(old[:4],((-1,0,0,0),(0,0,0,0)));self.assertEqual(new[1:4],(2,0,0))
            self.assertLess(key,800000);self.assertEqual(r['augtype'],0)
    def test_stock_magnitudes_and_limits_remain_intact(self):
        spells={r['id']:r for r in self.data['spells']}
        for _,(_,old,new) in self.targets.items():
            if old[4:]==new[4:]:continue
            s=spells[new[4]];kind=s['effectid1']
            self.assertIn(kind,(125,127,132))
            self.assertEqual(s['effect_base_value1'] if kind==127 else s['effect_limit_value1'],{125:20,127:15,132:10}[kind])
            self.assertIn(s['effect_base_value2'],(20,44,60))
        for sid,minimum in ((2339,1000),(2340,2000),(2341,3000)):
            s=spells[sid]
            self.assertIn((143,minimum),[(s['effectid'+str(i)],s['effect_base_value'+str(i)]) for i in range(1,13)])
    def test_guarded_migration_only_assigns_focus_fields(self):
        for action in ('forward','rollback'):
            sql=generate(action)
            updates=[line for line in sql.splitlines() if line.startswith('UPDATE ')]
            self.assertEqual(len(updates),476)
            for line in updates:
                assigned=line.split(' SET ',1)[1].split(' WHERE ',1)[0]
                self.assertTrue(set(p.split('=')[0] for p in assigned.split(','))<={'`focuseffect`','`focustype`','`worneffect`','`worntype`'})
                for column in ('Name','classes','slots','clickeffect','proceffect','augslot1type','hp','mana'):
                    self.assertIn('`'+column+'` <=> ',line)
        self.assertNotIn('UPDATE ',generate('verify'))
        self.assertNotIn('UPDATE ',generate('before'))
        with self.assertRaises(ValueError):generate('anything_else')

    def test_defensive_magnitudes_and_legal_loadout_budget(self):
        expected={3889:[(174,10)],3892:[(175,8),(188,8)],2686:[(0,1)],2687:[(0,2)],2688:[(0,3)],1298:[(15,1)],1299:[(15,2)],1300:[(15,3)]}
        spells={r['id']:r for r in self.data['spells']}
        for _,(row,old,new) in self.targets.items():
            if old[:4]==new[:4]:continue
            s=spells[new[0]]
            actual=[(s['effectid'+str(i)],s['effect_base_value'+str(i)]) for i in range(1,13) if s['effectid'+str(i)]!=254 and (s['effectid'+str(i)]!=10 or s['effect_base_value'+str(i)]!=0)]
            self.assertEqual(actual,expected[new[0]])
            if new[0] in (2686,2687,2688):self.assertEqual(row['slots'],1<<2)
            if new[0] in (1298,1299,1300):self.assertEqual(row['slots'],1<<19)
            for i in range(1,13):
                if s['effectid'+str(i)] not in (254,10):self.assertEqual(s['formula'+str(i)],100)

if __name__=='__main__':unittest.main()
