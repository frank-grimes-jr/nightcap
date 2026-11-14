import json
from pathlib import Path
import unittest
from catalog import FAMILIES, HERE, SLOTS, scales


class ClassicAugments(unittest.TestCase):
    def test_legal_slots_and_power(self):
        legal=json.loads((HERE/'eligibility.json').read_bytes())
        mask=sum(int(n) for n in legal['hosts'])
        self.assertEqual(mask,SLOTS)
        self.assertEqual(mask.bit_count(),8)
        for row in scales():
            self.assertEqual(row['slots'],mask)
            self.assertEqual(row['augtype'],64)
            self.assertEqual(row['reqlevel'],50)
            self.assertFalse(mask & ((1<<11)|(1<<13)|(1<<14)|(1<<21)))
        for base,kind,effect,part,gem in FAMILIES:
            family=[row for row in scales() if row['id']%200000==base]
            self.assertEqual([r['id'] for r in family],[base+200000*i for i in range(4)])
            self.assertEqual([r['Name'] for r in family],[f'Prismatic Scale of {kind}'+s for s in ('',' (Polished)',' (Exalted)',' (Ascended)')])
            self.assertEqual(8*family[-1]['hp'],960)
            self.assertEqual(8*family[-1].get('mana',0),960)
            key={'Dodging':'damageshield','Healing':'healamt','Magic':'spelldmg'}[kind]
            self.assertEqual(8*family[-1][key],40 if kind=='Dodging' else 80)
            fx='worneffect' if kind=='Dodging' else 'focuseffect'
            self.assertEqual(family[-1][fx],effect)
            self.assertTrue(all(fx not in r for r in family[:-1]))
            ingredients={int(r.split('\t')[0]) for r in legal['ingredients']}
            self.assertTrue({part,gem}<=ingredients)

    def test_stock_rounding_and_scope(self):
        rows=json.loads((HERE/'stock.json').read_bytes())
        legal=json.loads((HERE/'eligibility.json').read_bytes())
        self.assertEqual({int(r.split('\t')[0]) for r in legal['stock']},{r['id']%200000 for r in rows})
        self.assertEqual(len({r['id'] for r in rows}),36)
        for r in rows:
            for before,after,step in zip(r['before'],r['after'],[5,5,10,10],strict=True):
                self.assertGreaterEqual(after,before)
                self.assertEqual(after%step,0)
                self.assertEqual(bool(before),bool(after))


if __name__=='__main__':
    unittest.main()
