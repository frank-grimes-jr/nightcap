import copy
import gzip
import json
from pathlib import Path
import unittest

from pet_combat_controls import prepare, summarize, verify, assess_commands


class PetCombatEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.before_inputs = cls.read('pet-command-before-inputs.json')
        cls.before = cls.read('pet-command-before.json.gz')
        cls.after_inputs = cls.read('pet-command-after-inputs.json')
        cls.after = cls.read('pet-command-after.json.gz')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_all_command_and_boss_records_reproduce_their_summaries(self):
        old = verify(self.before_inputs, self.before)
        new = verify(self.after_inputs, self.after)
        self.assertEqual((len(old), len(new)), (12, 12))
        self.assertEqual(sum(s['command_boundary']['passed'] for s in old if 'command_boundary' in s), 2)
        self.assertEqual(sum(s['command_boundary']['passed'] for s in new if 'command_boundary' in s), 8)

    def test_inputs_regenerate_and_remain_matched(self):
        positions = {c['input']['pet_probe']['combat']['npc_id']: c['input']['pet_probe']['combat']['npc_position']
                     for c in self.before_inputs['cases']}
        regenerated = prepare(self.read('pet-ownership-inputs.json'), positions, self.after_inputs['binary_sha256'])
        self.assertEqual(regenerated, self.after_inputs)
        self.assertEqual(self.before_inputs['cases'], self.after_inputs['cases'])

    def test_reproduced_out_of_range_damage_is_rejected(self):
        report = next(r['report'] for r in self.before['runs'] if r['id'] == 'command-2-500-extraonly-False')
        combat = report['pet_probe']['combat']
        result = assess_commands(combat)
        self.assertEqual(sum(result['immediate_damage']), 102)
        self.assertFalse(result['passed'])
        self.assertTrue(all(not p['melee_range'] for p in combat['trace'][0]['pets']))

    def test_primary_only_reports_remain_byte_identical(self):
        old = {r['id']: r for r in self.before['runs']}
        for run in self.after['runs']:
            if run['id'].endswith('primaryonly'):
                self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])

    def test_command_schedule_corruption_is_rejected(self):
        case = self.after_inputs['cases'][0]
        report = copy.deepcopy(next(r['report'] for r in self.after['runs'] if r['id'] == case['id']))
        report['pet_probe']['combat']['commands'][0]['input']['command'] = 28
        with self.assertRaisesRegex(ValueError, 'schedule'):
            summarize(case, report)

    def test_native_boss_fights_include_damage_and_actual_pet_deaths(self):
        fights = [r['report']['pet_probe']['combat'] for r in self.after['runs'] if r['id'].startswith('pet-only')]
        self.assertEqual(len(fights), 4)
        self.assertTrue(all(c['damage_ledger'] for c in fights))
        self.assertTrue(any(any(not p['present'] for p in c['trace'][-1]['pets']) for c in fights))
        for combat in fights:
            self.assertFalse(combat['input']['commands_only'])
            loss = sum(max(0, e['hp_before'])-max(0, e['hp_after']) for e in combat['damage_ledger'] if e['depth'] == 0)
            self.assertGreaterEqual(loss, 32000-combat['trace'][-1]['boss_hp'])

    def test_prior_ownership_and_caster_monk_reports_remain_unchanged(self):
        for prior, newer, count in [('pet-after-ownership.json.gz', 'pet-command-ownership-regression.json.gz', 15),
                                    ('pet-encounter-regressions.json.gz', 'pet-command-encounter-regression.json.gz', 8)]:
            old = {r['id']: r for r in self.read(prior)['runs']}
            runs = self.read(newer)['runs']
            self.assertEqual(len(runs), count)
            self.assertEqual(set(old), {r['id'] for r in runs})
            for run in runs:
                self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])
                self.assertEqual(run['report'], old[run['id']]['report'])


if __name__ == '__main__':
    unittest.main()
