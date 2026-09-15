import copy
import json
from pathlib import Path
import unittest

from release_pool_controls import allocation_plan, prepare


class SharedPoolAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.catalog = cls.read('native-aa-catalog.json')
        cls.spec = cls.read('aa-release-candidates.json')

    @classmethod
    def read(cls, name):
        return json.loads((cls.docs/name).read_text(encoding='utf-8'))

    def test_caps_apply_globally_and_remove_unlisted_ranks(self):
        catalogs = {b['profile']: {r['rank_id']: r for r in b['aa_catalog']} for b in self.catalog['builds']}
        policies = {p['id']: p for p in self.spec['policies']}
        for allocation in allocation_plan(self.catalog, self.spec):
            ranks = [catalogs[allocation['profile']][i] for i in allocation['rank_ids']]
            self.assertEqual(sum(r['cost'] for r in ranks), allocation['spent'])
            self.assertFalse({0, 1684, 1685, 515, 308, 108, 338, 341, 398} & {r['ability_id'] for r in ranks})
            for alias in allocation['aliases']:
                caps = {int(k): v for k, v in (policies[alias['policy']]['caps'] | self.spec['free_caps']).items()}
                self.assertTrue(all(r['rank'] <= caps.get(r['ability_id'], 0) for r in ranks))

    def test_all_means_pool_exhaustion_and_500_cannot_invent_spend(self):
        costs = {}
        for allocation in allocation_plan(self.catalog, self.spec):
            for alias in allocation['aliases']:
                if alias['requested'] == 'all':
                    self.assertTrue(alias['pool_exhausted'])
                    self.assertEqual(alias['spent'], alias['pool_cost'])
                    costs[(allocation['profile'], alias['policy'])] = alias['spent']
                if alias['requested'] == 500:
                    self.assertTrue(alias['pool_exhausted'])
                    self.assertEqual(alias['unused_points'], 500-alias['spent'])
        self.assertEqual(costs, {('war-clr-wiz', 'launch_core'): 135, ('war-clr-wiz', 'later_core'): 261,
                                 ('war-clr-mnk', 'launch_core'): 141, ('war-clr-mnk', 'later_core'): 288,
                                 ('mag-nec-shm', 'launch_core'): 165, ('mag-nec-shm', 'later_core'): 306})

    def test_zero_baseline_is_explicit_and_shared(self):
        catalogs = {b['profile']: {r['rank_id']: r for r in b['aa_catalog']} for b in self.catalog['builds']}
        zeros = [a for a in allocation_plan(self.catalog, self.spec) if a['spent'] == 0]
        self.assertEqual(len(zeros), 3)
        for a in zeros:
            self.assertEqual({catalogs[a['profile']][r]['ability_id'] for r in a['rank_ids']}, {331, 938, 2220})
            self.assertEqual({x['policy'] for x in a['aliases']}, {'launch_core', 'later_core'})

    def test_removed_prerequisite_is_not_reintroduced(self):
        spec = copy.deepcopy(self.spec)
        spec['policies'][0]['caps']['398'] = 3
        plan = allocation_plan(self.catalog, spec)
        ranks = {r['rank_id']: r for b in self.catalog['builds'] for r in b['aa_catalog']}
        launch = [a for a in plan if any(x['policy'] == 'launch_core' and x['requested'] == 'all' for x in a['aliases'])]
        self.assertTrue(all(not any(ranks[i]['ability_id'] == 398 for i in a['rank_ids']) for a in launch))
        self.assertTrue(any(x['unreachable'] for a in launch for x in a['aliases'] if x['policy'] == 'launch_core'))

    def test_duplicate_or_invalid_policy_is_rejected(self):
        for mutate in (lambda s: s['policies'].append(copy.deepcopy(s['policies'][0])),
                       lambda s: s['policies'][0]['caps'].update({'999999': 1}),
                       lambda s: s['policies'][0]['caps'].update({'28': -1}),
                       lambda s: s['policies'][0]['budgets'].append(100)):
            spec = copy.deepcopy(self.spec)
            mutate(spec)
            with self.assertRaises(ValueError):
                allocation_plan(self.catalog, spec)

    def test_later_pool_retains_earned_launch_ranks(self):
        plan = allocation_plan(self.catalog, self.spec)
        full = {(a['profile'], x['policy']): set(a['rank_ids']) for a in plan for x in a['aliases'] if x['requested'] == 'all'}
        for profile in ('war-clr-wiz', 'war-clr-mnk', 'mag-nec-shm'):
            self.assertLess(full[(profile, 'launch_core')], full[(profile, 'later_core')])
            for policy in ('launch_core', 'later_core'):
                stages = {x['requested']: a['rank_ids'] for a in plan if a['profile'] == profile
                          for x in a['aliases'] if x['policy'] == policy}
                for before, after in zip((0, 100, 200, 500), (100, 200, 500, 'all')):
                    self.assertEqual(stages[before], stages[after][:len(stages[before])])

    def test_matrix_regenerates_and_deduplicates_identical_allocations(self):
        matrix = self.read('release-pool-inputs.json')
        self.assertEqual(matrix, prepare(self.catalog, self.spec, self.read('gear-expanded-aa-inputs.json'),
                                         self.read('melee-inputs.json'), self.read('pet-belly-inputs.json'),
                                         matrix['binary_sha256']))
        self.assertEqual((len(matrix['allocations']), len(matrix['cases'])), (18, 108))
        self.assertEqual(len({json.dumps([c['input'], c['seed']], sort_keys=True) for c in matrix['cases']}), 108)


if __name__ == '__main__':
    unittest.main()
