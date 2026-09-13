import copy
import unittest

from aa_bulk_controls import assess, cases


class AABulkControlsTests(unittest.TestCase):
    def setUp(self):
        self.cases = cases({'cases': [{'input': {'builds': [
            {'profile': 'war-clr-wiz', 'test_character_id': 10}]}}]})

    def report(self, case):
        steps = copy.deepcopy(case['expected'])
        for step, operation in zip(steps, case['input']['aa_ownership_probe']['operations']):
            step['operation'] = operation
        return {'aa_ownership_probe': {'steps': steps}}

    def test_refund_grant_preservation_profile_guard_and_prior_removal_controls(self):
        self.assertEqual(len(self.cases), 11)
        for case in self.cases:
            self.assertTrue(assess(case, self.report(case))['passed'])
        for case in self.cases[:3]:
            end = case['expected'][-1]
            self.assertEqual(end['saved_points'], {'wallet': 41, 'spent': 5, 'expended': 5})
            self.assertEqual(end['stored'], [{'first_rank_id': 5006, 'rank_count': 1, 'charges': 0}])
        guard = self.cases[4]['expected'][-1]
        self.assertEqual((guard['spent_points'], guard['saved_points']['spent'], guard['success']), (29, 5, False))
        partial = self.cases[6]['expected']
        self.assertEqual((partial[2]['effective_rank_count'], partial[2]['earned_rank_count']), (3, 6))
        self.assertEqual(partial[-1]['unspent_points'], 41)

    def test_duplicate_refund_lost_grant_stale_save_and_failed_mutations_cannot_pass(self):
        for case in self.cases:
            for field, value in [('unspent_points', 65), ('saved_points', {'wallet': 65}),
                                 ('stored', []), ('profile', []), ('earned_state_valid', 'missing'),
                                 ('success', 'missing')]:
                report = self.report(case)
                step = report['aa_ownership_probe']['steps'][0]
                if step.get(field) == value:
                    continue
                step[field] = value
                with self.subTest(case=case['id'], field=field):
                    self.assertFalse(assess(case, report)['passed'])
            report = self.report(case)
            report['aa_ownership_probe']['steps'].pop()
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                assess(case, report)
