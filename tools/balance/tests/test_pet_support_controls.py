import copy
import gzip
import json
from pathlib import Path
import unittest

from pet_support_controls import prepare, summarize, verify, gems_for


class PetSupportEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3]/'docs/balance'
        cls.matrix = cls.read('pet-support-inputs.json')
        cls.evidence = cls.read('pet-support.json.gz')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def sample(self):
        case = self.matrix['cases'][0]
        run = next(r for r in self.evidence['runs'] if r['id'] == case['id'])
        return case, copy.deepcopy(run['report'])

    def test_thirty_native_fights_reproduce_summaries(self):
        self.assertEqual(len(verify(self.matrix, self.evidence)), 30)

    def test_matrix_is_reproducible_and_holds_gear_fixed(self):
        positions = {c['input']['pet_probe']['combat']['npc_id']: c['input']['pet_probe']['combat']['npc_position']
                     for c in self.matrix['cases']}
        self.assertEqual(self.matrix, prepare(self.read('pet-ownership-inputs.json'), positions,
                                              self.matrix['binary_sha256']))
        gear = self.matrix['cases'][0]['input']['builds'][0]['equipment']
        self.assertTrue(all(c['input']['builds'][0]['equipment'] == gear for c in self.matrix['cases']))
        for case in self.matrix['cases']:
            if case['input']['builds'][0]['aa_stage'] == 'all':
                self.assertEqual(case['aa_pool'], 'unrestricted stress test')

    def test_recovery_cannot_inject_resources_before_combat(self):
        case, report = self.sample()
        report['pet_probe']['combat']['trace'][0]['player']['mana'] += 1
        with self.assertRaisesRegex(ValueError, 'Resources changed'):
            summarize(case, report)

    def test_full_mana_and_pet_hp_are_required(self):
        case, report = self.sample()
        report['pet_probe']['recovery']['trace'][-1]['pets'][0]['hp'] -= 1
        with self.assertRaisesRegex(ValueError, 'recovery incomplete'):
            summarize(case, report)

    def test_wrong_gem_or_target_is_rejected(self):
        case, report = self.sample()
        report['pet_probe']['combat']['owner_actions'][0]['gem'] = 99
        with self.assertRaisesRegex(ValueError, 'fixed gem'):
            summarize(case, report)
        case, report = self.sample()
        report['pet_probe']['combat']['owner_actions'][0]['target'] = 999
        with self.assertRaisesRegex(ValueError, 'support target'):
            summarize(case, report)

    def test_boss_specific_elements_and_native_actions(self):
        self.assertIn(510, gems_for(32040))
        self.assertIn(120, gems_for(73057))
        for boss in (32040, 73057):
            self.assertEqual(len(set(gems_for(boss))), 8)
        actions = [a for r in self.evidence['runs'] for a in r['report']['pet_probe']['combat']['owner_actions']]
        self.assertTrue(any(a['reason'] == 'pet_heal' and a['accepted'] and a.get('target_hp_after', 0)
                            and a['target_hp_after'] > a['target_hp_before'] for a in actions))
        ledger = [e for r in self.evidence['runs'] for e in r['report']['pet_probe']['combat']['damage_ledger']]
        self.assertTrue(any(e['spell'] in (510, 120) and e['hp_after'] < e['hp_before'] for e in ledger))

    def test_unearned_victory_and_incomplete_matrix_are_rejected(self):
        case, report = self.sample()
        report['pet_probe']['combat']['result'] = 'boss_death'
        with self.assertRaisesRegex(ValueError, 'terminal HP'):
            summarize(case, report)
        evidence = copy.deepcopy(self.evidence)
        evidence['runs'].pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            verify(self.matrix, evidence)

    def test_preparation_waits_for_native_recast_and_aa_must_be_owned(self):
        waited = 0
        for run in self.evidence['runs']:
            report = run['report']
            probe = report['pet_probe']
            waited += sum(a['recast_wait_ms'] for a in probe['actions'])
            self.assertFalse(any(e.get('string_id') == 236 for e in probe['events']))
            purchased = {p['rank_id'] for p in report['builds'][0]['aa_purchases']}
            for aa in probe['combat']['activated_aa']:
                self.assertIn(aa['rank_id'], purchased)
        self.assertGreater(waited, 0)

    def test_movement_cannot_teleport(self):
        run = next(r for r in self.evidence['runs'] if r['report']['pet_probe']['combat']['movement']['events'])
        case = next(c for c in self.matrix['cases'] if c['id'] == run['id'])
        report = copy.deepcopy(run['report'])
        report['pet_probe']['combat']['movement']['events'][0]['to'][0] += 100
        with self.assertRaisesRegex(ValueError, 'exceeds native speed'):
            summarize(case, report)

    def test_prior_commands_ownership_and_fights_are_unchanged(self):
        for old_name, new_name in [('pet-command-after.json.gz', 'pet-support-command-regression.json.gz'),
                                   ('pet-command-ownership-regression.json.gz', 'pet-support-ownership-regression.json.gz'),
                                   ('pet-command-encounter-regression.json.gz', 'pet-support-encounter-regression.json.gz')]:
            old = {r['id']: r for r in self.read(old_name)['runs']}
            runs = self.read(new_name)['runs']
            self.assertEqual(set(old), {r['id'] for r in runs})
            for run in runs:
                self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])


if __name__ == '__main__':
    unittest.main()
