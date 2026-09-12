import unittest

from snapshot import era_predicate, row_json, DROP_SOURCES
from verify_cpp import extract_function


class SnapshotTests(unittest.TestCase):
    def test_rejects_sql_identifiers_and_noncontent_tables(self):
        with self.assertRaises(ValueError):
            era_predicate('s; DROP TABLE items')
        with self.assertRaises(ValueError):
            row_json('account', 'a')

    def test_rule_export_omits_freeform_notes(self):
        self.assertNotIn('notes', row_json('rule_values', 'r'))

    def test_drop_candidates_have_independent_era_and_chance_gates(self):
        for alias in ('s', 'se', 'ld', 'l', 'd'):
            self.assertIn(era_predicate(alias), DROP_SOURCES)
        for predicate in ('z.expansion=0', 'z.version=0', 'ld.chance>0', 'se.chance>0', 'lt.probability>0'):
            self.assertIn(predicate, DROP_SOURCES)

    def test_disabled_openworld_spawns_are_excluded(self):
        self.assertIn('spawn2_disabled', DROP_SOURCES)
        self.assertIn('sd.instance_id=0', DROP_SOURCES)
        self.assertIn('sd.disabled<>0', DROP_SOURCES)

    def test_extracts_complete_cpp_function_not_following_function(self):
        source = 'int f() { if (true) { return 1; } return 0; }\nint g() { return 2; }'
        self.assertEqual(extract_function(source, 'int f()'), source.split('\n')[0])

    def test_duplicate_or_missing_cpp_function_is_rejected(self):
        for source in ('', 'int f() {} int f() {}', 'int f() {'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                extract_function(source, 'int f()')
