import copy
from pathlib import Path
import unittest

from aa_policy_preflight import read_json
from pet_shield_controls import prepare


class PetShieldControlsTests(unittest.TestCase):
    def test_only_declared_owner_buff_and_optional_magic_casts_change(self):
        source = read_json(Path(__file__).resolve().parents[3] / 'docs/balance/gear-source-inputs.json')
        frozen = copy.deepcopy(source)
        result = prepare(source, 'candidate')
        self.assertEqual(source, frozen)
        self.assertEqual(len(result['cases']), 36)
        originals = {c['id']: c for c in source['cases']}
        for case in result['cases']:
            restored = copy.deepcopy(case['input'])
            actions = restored['pet_probe']['actions']
            for action in actions:
                if action['spell'] == 67:
                    self.assertFalse(action.get('target_class'))
                    action['spell'] = 168
            if case['shield_variant'] == 'arch_magic':
                self.assertEqual(sum(a['spell'] == 64 for a in actions), 4)
                restored['pet_probe']['actions'] = [a for a in actions if a['spell'] != 64]
            self.assertEqual(restored, originals[case['paired_gear_case_id']]['input'])


if __name__ == '__main__':
    unittest.main()
