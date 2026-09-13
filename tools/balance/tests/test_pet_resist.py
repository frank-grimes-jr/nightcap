import copy
import json
from pathlib import Path
import unittest

from pet_resist_controls import prepare,verify


class PetResistanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((Path(__file__).resolve().parents[3]/'docs/balance/gear-source-inputs.json').read_text(encoding='utf-8'))

    def test_adds_only_four_native_preparation_casts(self):
        matrix=prepare(self.original,'0'*64)
        self.assertEqual(len(matrix['cases']),36)
        self.assertEqual(matrix['allocations'],self.original['allocations'])
        old={c['id']:c for c in self.original['cases']}
        for case in matrix['cases']:
            value=copy.deepcopy(case['input'])
            actions=value['pet_probe']['actions']
            self.assertEqual([a for a in actions if a['spell']==64],
                             [{'spell':64},{'spell':64,'target_class':13},{'spell':64,'target_class':11},{'spell':64,'target_class':10}])
            value['pet_probe']['actions']=[a for a in actions if a['spell']!=64]
            self.assertEqual(value,old[case['paired_gear_case_id']]['input'])

    def test_pilot_keeps_zero_and_both_aa_maxima(self):
        matrix=prepare(self.original,'0'*64,True)
        self.assertEqual(len(matrix['cases']),3)
        self.assertEqual({c['input']['builds'][0]['aa_budget'] for c in matrix['cases']},{0,165,306})

    def test_cannot_silently_change_combat_policy(self):
        matrix=prepare(self.original,'0'*64,True)
        matrix['cases'][0]['input']['pet_probe']['combat']['owner_policy']='none'
        with self.assertRaisesRegex(ValueError,'matched gear'):
            verify(matrix,{},self.original,{})


if __name__=='__main__':unittest.main()
