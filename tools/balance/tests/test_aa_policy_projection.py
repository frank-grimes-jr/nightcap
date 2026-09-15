import copy
import unittest

from aa_policy_projection import project, transaction_sql
from run_aa_projection import verify_batch
from tests import test_aa_policy_preflight as fixtures


class AAProjectionTests(unittest.TestCase):
    def fixture(self):
        snapshot, spec = fixtures.AAPolicyPreflightTests().fixture()
        snapshot['abilities'].append({'id': 30, 'name': 'Omitted', 'enabled': 1, 'first_rank_id': 300})
        snapshot['ranks'].append({'id': 300, 'cost': 1, 'next_id': -1, 'level_req': 1, 'expansion': 3})
        return snapshot, spec

    def test_projection_only_changes_enabled_and_selected_chain_end(self):
        snapshot, spec = self.fixture()
        original = copy.deepcopy(snapshot)
        result = project(snapshot, spec, 'launch')
        self.assertEqual(snapshot, original)
        self.assertEqual(result['changes'], {'aa_ability': [[30, 1, 0]], 'aa_ranks': [[100, 101, -1]]})
        self.assertEqual(result['allowed_rank_ids'], [100, 200])

    def test_later_projection_restores_the_original_rank_chain(self):
        snapshot, spec = self.fixture()
        later = project(snapshot, spec, 'later')
        self.assertEqual(later['changes']['aa_ranks'], [])
        self.assertEqual(later['allowed_rank_ids'], [100, 101, 200])

    def test_live_database_or_unsafe_procedure_name_is_rejected(self):
        snapshot, spec = self.fixture()
        plan = project(snapshot, spec, 'launch')
        with self.assertRaises(ValueError):
            transaction_sql(plan, 'peq', 'aa_test')
        with self.assertRaises(ValueError):
            transaction_sql(plan, 'nightcap_balance_20260912', 'aa_test; DROP TABLE aa_ranks')

    def test_forward_and_restore_sql_are_guarded_atomic_and_leave_class_masks_alone(self):
        snapshot, spec = self.fixture()
        plan = project(snapshot, spec, 'launch')
        for restore in (False, True):
            sql = transaction_sql(plan, 'nightcap_balance_20260912', 'aa_test', restore)
            self.assertIn('DECLARE EXIT HANDLER FOR SQLEXCEPTION', sql)
            self.assertIn('ROLLBACK; RESIGNAL;', sql)
            self.assertIn('START TRANSACTION;', sql)
            self.assertIn('FROM character_data', sql)
            self.assertIn('FROM character_alternate_abilities', sql)
            self.assertIn('ROW_COUNT() <> 1', sql)
            self.assertNotIn('SET classes', sql)
            self.assertNotIn('UPDATE character_', sql)
            self.assertIn('THEN 101' if restore else 'THEN -1', sql)

    def test_prerequisite_gaps_cannot_be_projected(self):
        snapshot, spec = self.fixture()
        snapshot['prerequisites'] = [{'rank_id': 100, 'aa_id': 30, 'points': 1}]
        with self.assertRaisesRegex(ValueError, 'prerequisite'):
            project(snapshot, spec, 'launch')

    def test_native_verification_requires_exact_allowed_catalog_and_unchanged_stats(self):
        before = {'builds': [{'hp': 500, 'aa_catalog': [
            {'rank_id': 100, 'next_rank_id': 101}, {'rank_id': 101, 'next_rank_id': -1}]}]}
        after = {'builds': [{'hp': 500, 'aa_catalog': [{'rank_id': 100, 'next_rank_id': -1}]}]}
        verify_batch(before, after, {100})
        for mutate in (lambda x: x['builds'][0].update(hp=501),
                       lambda x: x['builds'][0]['aa_catalog'].append({'rank_id': 101, 'next_rank_id': -1}),
                       lambda x: x['builds'][0].update(aa_catalog=[])):
            changed = copy.deepcopy(after)
            mutate(changed)
            with self.assertRaises(ValueError):
                verify_batch(before, changed, {100})


if __name__ == '__main__':
    unittest.main()
