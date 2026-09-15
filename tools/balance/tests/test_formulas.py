import unittest

from formulas import SpellRules, extra_spell_amount, spell_amount


class SpellFormulaTests(unittest.TestCase):
    def test_current_direct_spell_and_cap(self):
        rules = SpellRules(flat=True, percent=True)
        self.assertEqual(spell_amount(1000, 440, 250, rules), 3500)
        self.assertEqual(spell_amount(1000, 440, 500, rules), 5400)
        self.assertEqual(spell_amount(1000, 500, 500, rules), 6000)

    def test_damage_sign_does_not_change_bonus_magnitude(self):
        rules = SpellRules(flat=True, percent=True)
        self.assertEqual(extra_spell_amount(-1000, 250, rules), 2500)

    def test_dot_and_hot_split_bonus_not_base(self):
        rules = SpellRules(flat=True, percent=True)
        self.assertEqual(spell_amount(100, 250, 250, rules, duration=10, split=True), 125)
        self.assertEqual(spell_amount(100, 250, 250, rules, duration=10, split=False), 350)

    def test_spell_exclusion_and_disabled_periodic_scaling(self):
        rules = SpellRules(flat=True, percent=True)
        self.assertEqual(spell_amount(100, 250, 250, rules, eligible=False), 100)

    def test_percentage_truncation_then_duration_truncation(self):
        rules = SpellRules(flat=True, percent=True)
        self.assertEqual(spell_amount(3, 50, 250, rules, duration=2, split=True), 3)

    def test_stock_timing_and_half_base_clamp(self):
        stock = SpellRules(flat=False, percent=False)
        self.assertEqual(extra_spell_amount(1000, 100, stock, cast_ms=2000), 25)
        self.assertEqual(extra_spell_amount(100, 1000, stock, cast_ms=7000), 50)
        self.assertEqual(extra_spell_amount(1000, 100, stock, cast_ms=0), 0)

    def test_nonflat_percent_branch_is_not_a_noop(self):
        rules = SpellRules(flat=False, percent=True)
        self.assertEqual(extra_spell_amount(1000, 100, rules, cast_ms=2000), 250)

    def test_recast_and_recovery_use_larger_interval(self):
        stock = SpellRules(flat=False, percent=False)
        self.assertEqual(extra_spell_amount(1000, 100, stock, cast_ms=2000, recast_ms=1000, recovery_ms=5000), 100)

    def test_invalid_inputs_fail_instead_of_fabricating_output(self):
        for kwargs in ({'cap': -1}, {'duration': -1}, {'base': -1}, {'cast_ms': -1}):
            args = {'base': 100, 'worn_bonus': 20, 'cap': 250, 'rules': SpellRules(True, True)}
            args.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                spell_amount(**args)
