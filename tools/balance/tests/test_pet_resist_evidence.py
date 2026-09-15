import copy
import gzip
import json
from pathlib import Path
import unittest

from pet_resist_controls import verify


class PetResistanceNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3] / 'docs/balance'
        cls.original = cls.read('gear-source-inputs.json')
        cls.catalog = cls.read('native-aa-catalog.json')

    @classmethod
    def read(cls, name):
        raw = (cls.docs / name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_full_matrix_and_pilot_verify_native_preparation_and_outcomes(self):
        for stem, count in (('pet-resist', 36), ('pet-resist-pilot', 3)):
            self.assertEqual(len(verify(self.read(stem + '-inputs.json'),
                                        self.read(stem + '.json.gz'),
                                        self.original, self.catalog)), count)

    def test_accepted_cast_does_not_substitute_for_owner_or_pet_buff_retention(self):
        original = self.read('pet-resist-pilot.json.gz')
        for actor in ('player', 0, 1, 2):
            evidence = copy.deepcopy(original)
            probe = evidence['runs'][0]['report']['pet_probe']
            for state in (probe['final'], probe['recovery']['trace'][-1]):
                target = state['player'] if actor == 'player' else state['pets'][actor]
                target['buffs'] = [b for b in target['buffs'] if b['spell'] != 64]
            with self.assertRaisesRegex(ValueError, 'Resist Magic did not survive'):
                verify(self.read('pet-resist-pilot-inputs.json'), evidence,
                       self.original, self.catalog)

    def test_allowlist_addition_preserves_six_original_native_reports(self):
        old = {r['id']: r for r in self.read('gear-source.json.gz')['runs']}
        runs = self.read('pet-resist-regression.json.gz')['runs']
        self.assertEqual(len(runs), 6)
        for run in runs:
            self.assertEqual(run['native_raw_sha256'], old[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'], old[run['id']]['report'])

    def test_full_matrix_reproduces_three_pilot_reports_exactly(self):
        full = {r['id']: r for r in self.read('pet-resist.json.gz')['runs']}
        runs = self.read('pet-resist-pilot.json.gz')['runs']
        self.assertEqual(len(runs), 3)
        for run in runs:
            self.assertEqual(run['native_raw_sha256'], full[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'], full[run['id']]['report'])


if __name__ == '__main__':
    unittest.main()
