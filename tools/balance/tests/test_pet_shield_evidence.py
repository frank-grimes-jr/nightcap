import copy
from pathlib import Path
import unittest

from aa_policy_preflight import read_json
from pet_shield_controls import verify


class PetShieldEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3] / 'docs/balance'

    def read(self, name):
        return read_json(self.docs / name)

    def test_all_36_native_cases_verify_with_unchanged_unbuffed_builds(self):
        matrix = self.read('pet-shield-inputs.json')
        evidence = self.read('pet-shield.json.gz')
        self.assertEqual(len(verify(matrix, evidence, self.read('gear-source-inputs.json'),
                                    self.read('native-aa-catalog.json'))), 36)
        cases = {c['id']: c for c in matrix['cases']}
        old = {r['id']: r for r in self.read('gear-source.json.gz')['runs']}
        for run in evidence['runs']:
            paired = old[cases[run['id']]['paired_gear_case_id']]
            self.assertEqual(run['report']['builds'], paired['report']['builds'])
        self.assertEqual(self.read('pet-shield-final-checks.json')['remaining_rows'],
                         {'account': 0, 'character_data': 0, 'character_alternate_abilities': 0, 'inventory': 0})

    def test_missing_chosen_owner_buff_is_rejected(self):
        evidence = self.read('pet-shield.json.gz')
        bad = copy.deepcopy(evidence)
        buffs = bad['runs'][0]['report']['pet_probe']['final']['player']['buffs']
        buffs[:] = [b for b in buffs if b['spell'] != 67]
        with self.assertRaises(ValueError):
            verify(self.read('pet-shield-inputs.json'), bad, self.read('gear-source-inputs.json'),
                   self.read('native-aa-catalog.json'))


if __name__ == '__main__':
    unittest.main()
