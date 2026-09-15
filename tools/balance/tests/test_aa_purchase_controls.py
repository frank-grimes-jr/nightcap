import copy
import unittest
from aa_purchase_controls import assess, cases


class AAPurchaseControlsTests(unittest.TestCase):
    def setUp(self):
        self.cases = cases({'cases': [{'input': {'builds': [
            {'profile': 'war-clr-wiz', 'test_character_id': 10}]}}]})

    def report(self, case):
        steps = copy.deepcopy(case['expected'])
        for step, operation in zip(steps, case['input']['aa_ownership_probe']['operations']):
            step['operation'] = operation
        return {'aa_ownership_probe': {'steps': steps}}

    def test_paid_free_silent_charged_and_failed_purchase_contracts(self):
        self.assertEqual(len(self.cases), 13)
        for case in self.cases:
            self.assertTrue(assess(case, self.report(case))['passed'])
        by_id = {c['id']: c for c in self.cases}
        self.assertEqual(by_id['paid-ranks-save-wallet-before-reload']['expected'][-1]['saved_points'],
                         {'wallet': 11, 'spent': 11, 'expended': 5})
        self.assertEqual(by_id['silent-grant-is-durable-without-later-save']['expected'][-1]['earned_rank_count'], 2)
        self.assertEqual(by_id['charged-purchase-consume-and-repurchase']['expected'][-1]['saved_points'],
                         {'wallet': 11, 'spent': 11, 'expended': 8})
        for case in self.cases:
            if case['fail_character_update']:
                self.assertEqual(case['expected'][-1]['stored'], [])
                self.assertFalse(case['expected'][-1]['earned_state_valid'])

    def test_stale_wallet_lost_grant_and_false_success_are_rejected(self):
        for case in self.cases:
            for field, value in [('saved_points', {'wallet': 999}), ('earned_rank_count', 99),
                                 ('success', 'unknown'), ('earned_state_valid', 'unknown'), ('purchase_events', ['false success'])]:
                report = self.report(case)
                report['aa_ownership_probe']['steps'][-1][field] = value
                self.assertFalse(assess(case, report)['passed'], (case['id'], field))
            report = self.report(case)
            report['aa_ownership_probe']['steps'].pop()
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                assess(case, report)
