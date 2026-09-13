import copy
import unittest

from aa_owned_core_controls import cases, verify


class EarnedCoreControlsTests(unittest.TestCase):
    def setUp(self):
        self.cases = cases({'cases': [{'input': {'builds': [
            {'profile': 'war-clr-wiz', 'test_character_id': 10}]}}]})

    def passing_report(self, case):
        row = case['stored']
        stored = [] if row is None else [{'first_rank_id': row['aa_id'],
                                         'rank_count': row['aa_value'], 'charges': row['charges']}]
        probe = case['input']['aa_ownership_probe']
        return {'aa_ownership_probe': {'steps': [
            {'operation': op, 'effective_rank_count': active, 'stored': stored,
             'profile': [] if not active else [{'first_rank_id': probe['first_rank_id'],
                                                'rank_count': active, 'charges': row['charges']}],
             'spent_points': probe['initial_spent_points'], 'unspent_points': 17,
             'earned_state_valid': case['expected_valid'], 'success': case['expected_valid'],
             'earned_rank_count': case['expected_earned'],
             'first_rank_already_earned': bool(case['expected_earned']),
             'first_rank_purchasable': False}
            for op, active in zip(probe['operations'], case['expected_active'])]}}

    def test_partial_full_empty_charged_and_invalid_ownership_are_distinct(self):
        self.assertEqual(len(self.cases), 6)
        for case in self.cases:
            self.assertTrue(verify(case, self.passing_report(case))['passed'])
        self.assertEqual(self.cases[1]['expected_active'][2:5], [0, 0, 0])
        self.assertIsNone(self.cases[2]['stored'])

    def test_currency_ownership_purchase_and_failure_corruption_cannot_pass(self):
        for case in self.cases:
            report = self.passing_report(case)
            corruptions = {'stored': [{'first_rank_id': 1}], 'profile': [{'first_rank_id': 1}], 'spent_points': 0,
                           'unspent_points': 18, 'earned_rank_count': 99,
                           'earned_state_valid': not case['expected_valid'],
                           'success': not case['expected_valid']}
            if case['expected_earned'] or not case['expected_valid']:
                corruptions['first_rank_purchasable'] = True
            if case['expected_earned']:
                corruptions['first_rank_already_earned'] = False
            for field, value in corruptions.items():
                with self.subTest(case=case['id'], field=field):
                    changed = copy.deepcopy(report)
                    changed['aa_ownership_probe']['steps'][-1][field] = value
                    with self.assertRaises(ValueError):
                        verify(case, changed)
            report['aa_ownership_probe']['steps'].pop()
            with self.assertRaises(ValueError):
                verify(case, report)
