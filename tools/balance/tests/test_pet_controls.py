import copy
import gzip
import json
from pathlib import Path
import unittest

from pet_controls import assess_ownership, prepare, summarize, verify


class PetOwnershipTests(unittest.TestCase):
    def fixture(self):
        return {'primary_pet': 2, 'class_pets': [
            {'class': 10, 'entity_id': 4}, {'class': 11, 'entity_id': 3},
            {'class': 13, 'entity_id': 0}], 'pets': [
                {'entity_id': 2, 'owner_id': 1, 'spell': 633, 'depop': False},
                {'entity_id': 3, 'owner_id': 1, 'spell': 443, 'depop': False},
                {'entity_id': 4, 'owner_id': 1, 'spell': 166, 'depop': False}]}

    def test_three_real_owned_pets_satisfy_roster(self):
        result = assess_ownership(self.fixture(), 1, [633, 443, 166])
        self.assertTrue(result['ready'])
        self.assertEqual(result['pet_spells'], [166, 443, 633])

    def test_stale_registry_is_not_a_surviving_pet(self):
        state = self.fixture()
        state['pets'] = state['pets'][:1]
        result = assess_ownership(state, 1, [633, 443, 166])
        self.assertFalse(result['ready'])
        self.assertEqual(result['dangling_references'], [3, 4])

    def test_wrong_owner_and_depop_fail_even_with_correct_spell_ids(self):
        for key, value in [('owner_id', 0), ('depop', True)]:
            state = self.fixture()
            state['pets'][1][key] = value
            with self.subTest(key=key):
                self.assertFalse(assess_ownership(state, 1, [633, 443, 166])['ready'])

    def test_untracked_duplicate_or_missing_pets_fail(self):
        for mutate in [lambda s: s['class_pets'][0].update(entity_id=0),
                       lambda s: s['pets'].append(copy.deepcopy(s['pets'][0])),
                       lambda s: s['pets'].clear()]:
            state = self.fixture()
            mutate(state)
            self.assertFalse(assess_ownership(state, 1, [633, 443, 166])['ready'])

    def test_no_reagent_control_expects_no_pets_or_references(self):
        state = {'primary_pet': 0, 'class_pets': [], 'pets': []}
        self.assertTrue(assess_ownership(state, 1, [])['ready'])
        self.assertFalse(assess_ownership(self.fixture(), 1, [])['ready'])


class NativePetEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.before_inputs = cls.read('pet-inputs.json')
        cls.after_inputs = cls.read('pet-ownership-inputs.json')
        cls.before = cls.read('pet-before-ownership.json.gz')
        cls.after = cls.read('pet-after-ownership.json.gz')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def case(self, identity):
        return (next(c for c in self.after_inputs['cases'] if c['id'] == identity),
                next(r['report'] for r in self.after['runs'] if r['id'] == identity))

    def test_original_failure_and_corrected_pet_rosters(self):
        before = verify(self.before_inputs, self.before)
        after = verify(self.after_inputs, self.after)
        self.assertEqual(sum(s['assessment']['ready'] for s in before), 3)
        self.assertEqual(len(after), 15)
        self.assertTrue(all(s['assessment']['ready'] for s in after))

    def test_inputs_regenerate_and_thirteen_original_controls_remain_matched(self):
        regenerated = prepare(self.read('gear-expanded-inputs.json'), self.read('native-aa-inputs.json'),
                              self.after_inputs['binary_sha256'])
        self.assertEqual(regenerated, self.after_inputs)
        self.assertEqual(self.before_inputs['cases'], self.after_inputs['cases'][:13])

    def test_native_reagent_gate_consumes_one_supplied_malachite(self):
        _, missing = self.case('mage-missing-reagent')
        _, supplied = self.case('mage-with-reagent')
        self.assertEqual(missing['pet_probe']['final']['pets'], [])
        initial = supplied['pet_probe']['initial']['reagents'][0]
        final = supplied['pet_probe']['final']['reagents'][0]
        self.assertEqual((initial['id'], initial['count'], final['id'], final['count']), (10015, 10, 10015, 9))

    def test_native_burnout_affects_primary_pet_and_extra_pets_survive(self):
        _, report = self.case('triple-0')
        action = report['pet_probe']['actions'][-1]
        self.assertEqual(action['input'], {'spell': 107, 'target_class': 13})
        before = next(p for p in action['before']['pets'] if p['spell'] == 633)
        after = next(p for p in action['settled']['pets'] if p['spell'] == 633)
        self.assertEqual((before['haste'], after['haste']), (100, 160))
        self.assertTrue(any(b['spell'] == 107 for b in after['buffs']))
        self.assertEqual(len(action['settled']['pets']), 3)

    def test_native_pet_hp_scales_with_matched_aa_allocations(self):
        expected = [('0', 0, 2520), ('100', 100, 2545), ('200', 199, 2646),
                    ('500', 494, 3099), ('all', 13288, 3402)]
        gear = None
        for stage, spent, hp in expected:
            case, report = self.case('triple-' + stage)
            equipment = case['input']['builds'][0]['equipment']
            if gear is not None:
                self.assertEqual(gear, equipment)
            gear = equipment
            self.assertEqual(report['builds'][0]['aa_spent'], spent)
            water = next(p for p in report['pet_probe']['final']['pets'] if p['spell'] == 633)
            self.assertEqual(water['max_hp'], hp)

    def test_native_orphan_control_rejects_sticky_ownership(self):
        case, report = self.case('unregistered-owner_or_self')
        changed = copy.deepcopy(report)
        changed['pet_probe']['owner_lookup_control']['unregistered_owner_id'] = 1
        with self.assertRaisesRegex(ValueError, 'orphan'):
            summarize(case, changed)

    def test_native_reports_reject_wrong_spend_and_equipment(self):
        case, report = self.case('triple-100')
        changed = copy.deepcopy(report)
        changed['builds'][0]['aa_spent'] = 101
        with self.assertRaises(ValueError):
            summarize(case, changed)
        changed = copy.deepcopy(report)
        changed['builds'][0]['equipped_items'].pop()
        with self.assertRaises(ValueError):
            summarize(case, changed)

    def test_eight_unrelated_native_encounters_remain_byte_identical(self):
        old = {r['id']: r for r in self.read('melee-encounters.json.gz')['runs']}
        newer = self.read('pet-encounter-regressions.json.gz')['runs']
        self.assertEqual(len(newer), 8)
        for run in newer:
            self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'], old[run['id']]['report'])


if __name__ == '__main__':
    unittest.main()
