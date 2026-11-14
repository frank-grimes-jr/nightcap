import json
from pathlib import Path
import unittest
from catalog import HERE, POLICY, changes

class RaidFocus(unittest.TestCase):
    def test_source_and_existing_abilities(self):
        audit=json.loads((HERE/'audit.json').read_bytes())
        target=changes()
        self.assertEqual(len(target),24)
        zones={row[0] for row in audit['routes'] if int(row[3]) in POLICY}
        self.assertTrue({'hateplane','fearplane','airplane','kedge','permafrost','soldungb'}<=zones)
        for key,(record,old,new) in target.items():
            self.assertEqual(sum(a!=b for a,b in zip(old,new)),2)
            self.assertEqual(int(record['id']),key)
            suffix=('',' (Polished)',' (Exalted)',' (Ascended)')[key//200000]
            self.assertEqual(record['Name'],target[key%200000][0]['Name']+suffix)
            self.assertEqual(record['slots'],target[key%200000][0]['slots'])
        self.assertEqual(target[11611][0]['proceffect'],'44')
        self.assertTrue(all(int(r['id']) not in target for r in audit['items'] if r['clickeffect']=='276'))

    def test_spell_limits(self):
        rows=json.loads((HERE/'effects.json').read_bytes())['spells']
        for effect in set(POLICY.values()):
            r=next(r for r in rows if int(r[0])==effect)
            slots=[tuple(map(int,r[i:i+4])) for i in range(2,len(r),4)]
            if effect==3889:
                self.assertEqual(slots[0],(174,10,0,0))
            else:
                self.assertIn((134,44,5,0),slots)
                self.assertEqual(100-(50-44)*5,70)
        # The existing stronger Prismatic healing and damage focuses cover spell level 50.
        for key in (3501,3513):
            r=next(r for r in rows if int(r[0])==key)
            self.assertIn(['134','65','5','0'],[r[i:i+4] for i in range(2,len(r),4)])


if __name__=='__main__':
    unittest.main()
