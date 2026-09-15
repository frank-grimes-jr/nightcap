import copy
import gzip
import json
from pathlib import Path
import unittest

from pet_belly_controls import prepare, summarize, verify


class BellyCastingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.matrix = cls.read('pet-belly-inputs.json')
        cls.evidence = cls.read('pet-belly.json.gz')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_thirty_native_reports_reproduce_summaries(self):
        self.assertEqual(len(verify(self.matrix, self.evidence)), 30)

    def test_only_approach_policy_changes_in_matched_inputs(self):
        old = self.read('pet-support-inputs.json')
        self.assertEqual(self.matrix, prepare(old, self.matrix['binary_sha256']))
        for before, after in zip(old['cases'], self.matrix['cases']):
            changed = copy.deepcopy(after['input'])
            changed['pet_probe']['combat'].pop('approach_policy')
            self.assertEqual(before['input'], changed)

    def test_offensive_spells_require_native_belly_range(self):
        case = self.matrix['cases'][0]
        report = copy.deepcopy(next(r['report'] for r in self.evidence['runs'] if r['id'] == case['id']))
        combat = report['pet_probe']['combat']
        action = next(a for a in combat['owner_actions'] if a['target'] == combat['boss_id'])
        action['owner_combat_range'] = False
        with self.assertRaisesRegex(ValueError, 'Offensive cast'):
            summarize(case, report)

    def test_disabled_range_immunity_is_not_a_valid_control(self):
        case = self.matrix['cases'][0]
        report = copy.deepcopy(next(r['report'] for r in self.evidence['runs'] if r['id'] == case['id']))
        report['pet_probe']['combat']['range_immunity'] = False
        with self.assertRaisesRegex(ValueError, 'require native belly'):
            summarize(case, report)

    def test_native_control_can_interrupt_but_not_fabricate_movement(self):
        run = next(r for r in self.evidence['runs'] if any(not e['accepted'] for e in r['report']['pet_probe']['combat']['movement']['events']))
        case = next(c for c in self.matrix['cases'] if c['id'] == run['id'])
        report = copy.deepcopy(run['report'])
        event = next(e for e in report['pet_probe']['combat']['movement']['events'] if not e['accepted'])
        self.assertTrue(event['controlled_after'])
        self.assertFalse(event['controlled'])
        event['controlled_after'] = False
        with self.assertRaisesRegex(ValueError, 'without native control'):
            summarize(case, report)

    def test_legacy_native_reports_remain_byte_identical(self):
        pairs = [('pet-support.json.gz', 'pet-belly-legacy-support.json.gz'),
                 ('pet-support-command-regression.json.gz', 'pet-belly-command-regression.json.gz'),
                 ('pet-support-ownership-regression.json.gz', 'pet-belly-ownership-regression.json.gz'),
                 ('pet-support-encounter-regression.json.gz', 'pet-belly-encounter-regression.json.gz')]
        for before, after in pairs:
            old = {r['id']: r for r in self.read(before)['runs']}
            new = self.read(after)['runs']
            self.assertEqual(set(old), {r['id'] for r in new})
            for run in new:
                self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])


if __name__ == '__main__':
    unittest.main()
