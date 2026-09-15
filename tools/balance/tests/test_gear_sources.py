import copy
import json
from pathlib import Path
import unittest

from builds import load_snapshot
from gear_source_controls import prepare, source_items, verify


class GearSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[3]
        cls.original = json.loads((root/'docs/balance/release-pool-inputs.json').read_text(encoding='utf-8'))
        cls.snapshot, cls.manifest = load_snapshot(root/'tools/balance/fixtures/classic-20260912-v2.json.gz')
        cls.matrix = prepare(cls.original, cls.snapshot, cls.manifest['snapshot_sha256'])

    def test_shared_source_survives_and_exclusive_source_tiers_do_not(self):
        snapshot = {'tables': {'items': [{'id': i} for i in (1,200001,2,600002,3)],
                                'drop_sources': [{'item_id': 1, 'npc_id': 10},
                                                 {'item_id': 2, 'npc_id': 10},
                                                 {'item_id': 2, 'npc_id': 20}]}}
        items, sources = source_items(snapshot, [10])
        self.assertEqual([i['id'] for i in items], [2,600002])
        self.assertEqual(sources, {2: [{'item_id': 2, 'npc_id': 20}]})
        for invalid in ([], [99], [10,10], [True]):
            with self.assertRaises(ValueError):
                source_items(snapshot, invalid)

    def test_aa_allocations_encounters_and_seeds_are_unchanged(self):
        self.assertEqual(self.matrix['allocations'], self.original['allocations'])
        self.assertEqual(len(self.matrix['cases']), 108)
        for before, after in zip(self.original['cases'], self.matrix['cases']):
            self.assertEqual(after['paired_case_id'], before['id'])
            self.assertEqual(after['seed'], before['seed'])
            left, right = copy.deepcopy(before['input']), copy.deepcopy(after['input'])
            for value in (left, right):
                for key in ('equipment', 'tier', 'gear_search'):
                    value['builds'][0].pop(key, None)
                if 'pet_probe' in value:
                    value['pet_probe']['combat'].pop('capture_terminal', None)
            self.assertEqual(left, right)

    def test_every_worn_item_and_augment_has_a_surviving_source(self):
        for profile, loadout in self.matrix['gear_source_policy']['loadouts'].items():
            self.assertEqual(len(loadout['equipment']), 20)
            self.assertTrue(all(rows and all(r['npc_id'] != 56182 for r in rows)
                                for rows in loadout['sources'].values()))
            self.assertNotIn('609959', loadout['sources'])
            for case in self.matrix['cases']:
                if case['input']['builds'][0]['profile'] == profile:
                    self.assertEqual(case['input']['builds'][0]['equipment'], loadout['equipment'])

    def test_changed_controller_cannot_masquerade_as_a_gear_comparison(self):
        matrix = copy.deepcopy(self.matrix)
        matrix['cases'][0]['input']['encounter']['duration_ms'] = 1
        with self.assertRaisesRegex(ValueError, 'paired inputs'):
            verify(matrix, {}, self.original, self.snapshot, self.manifest['snapshot_sha256'], {})

    def test_cloak_comparison_keeps_all_monk_allocations_without_repeating_other_roles(self):
        matrix = prepare(self.original, self.snapshot, self.manifest['snapshot_sha256'], monk_cloak36=True)
        self.assertEqual(len(matrix['cases']), 36)
        self.assertEqual(matrix['allocations'], self.original['allocations'])
        loadout = matrix['gear_source_policy']['loadouts']['war-clr-mnk']
        self.assertEqual(loadout['max_raw_worn_haste'], 36)
        self.assertTrue(all(c['input']['builds'][0]['profile'] == 'war-clr-mnk' for c in matrix['cases']))
        self.assertEqual(next(e['id'] for e in loadout['equipment'] if e['slot'] == 8), 611621)
        self.assertEqual({c['allocation_key'] for c in matrix['cases']},
                         {c['allocation_key'] for c in self.original['cases']
                          if c['input']['builds'][0]['profile'] == 'war-clr-mnk'})


if __name__ == '__main__':
    unittest.main()
