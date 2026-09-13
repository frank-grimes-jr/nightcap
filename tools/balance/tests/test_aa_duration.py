import copy
import gzip
import json
from pathlib import Path
import unittest

from aa_duration_controls import verify, verify_case


DOCS = Path(__file__).resolve().parents[3] / 'docs' / 'balance'


class AADurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((DOCS / 'duration-inputs.json').read_text())
        cls.evidence = json.loads(gzip.decompress((DOCS / 'duration-controls.json.gz').read_bytes()))
        cls.baseline = json.loads(gzip.decompress((DOCS / 'active-aa-controls.json.gz').read_bytes()))

    def control(self, name, evidence=None):
        case = next(c for c in self.matrix['cases'] if c['id'] == name)
        report = next(r['report'] for r in (evidence or self.evidence)['runs'] if r['id'] == name)
        return copy.deepcopy(case), copy.deepcopy(report)

    def test_native_controls_and_unchanged_comparators(self):
        result = verify(self.matrix, self.evidence, self.baseline)
        self.assertEqual(len(result['controls']), 18)
        self.assertEqual(len(result['unchanged_native_controls']), 6)

    def test_old_permanent_aa_behavior_is_rejected(self):
        for name in ('200-tenacity', 'all-tenacity', '200-twincast', 'all-twincast'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                verify_case(*self.control(name, self.baseline))

    def test_preparation_observation_allows_one_elapsed_tick(self):
        case, report = self.control('200-preparation-67')
        self.assertEqual(verify_case(case, report)['maximum_observed_ticks'], 999999)

    def test_finite_or_missing_preparation_buff_is_rejected(self):
        for replacement in (720, None):
            case, report = self.control('200-preparation-67')
            for state in report['aa_probe']['trace']:
                if replacement is None:
                    state['buffs'] = []
                else:
                    for buff in state['buffs']:
                        buff['ticks'] = min(buff['ticks'], replacement)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                verify_case(case, report)

    def test_missing_control_or_changed_build_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['runs'].pop()
        with self.assertRaises(ValueError):
            verify(self.matrix, evidence, self.baseline)
        evidence = copy.deepcopy(self.evidence)
        evidence['runs'][0]['report']['builds'][0]['hp'] += 1
        with self.assertRaises(ValueError):
            verify(self.matrix, evidence, self.baseline)


if __name__ == '__main__':
    unittest.main()
