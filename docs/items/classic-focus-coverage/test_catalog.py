import json,unittest
from catalog import HERE,FIELDS,changes,generate
from analyze import load,active

class CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load();cls.targets=changes()
    def test_targets_are_existing_active_stock_drops_at_all_qualities(self):
        routes={r['item'] for r in active(self.data)}
        bases={key%200000 for key in self.targets}
        self.assertEqual(len(bases),19);self.assertEqual(len(self.targets),76)
        self.assertTrue(bases<=routes)
        for key,(r,old,new) in self.targets.items():
            self.assertEqual([f for f,a,b in zip(FIELDS,old,new) if a!=b],['focuseffect','focustype'])
            self.assertEqual(old[4:],(-1,0,0,0));self.assertEqual(new[5:],(6,0,0))
            self.assertLess(key,800000);self.assertEqual(r['augtype'],0)
    def test_stock_magnitudes_and_limits_remain_intact(self):
        spells={r['id']:r for r in self.data['spells']}
        for _,(_,_,new) in self.targets.items():
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
            self.assertEqual(len(updates),76)
            for line in updates:
                assigned=line.split(' SET ',1)[1].split(' WHERE ',1)[0]
                self.assertEqual([p.split('=')[0] for p in assigned.split(',')],['`focuseffect`','`focustype`'])
                for column in ('Name','classes','slots','clickeffect','proceffect','augslot1type','hp','mana'):
                    self.assertIn('`'+column+'` <=> ',line)
        self.assertNotIn('UPDATE ',generate('verify'))
        self.assertNotIn('UPDATE ',generate('before'))
        with self.assertRaises(ValueError):generate('anything_else')

if __name__=='__main__':unittest.main()
