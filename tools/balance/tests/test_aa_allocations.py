import unittest

from aa_allocations import Purchases, within_budget
from verify_native_aa import verify


def rank(ability, level=1, cost=2, **changes):
    return {'ability_id': ability, 'rank': level, 'rank_id': ability*100+level,
            'cost': cost, 'grant_only': False, 'charges': 0,
            'previous_rank_id': ability*100+level-1 if level > 1 else -1,
            'prereqs': [], **changes}


class PurchaseTests(unittest.TestCase):
    def test_native_ledger_verifier_rejects_cost_rank_and_budget_corruption(self):
        b = {'profile':'test','tier':'Ascended','aa_stage':'100','aa_policy':'balanced',
             'aa_budget':100,'aa_rank_ids':[101]}
        purchase = {'rank_id':101,'ability_id':1,'rank':1,'cost':2,'points_spent':2,'name':'Test AA'}
        result = b | {'aa_spent':2,'aa_remaining':98,'aa_purchases':[purchase]}
        catalog = {'builds':[{'profile':'test','aa_catalog':[rank(1, name='Test AA')]}]}
        self.assertEqual(verify({'builds':[b]},{'builds':[result]},catalog), [])
        for corrupt in (result | {'aa_remaining':99}, result | {'aa_purchases':[]},
                        result | {'aa_purchases':[purchase | {'cost':3}]}):
            self.assertTrue(verify({'builds':[b]},{'builds':[corrupt]},catalog))
        with self.assertRaises(ValueError):
            verify({'builds':[b]},{'builds':[]},catalog)

    def test_prerequisite_and_previous_ranks_are_bought_in_order(self):
        rows = [rank(1), rank(1, 2), rank(2, prereqs=[{'ability_id': 1, 'ranks': 2, 'ability_exists': True}])]
        p = Purchases(rows)
        p.require(2, 1)
        self.assertEqual(p.ids, [101, 102, 201])
        self.assertEqual(p.spent, 6)
        p.require(2, 1)
        self.assertEqual(p.spent, 6)

    def test_budget_prefix_is_nested_and_reports_unaffordable_rank(self):
        rows = [rank(1, cost=0), rank(2, cost=3), rank(3, cost=4)]
        small, pending = within_budget(rows, [101, 201, 301], 5)
        large, _ = within_budget(rows, [101, 201, 301], 7)
        self.assertEqual((small.ids, small.spent, pending), ([101, 201], 3, 301))
        self.assertEqual(large.ids[:len(small.ids)], small.ids)

    def test_free_baseline_excludes_grant_only_and_paid_prerequisites(self):
        rows = [rank(1, cost=0), rank(1, 2, cost=0), rank(2, cost=0, grant_only=True),
                rank(3), rank(4, cost=0, prereqs=[{'ability_id': 3, 'ranks': 1, 'ability_exists': True}])]
        p = Purchases(rows)
        p.free_closure()
        self.assertEqual(p.ids, [101, 102])
        blocked = p.all_closure()
        self.assertEqual(set(p.ids), {101, 102, 301, 401})
        self.assertEqual(blocked, [{'rank_id': 201, 'ability_id': 2, 'reasons': ['grant_only']}])

    def test_charged_ability_does_not_purchase_next_rank_while_charged(self):
        p = Purchases([rank(1, charges=1), rank(1, 2, charges=1)])
        blocked = p.all_closure()
        self.assertEqual(p.ids, [101])
        self.assertIn('unspent_charges', blocked[0]['reasons'])

    def test_missing_native_ability_prerequisite_is_ignored_but_gated_one_is_not(self):
        p = Purchases([rank(1, prereqs=[{'ability_id': 2, 'ranks': 1, 'ability_exists': False}]),
                       rank(3, prereqs=[{'ability_id': 4, 'ranks': 1, 'ability_exists': True}])])
        blocked = p.all_closure()
        self.assertEqual(p.ids, [101])
        self.assertEqual(blocked[0]['reasons'], ['prerequisite:4'])

    def test_cycles_missing_chain_and_duplicates_fail_closed(self):
        p = Purchases([rank(1, prereqs=[{'ability_id': 2, 'ranks': 1, 'ability_exists': True}]),
                       rank(2, prereqs=[{'ability_id': 1, 'ranks': 1, 'ability_exists': True}])])
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            p.require(1, 1)
        with self.assertRaisesRegex(ValueError, 'previous'):
            Purchases([rank(1, 2)]).require(1, 2)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            Purchases([rank(1), rank(1)])
        with self.assertRaises(ValueError):
            within_budget([rank(1)], [101], -1)
