import copy
from pathlib import Path
import unittest

from aa_policy_preflight import read_json
from cap_controls import prepare, rule_sql


class CapControlsTests(unittest.TestCase):
    def source(self):
        return read_json(Path(__file__).resolve().parents[3] / 'docs/balance/gear-source-inputs.json')

    def test_selection_keeps_exact_source_cases_and_all_three_progression_stages(self):
        source = self.source()
        frozen = copy.deepcopy(source)
        result = prepare(source, 'candidate')
        self.assertEqual(source, frozen)
        self.assertEqual(len(result['cases']), 54)
        self.assertEqual(result['binary_sha256'], 'candidate')
        original = {c['id']: c for c in source['cases']}
        for case in result['cases']:
            self.assertEqual(case, original[case['id']])

    def test_duplicate_or_missing_seed_is_rejected(self):
        source = self.source()
        source['cases'][0]['seed'] = source['cases'][1]['seed']
        with self.assertRaises(ValueError):
            prepare(source, 'candidate')

    def test_sql_guards_clone_empty_characters_and_exact_old_rule_values(self):
        statement = rule_sql((250, 250), (300, 250), 'cap_test')
        self.assertIn("DATABASE() <> 'nightcap_balance_20260912'", statement)
        self.assertIn('Nonempty character fixture', statement)
        self.assertIn('ROLLBACK; RESIGNAL;', statement)
        self.assertEqual(statement.count('UPDATE rule_values'), 1)
        self.assertIn("rule_name='Character:ItemSpellDmgCap' AND rule_value='250'", statement)
        for before, after, name in [((250, 250), (500, 250), 'cap_test'),
                                     ((250, 250), (300, 250), 'cap_bad`;DROP'),
                                     ((250, True), (300, 250), 'cap_test')]:
            with self.assertRaises(ValueError):
                rule_sql(before, after, name)


if __name__ == '__main__':
    unittest.main()
