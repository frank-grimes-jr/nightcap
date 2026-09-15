import copy
import unittest

from aa_owned_view_controls import assess, prepare


class EarnedViewControlsTests(unittest.TestCase):
    def setUp(self):
        self.case = prepare({'cases': [{'input': {'builds': [{
            'profile': 'war-clr-wiz', 'test_character_id': 10,
            'aa_rank_ids': [999], 'equipment': [{'slot': 1, 'id': 100}],
        }]}}]})
        self.report = {'aa_ownership_probe': {'steps': [
            {'operation': operation, 'effective_rank_count': rank,
             'stored': [{'first_rank_id': 107, 'rank_count': 6, 'charges': 0}],
             'spent_points': 29, 'unspent_points': 17}
            for operation, rank in zip(self.case['input']['aa_ownership_probe']['operations'], [6, 6, 3, 3, 3, 6, 6])
        ]}}

    def test_preserved_earned_ranks_and_usable_prefix_are_required(self):
        self.assertTrue(all(assess(self.case, self.report).values()))
        broken = copy.deepcopy(self.report)
        broken['aa_ownership_probe']['steps'][2]['effective_rank_count'] = 0
        broken['aa_ownership_probe']['steps'][3]['spent_points'] = 5
        result = assess(self.case, broken)
        self.assertFalse(result['usable_prefix_preserved'])
        self.assertFalse(result['earned_plus_expended_points_preserved'])
        self.assertTrue(result['earned_rows_preserved'])

    def test_missing_operations_or_changed_earned_rows_cannot_pass(self):
        broken = copy.deepcopy(self.report)
        broken['aa_ownership_probe']['steps'].pop()
        with self.assertRaises(ValueError):
            assess(self.case, broken)
        self.report['aa_ownership_probe']['steps'][3]['stored'][0]['rank_count'] = 3
        self.assertFalse(assess(self.case, self.report)['earned_rows_preserved'])
