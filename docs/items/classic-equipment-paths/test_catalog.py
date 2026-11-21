import gzip,json,unittest
from catalog import HERE,FIELDS,changes,generate

class EquipmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets=changes();cls.policy=json.loads((HERE/'policy.json').read_bytes())['families']
        cls.effects={r['id']:r for r in json.loads((HERE/'effects.json').read_bytes())['spells']}
    def test_full_quality_empty_fields_only(self):
        self.assertEqual(len(self.targets),4*len(self.policy))
        for key,(row,old,new) in self.targets.items():
            self.assertEqual(row['augtype'],0);self.assertLess(key,800000)
            if old[:4]!=new[:4]:self.assertIn(old[:4],((-1,0,0,0),(0,0,0,0)))
            if old[4:]!=new[4:]:self.assertEqual(old[4:],(-1,0,0,0))
            self.assertTrue({f for f,a,b in zip(FIELDS,old,new) if a!=b}<={'focuseffect','focustype','worneffect','worntype'})
    def test_additive_budgets_are_limited_by_slot(self):
        expected={2686:(0,1,4),2687:(0,2,4),1298:(15,1,524288),1299:(15,2,524288),2201:(2,5,64),2594:(2,15,64)}
        for key,e in self.policy.items():
            if e.get('worn') not in expected:continue
            spa,value,slots=expected[e['worn']];row=self.targets[int(key)][0];s=self.effects[e['worn']]
            self.assertEqual(row['slots'],slots)
            active=[(s['effectid'+str(n)],s['effect_base_value'+str(n)]) for n in range(1,13) if s['effectid'+str(n)] not in (254,10)]
            self.assertEqual(active,[(spa,value)])
    def test_haste_and_defense_are_strongest_not_additive(self):
        expected={4348:[(11,110)],1925:[(11,120)],3889:[(174,10)],3892:[(175,8),(188,8)]}
        for key,pairs in expected.items():
            s=self.effects[key]
            actual=[(s['effectid'+str(n)],s['effect_base_value'+str(n)]) for n in range(1,13) if s['effectid'+str(n)] not in (254,10)]
            self.assertEqual(actual,pairs)
        self.assertTrue(all(e.get('worn') not in (4348,1925) or self.targets[int(k)][0]['slots']==4096 for k,e in self.policy.items()))
    def test_focus_categories_and_thj_damage_amplification_are_explicit(self):
        for e in self.policy.values():
            if 'focus' not in e:continue
            s=self.effects[e['focus']];spa=s['effectid1'];self.assertIn(spa,(124,125,127,132))
            self.assertIn(s['effect_base_value2'],(20,44,60))
            if spa==124:self.assertEqual(s['effect_limit_value1']*10,200)
    def test_reachable_crafts_not_orphan_recipes(self):
        audit=json.loads((HERE/'acquisition-audit.json').read_bytes())
        for key,e in self.policy.items():
            if e['category'].startswith('crafted_'):self.assertIn(key,audit['reached'])
        self.assertEqual({e['category'] for e in self.policy.values()},{'crafted_jewelry','crafted_armor','class_quest','ro_quest','stock_drop'})
    def test_full_row_guards_protect_custom_and_instance_boundaries(self):
        for action in ('forward','rollback'):
            lines=[x for x in generate(action).splitlines() if x.startswith('UPDATE ')]
            self.assertEqual(len(lines),len(self.targets))
            for line in lines:
                assigned=line.split(' SET ')[1].split(' WHERE ')[0]
                self.assertTrue(set(p.split('=')[0] for p in assigned.split(','))<={'`focuseffect`','`focustype`','`worneffect`','`worntype`'})
                for f in ('Name','clickeffect','proceffect','augslot1type','hp','mana','haste','attack','accuracy','classes','races','deity'):
                    self.assertIn('`'+f+'` <=> ',line)
        self.assertNotIn('UPDATE ',generate('verify'))
        self.assertNotIn('UPDATE ',generate('before'))

if __name__=='__main__':unittest.main()
