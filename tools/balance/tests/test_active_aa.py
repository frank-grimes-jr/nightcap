import copy
import gzip
import json
from pathlib import Path
import unittest

from active_aa_controls import prepare, prepare_encounters, verify, verify_case, verify_encounter, verify_encounters


DOCS = Path(__file__).resolve().parents[3] / 'docs' / 'balance'


class ActiveAAControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((DOCS / 'active-aa-inputs.json').read_text())
        cls.evidence = json.loads(gzip.decompress((DOCS / 'active-aa-controls.json.gz').read_bytes()))

    def control(self, name):
        case = next(c for c in self.matrix['cases'] if c['id'] == name)
        report = next(r['report'] for r in self.evidence['runs'] if r['id'] == name)
        return copy.deepcopy(case), copy.deepcopy(report)

    def test_recorded_native_lifecycles_and_solo_arbitration(self):
        self.assertEqual(len(verify(self.matrix, self.evidence)), 14)

    def test_missing_actions_wrong_seed_and_incomplete_trace_fail(self):
        mutations = [lambda r: r['aa_probe']['actions'].pop(),
                     lambda r: r.update(native_rng_seed=1),
                     lambda r: r['aa_probe']['trace'].pop()]
        for mutate in mutations:
            case, report = self.control('200-tenacity')
            mutate(report)
            with self.assertRaises(ValueError):
                verify_case(case, report)

    def test_cooldown_collision_cannot_be_reported_as_success(self):
        for field, value in [('started', True), ('timer_before', 0), ('timer_after', 900)]:
            case, report = self.control('200-tenacity')
            report['aa_probe']['actions'][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_case(case, report)

    def test_level_rejection_requires_native_message_and_rule(self):
        case, report = self.control('200-regeneration')
        report['aa_probe']['events'] = []
        with self.assertRaises(ValueError):
            verify_case(case, report)
        case, report = self.control('200-regeneration')
        report['aa_probe']['actions'][0]['buff_level_restrictions'] = False
        with self.assertRaises(ValueError):
            verify_case(case, report)

    def test_missing_or_duplicate_controls_fail(self):
        for runs in (self.evidence['runs'][:-1], self.evidence['runs'] + [self.evidence['runs'][0]]):
            with self.assertRaises(ValueError):
                verify(self.matrix, {'runs': runs})

    def test_arbitration_cannot_silently_heal_solo(self):
        evidence = copy.deepcopy(self.evidence)
        report = next(r['report'] for r in evidence['runs'] if r['id'] == '200-arbitration')
        report['aa_probe']['trace'][-1]['hp'] += 100
        with self.assertRaises(ValueError):
            verify(self.matrix, evidence)

    def test_regeneration_and_tenacity_are_not_assumed_freely_stackable(self):
        source = json.loads((DOCS / 'movement-matrix-inputs.json').read_text())
        catalog = json.loads((DOCS / 'native-aa-catalog.json').read_text())
        controls = prepare(source, catalog)
        self.assertEqual(controls['cases'], self.matrix['cases'])
        encounters = prepare_encounters(source)
        self.assertEqual(len(encounters['cases']), 144)
        for case in encounters['cases']:
            original = next(c for c in source['cases'] if case['id'].startswith(c['id']+'-burst'))
            self.assertEqual(case['input']['builds'], original['input']['builds'])


class ActiveAAEncounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((DOCS / 'active-aa-encounter-inputs.json').read_text())
        cls.evidence = json.loads(gzip.decompress((DOCS / 'active-aa-encounters.json.gz').read_bytes()))

    def control(self):
        identity = '32040-ring41-200-balanced-1729-burst'
        case = next(c for c in self.matrix['cases'] if c['id'] == identity)
        report = next(r['report'] for r in self.evidence['runs'] if r['id'] == identity)
        return copy.deepcopy(case), copy.deepcopy(report)

    def test_all_native_encounters_and_serialized_summary_keys(self):
        self.assertEqual(len(verify_encounters(self.matrix, self.evidence)), 144)

    def test_disappearing_twincast_is_not_ten_consumed_charges(self):
        case, report = self.control()
        self.assertEqual(verify_encounter(case, report)['twincast_observed_charge_decrements'], 0)

    def test_charge_increase_is_rejected(self):
        case, report = self.control()
        state = next(s for s in report['encounter']['trace'] if s['ms'] == 500)
        state['aa_state']['buffs'][0]['hits'] = 11
        with self.assertRaises(ValueError):
            verify_encounter(case, report)

    def test_missing_activation_or_unowned_rank_is_rejected(self):
        for missing in (True, False):
            case, report = self.control()
            actions = report['encounter']['activated_aa']['actions']
            if missing:
                actions.pop(0)
            else:
                actions[0]['rank_id'] = 13663
            with self.assertRaises(ValueError):
                verify_encounter(case, report)


if __name__ == '__main__':
    unittest.main()
