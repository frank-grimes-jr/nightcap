import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import winged_helmet_item as item

def template():
    row={k:'0' for k in item.CHANGES}
    row.update(id='4851',Name='Valorium Helmet')
    for key in ('haste','regen','manaregen','enduranceregen','herosforgemodel',
                'elitematerial','heroic_str','heroic_sta','heroic_agi','heroic_dex',
                'heroic_wis','heroic_int','heroic_cha','spelldmg','healamt','reqlevel','reclevel'):
        row[key]='0'
    for key in ('clickeffect','proceffect','worneffect','focuseffect','scrolleffect','bardeffect'):row[key]='-1'
    for i in range(1,7):row[f'augslot{i}type']='0'
    row['augslot1type']='7';row['augslot2type']='21'
    return row

class ItemTests(unittest.TestCase):
    def test_classic_class_and_race_gates_and_template_preservation(self):
        source=template();before=dict(source);row=item.plan(source)
        self.assertEqual(source,before)
        self.assertEqual(int(row['classes']),1<<(3-1))
        self.assertEqual(int(row['races']),(1<<12)-1)
        self.assertEqual(row['slots'],'4')
        self.assertTrue(all(int(row[f'augslot{i}type'])==0 for i in range(1,7)))

    def test_unexpected_template_power_rejected(self):
        for name,value in [('haste','1'),('focuseffect','123'),('augslot3type','7')]:
            row=template();row[name]=value
            with self.assertRaises(ValueError,msg=name):item.plan(row)

    def test_rehearsal_uses_rollback_and_preserves_full_template_schema(self):
        sql=item.forward(template(),commit=False)
        self.assertIn('CREATE TEMPORARY TABLE nightcap_winged_helmet LIKE items',sql)
        self.assertIn('INSERT INTO items SELECT * FROM nightcap_winged_helmet',sql)
        self.assertNotIn('COMMIT;',sql)
        self.assertIn('ROLLBACK;',sql)
        self.assertIn('Helmet ID or name occupied',sql)

if __name__=='__main__':unittest.main()
