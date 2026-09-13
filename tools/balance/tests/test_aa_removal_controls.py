import copy
import unittest

from aa_removal_controls import assess, cases


class AARemovalControlsTests(unittest.TestCase):
    def setUp(self):
        self.cases = cases({'cases': [{'input': {'builds': [
            {'profile': 'war-clr-wiz', 'test_character_id': 10}]}}]})

    def report(self, case):
        steps = copy.deepcopy(case['expected'])
        for index, step in enumerate(steps):
            step['operation'] = case['input']['aa_ownership_probe']['operations'][index]
            step['first_rank_purchasable'] = not step['earned_rank_count']
        return {'aa_ownership_probe': {'steps': steps}}

    def test_reset_suspension_consumption_and_rollback_have_explicit_end_states(self):
        self.assertEqual(len(self.cases), 4)
        for case in self.cases:
            self.assertTrue(assess(case, self.report(case))['passed'])
        charge = self.cases[2]['expected']
        self.assertEqual([s['spent_points'] for s in charge], [8] * 7)
        self.assertEqual([s['expended_points'] for s in charge], [5] + [8] * 6)
        failure = self.cases[3]['expected']
        self.assertEqual([s['earned_state_valid'] for s in failure], [True, False, False, True])

    def test_resurrection_currency_profile_and_rollback_corruption_fail(self):
        for case in self.cases:
            for field, wrong in [('earned_rank_count', 99), ('stored', ['resurrected']),
                                 ('profile', ['stale']), ('unspent_points', 18),
                                 ('spent_points', 999), ('expended_points', 999),
                                 ('saved_points', {'wallet': 999}), ('active_charges', 99)]:
                with self.subTest(case=case['id'], field=field):
                    report = self.report(case)
                    report['aa_ownership_probe']['steps'][-1][field] = wrong
                    self.assertFalse(assess(case, report)['passed'])
            report = self.report(case)
            report['aa_ownership_probe']['steps'].pop()
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                assess(case, report)
