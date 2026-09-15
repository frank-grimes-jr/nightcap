import copy
from pathlib import Path
import re
import unittest

from aa_policy_preflight import read_json
from cap_controls import VARIANTS, prepare, rule_sql, verify


class CapEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3] / 'docs/balance'
        cls.matrix = cls.read('cap-experiment-inputs.json')
        cls.baseline = cls.read('gear-source.json.gz')
        cls.catalog = cls.read('native-aa-catalog.json')

    @classmethod
    def read(cls, name):
        return read_json(cls.docs / name)

    def test_all_162_native_fights_verify_and_inputs_regenerate(self):
        binary = self.read('aa-ownership-after-build.json')['binary_sha256']
        self.assertEqual(self.matrix, prepare(self.read('gear-source-inputs.json'), binary))
        checks = self.read('cap-experiment-checks.json')
        self.assertTrue(checks['completed'])
        self.assertEqual([p['variant'] for p in checks['phases']], list(VARIANTS))
        for phase in checks['phases']:
            evidence = self.read('cap-' + phase['variant'] + '.json.gz')
            self.assertEqual(len(evidence['runs']), 54)
            self.assertEqual(verify(self.matrix, evidence, self.baseline, phase['variant'], self.catalog),
                             phase['groups'])
            self.assertEqual(len(phase['groups']), 18)
            self.assertTrue(all(g['samples'] == 3 for g in phase['groups']))
        baseline = {r['id']: r for r in self.baseline['runs']}
        melee = [r for r in self.read('cap-damage300.json.gz')['runs']
                 if r['summary']['profile'] == 'war-clr-mnk']
        self.assertEqual(len(melee), 18)
        for run in melee:
            report = copy.deepcopy(run['report'])
            report['builds'][0]['spell_damage'] = 250
            self.assertEqual(report, baseline[run['id']]['report'])

    def test_wrong_effective_cap_or_changed_character_stats_are_rejected(self):
        original = self.read('cap-healing300.json.gz')
        for field, value, message in [('heal_amount', 250, 'effective caps'),
                                       ('str', 999999, 'Non-cap build')]:
            evidence = copy.deepcopy(original)
            evidence['runs'][0]['report']['builds'][0][field] = value
            with self.assertRaisesRegex(ValueError, message):
                verify(self.matrix, evidence, self.baseline, 'healing300', self.catalog)

    def test_generated_transactions_and_all_rule_restorations_match(self):
        checks = self.read('cap-experiment-checks.json')
        final = self.read('cap-final-checks.json')
        self.assertEqual(final['restored_rules_tsv'], checks['original_rules_tsv'])
        self.assertEqual(final['rule_values_engine'], 'InnoDB')
        self.assertEqual(final['remaining_rows'], {'account': 0, 'character_data': 0,
                                                  'character_alternate_abilities': 0, 'inventory': 0})
        self.assertEqual(final['temporary_procedures'], 0)
        rollback = self.read('cap-rollback-check.json')
        self.assertTrue(rollback['restored_exactly'])
        self.assertEqual(rollback['before_rules_tsv'], checks['original_rules_tsv'])
        self.assertEqual(rollback['after_rules_tsv'], checks['original_rules_tsv'])
        self.assertIn('Cap precondition changed', rollback['error'])
        rejected = (self.docs / 'cap-rollback-rejection.sql').read_text(encoding='utf-8')
        procedure = re.search(r'CREATE PROCEDURE `([^`]+)`', rejected).group(1)
        self.assertEqual(rejected, rule_sql((250, 300), (300, 250), procedure))
        for phase in checks['phases']:
            self.assertTrue(phase['restored_exactly'])
            self.assertEqual(phase['restored_rules_tsv'], checks['original_rules_tsv'])
            variant = phase['variant']
            for mode, before, after in [('apply', (250, 250), VARIANTS[variant]),
                                         ('restore', VARIANTS[variant], (250, 250))]:
                statement = (self.docs / f'cap-{variant}-{mode}.sql').read_text(encoding='utf-8')
                procedure = re.search(r'CREATE PROCEDURE `([^`]+)`', statement).group(1)
                self.assertEqual(statement, rule_sql(before, after, procedure))
            rows = [r.split('\t') for r in phase['applied_rules_tsv'].splitlines()]
            rules = {r[1]: int(r[2]) for r in rows}
            self.assertEqual(rules, {'Character:ItemSpellDmgCap': VARIANTS[variant][0],
                                     'Character:ItemHealAmtCap': VARIANTS[variant][1]})


if __name__ == '__main__':
    unittest.main()
