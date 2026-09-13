import tempfile
import unittest
from pathlib import Path

from baseline import compare_mirror, validate_cpp_summary, validate_rules


class BaselineTests(unittest.TestCase):
    def test_exit_zero_with_failed_assertions_is_failure(self):
        with self.assertRaises(ValueError):
            validate_cpp_summary('Total: 87 tests, 95% correct in 0.00 seconds', 0)

    def test_missing_or_empty_test_summary_is_failure(self):
        for output in ('', 'Total: 0 tests, 100% correct in 0.00 seconds'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                validate_cpp_summary(output, 0)

    def test_complete_cpp_run(self):
        self.assertEqual(validate_cpp_summary('Total: 87 tests, 100% correct in 0.00 seconds', 0), 87)

    def test_nonzero_exit_is_failure_even_with_passing_summary(self):
        with self.assertRaises(ValueError):
            validate_cpp_summary('Total: 87 tests, 100% correct in 0.00 seconds', 1)

    def test_missing_aa_override_is_not_treated_as_enabled(self):
        self.assertIn('Character:AAExpMinLevel', validate_rules({}, {'Character:AAExpMinLevel': '1'}))

    def test_rule_values_must_match(self):
        self.assertEqual(validate_rules({'cap': '250'}, {'cap': '250'}), {})
        self.assertEqual(validate_rules({'cap': '500'}, {'cap': '250'}), {'cap': {'expected': '250', 'actual': '500'}})

    def test_mirror_ignores_only_newline_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mirror, runtime = root / 'server-mods', root / 'akk-stack'
            (mirror / 'code/zone').mkdir(parents=True)
            (runtime / 'code/zone').mkdir(parents=True)
            (mirror / 'code/zone/test.cpp').write_bytes(b'one\r\ntwo\r\n')
            target = runtime / 'code/zone/test.cpp'
            target.write_bytes(b'one\ntwo\n')
            self.assertEqual(compare_mirror(mirror, runtime)['mismatches'], [])
            target.write_bytes(b'one\nthree\n')
            self.assertEqual(compare_mirror(mirror, runtime)['mismatches'], ['code/zone/test.cpp'])
            target.unlink()
            self.assertEqual(compare_mirror(mirror, runtime)['missing'], ['code/zone/test.cpp'])

    def test_empty_mirror_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                compare_mirror(Path(directory), Path(directory))
