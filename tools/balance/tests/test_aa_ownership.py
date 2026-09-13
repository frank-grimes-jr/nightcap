import copy
import unittest

from aa_ownership import transition
from tests import test_aa_policy_preflight as fixtures


class AAOwnershipTests(unittest.TestCase):
    def fixture(self):
        return fixtures.AAPolicyPreflightTests().fixture()

    def test_cap_preserves_earned_ranks_and_separates_suspended_nominal_cost(self):
        source, spec = self.fixture()
        result = transition(source, spec, 'launch', source['purchases'])
        self.assertEqual(result['earned_rows'], source['purchases'])
        self.assertEqual(result['active_rows'], [{'id': 7, 'aa_id': 100, 'aa_value': 1, 'charges': 0}])
        self.assertEqual(result['point_totals'], [{'character_id': 7, 'active_nominal_cost': 2,
                                                 'suspended_nominal_cost': 4, 'earned_nominal_cost': 6}])

    def test_later_unlock_and_restriction_round_trip_without_losing_ownership(self):
        source, spec = self.fixture()
        launch = transition(source, spec, 'launch', source['purchases'])
        later = transition(source, spec, 'later', launch['active_rows'], launch)
        self.assertEqual(later['active_rows'], source['purchases'])
        again = transition(source, spec, 'launch', later['active_rows'], later)
        self.assertEqual(again['active_rows'], launch['active_rows'])
        self.assertEqual(again['earned_rows'], launch['earned_rows'])

    def test_omitted_family_can_return_without_rebuying_it(self):
        source, spec = self.fixture()
        spec['policies'].append({'id': 'closed', 'caps': {}})
        closed = transition(source, spec, 'closed', source['purchases'])
        self.assertEqual(closed['active_rows'], [])
        later = transition(source, spec, 'later', [], closed)
        self.assertEqual(later['active_rows'], source['purchases'])

    def test_new_progress_within_previous_caps_becomes_earned_before_restricting(self):
        source, spec = self.fixture()
        initial = copy.deepcopy(source['purchases'])
        initial[0]['aa_value'] = 1
        previous = transition(source, spec, 'later', initial)
        current = copy.deepcopy(initial)
        current[0]['aa_value'] = 2
        result = transition(source, spec, 'launch', current, previous)
        self.assertEqual(result['earned_rows'][0]['aa_value'], 2)
        self.assertEqual(result['active_rows'][0]['aa_value'], 1)

    def test_disappearance_or_lower_count_requires_explicit_refund_reset_handling(self):
        source, spec = self.fixture()
        previous = transition(source, spec, 'later', source['purchases'])
        for rows in ([], [dict(source['purchases'][0], aa_value=1)]):
            with self.assertRaisesRegex(ValueError, 'decreased or disappeared'):
                transition(source, spec, 'launch', rows, previous)

    def test_illegal_new_rank_or_changed_source_is_not_silently_accepted(self):
        source, spec = self.fixture()
        previous = transition(source, spec, 'launch', source['purchases'])
        with self.assertRaisesRegex(ValueError, 'previous caps'):
            transition(source, spec, 'later', source['purchases'], previous)
        source['ranks'][1]['cost'] += 1
        with self.assertRaisesRegex(ValueError, 'source changed'):
            transition(source, spec, 'later', previous['active_rows'], previous)

    def test_charged_ownership_is_not_suspended_or_recharged_implicitly(self):
        source, spec = self.fixture()
        source['abilities'][0]['charges'] = 1
        source['purchases'][0]['charges'] = 1
        with self.assertRaisesRegex(ValueError, 'Charged'):
            transition(source, spec, 'launch', source['purchases'])

    def test_duplicate_and_invalid_ownership_are_rejected(self):
        source, spec = self.fixture()
        for rows in (source['purchases'] * 2, [dict(source['purchases'][0], aa_id=999)]):
            with self.assertRaises(ValueError):
                transition(source, spec, 'launch', rows)


if __name__ == '__main__':
    unittest.main()
