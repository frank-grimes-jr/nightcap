import copy
import unittest

from aa_policy_preflight import build_preflight


class AAPolicyPreflightTests(unittest.TestCase):
    def fixture(self):
        snapshot = {
            'abilities': [
                {'id': 10, 'name': 'Durability', 'enabled': 1, 'first_rank_id': 100},
                {'id': 20, 'name': 'Utility', 'enabled': 1, 'first_rank_id': 200}],
            'ranks': [
                {'id': 100, 'cost': 2, 'next_id': 101, 'level_req': 1, 'expansion': 3},
                {'id': 101, 'cost': 4, 'next_id': -1, 'level_req': 1, 'expansion': 4},
                {'id': 200, 'cost': 0, 'next_id': -1, 'level_req': 1, 'expansion': 0}],
            'prerequisites': [],
            'purchases': [{'id': 7, 'aa_id': 100, 'aa_value': 2, 'charges': 0}],
        }
        spec = {'free_caps': {'20': 1}, 'policies': [
            {'id': 'launch', 'caps': {'10': 1}},
            {'id': 'later', 'caps': {'10': 2}}]}
        return snapshot, spec

    def test_resolves_rank_chains_and_separates_ability_ids_from_saved_rank_ids(self):
        snapshot, spec = self.fixture()
        before = copy.deepcopy(snapshot)
        report = build_preflight(snapshot, spec)
        self.assertEqual(snapshot, before)
        launch, later = report['policies']
        self.assertEqual(launch['allowed_rank_ids'], [100, 200])
        self.assertEqual(later['allowed_rank_ids'], [100, 101, 200])
        row = launch['purchase_impact'][0]
        self.assertEqual((row['ability_id'], row['owned_rank_count'], row['candidate_rank_count']), (10, 2, 1))
        self.assertEqual(row['nominal_removed_rank_cost'], 4)
        self.assertEqual(row['status'], 'above_cap')
        self.assertEqual(later['purchase_impact'][0]['status'], 'retained')

    def test_omitted_ability_is_reported_without_claiming_refund_or_deletion(self):
        snapshot, spec = self.fixture()
        spec['policies'][0]['caps'] = {}
        row = build_preflight(snapshot, spec)['policies'][0]['purchase_impact'][0]
        self.assertEqual(row['status'], 'outside_pool')
        self.assertEqual(row['candidate_rank_count'], 0)
        self.assertEqual(row['nominal_removed_rank_cost'], 6)
        self.assertNotIn('refund', row)
        self.assertNotIn('sql', row)

    def test_missing_owned_rank_and_out_of_range_count_are_unresolved(self):
        for field, value in (('aa_id', 999), ('aa_value', 3), ('aa_value', 0)):
            snapshot, spec = self.fixture()
            snapshot['purchases'][0][field] = value
            row = build_preflight(snapshot, spec)['policies'][0]['purchase_impact'][0]
            self.assertEqual(row['status'], 'unresolved')
            self.assertIsNone(row['nominal_removed_rank_cost'])

    def test_noncanonical_saved_rank_is_not_silently_rewritten(self):
        snapshot, spec = self.fixture()
        snapshot['purchases'][0]['aa_id'] = 101
        row = build_preflight(snapshot, spec)['policies'][0]['purchase_impact'][0]
        self.assertEqual(row['status'], 'unresolved')
        self.assertIn('first rank', row['reason'])

    def test_charged_purchase_requires_separate_reconciliation(self):
        snapshot, spec = self.fixture()
        snapshot['purchases'][0]['charges'] = 1
        row = build_preflight(snapshot, spec)['policies'][0]['purchase_impact'][0]
        self.assertEqual(row['status'], 'above_cap')
        self.assertTrue(row['has_unspent_charges'])

    def test_selected_disabled_unknown_or_oversized_caps_are_rejected(self):
        for mutate in (lambda s, p: s['abilities'][0].update(enabled=0),
                       lambda s, p: p['policies'][0]['caps'].update({'99': 1}),
                       lambda s, p: p['policies'][0]['caps'].update({'10': 3}),
                       lambda s, p: p['policies'][0]['caps'].update({'010': 2}),
                       lambda s, p: p['policies'][0]['caps'].update({'10': True})):
            snapshot, spec = self.fixture()
            mutate(snapshot, spec)
            with self.assertRaises(ValueError):
                build_preflight(snapshot, spec)

    def test_missing_cyclic_or_shared_selected_rank_chain_is_rejected(self):
        for mutate in (lambda s: s['ranks'][0].update(next_id=999),
                       lambda s: s['ranks'][1].update(next_id=100),
                       lambda s: s['abilities'][1].update(first_rank_id=101)):
            snapshot, spec = self.fixture()
            mutate(snapshot)
            with self.assertRaises(ValueError):
                build_preflight(snapshot, spec)

    def test_missing_and_excluded_prerequisites_are_explicit_blockers(self):
        for prerequisite in (99, 20):
            snapshot, spec = self.fixture()
            snapshot['prerequisites'] = [{'rank_id': 100, 'aa_id': prerequisite, 'points': 1}]
            spec['free_caps'] = {}
            report = build_preflight(snapshot, spec)['policies'][0]
            self.assertTrue(report['prerequisite_issues'])
            self.assertFalse(report['prerequisites_closed'])

    def test_native_truncated_tail_keeps_existing_rank_prefix(self):
        snapshot, spec = self.fixture()
        snapshot['ranks'][1]['next_id'] = 999
        report = build_preflight(snapshot, spec)
        self.assertEqual(report['policies'][1]['allowed_rank_ids'], [100, 101, 200])
        self.assertTrue(report['source_chain_issues']['10'])
        self.assertEqual(report['policies'][1]['purchase_impact'][0]['status'], 'retained')

    def test_disabled_alias_does_not_own_native_ranks(self):
        snapshot, spec = self.fixture()
        snapshot['abilities'].append({'id': 30, 'name': 'Disabled duplicate',
                                     'enabled': 0, 'first_rank_id': 100})
        self.assertEqual(build_preflight(snapshot, spec)['policies'][0]['allowed_rank_ids'], [100, 200])

    def test_inherited_prerequisite_and_cycle_are_checked(self):
        snapshot, spec = self.fixture()
        snapshot['prerequisites'] = [{'rank_id': 100, 'aa_id': 20, 'points': 1},
                                     {'rank_id': 200, 'aa_id': 10, 'points': 1}]
        report = build_preflight(snapshot, spec)['policies'][1]
        self.assertEqual(report['ranks'][1]['prerequisites'], [{'ability_id': 20, 'ranks': 1}])
        self.assertTrue(any(i['reason'] == 'cyclic_prerequisite' for i in report['prerequisite_issues']))

    def test_duplicate_snapshot_and_free_paid_overlap_are_rejected(self):
        for mutate in (lambda s, p: s['purchases'].append(copy.deepcopy(s['purchases'][0])),
                       lambda s, p: s['abilities'].append(copy.deepcopy(s['abilities'][0])),
                       lambda s, p: p['free_caps'].update({'10': 1}),
                       lambda s, p: s['ranks'][2].update(cost=1)):
            snapshot, spec = self.fixture()
            mutate(snapshot, spec)
            with self.assertRaises(ValueError):
                build_preflight(snapshot, spec)


if __name__ == '__main__':
    unittest.main()
