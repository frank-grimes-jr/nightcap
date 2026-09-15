import unittest

from resources import base_hp, base_mana, max_hp, max_mana, worn_stat, heroic_resources


ROWS = [
    {'level': 50, 'class': 1, 'hp': 1500, 'hp_fac': 5, 'mana': 0, 'mana_fac': 0},
    {'level': 50, 'class': 2, 'hp': 1320, 'hp_fac': 4.4, 'mana': 900, 'mana_fac': 4.5},
    {'level': 50, 'class': 12, 'hp': 1200, 'hp_fac': 4, 'mana': 900, 'mana_fac': 4.5},
]


class ResourceTests(unittest.TestCase):
    def test_stamina_soft_breakpoint(self):
        self.assertEqual(base_hp((1,), 50, 255, 0, ROWS), 2780)
        self.assertEqual(base_hp((1,), 50, 256, 0, ROWS), 2780)
        self.assertEqual(base_hp((1,), 50, 257, 0, ROWS), 2785)

    def test_best_hp_uses_base_data_hp_not_final_formula(self):
        rows = [dict(ROWS[0], hp_fac=1), dict(ROWS[1], hp_fac=20)]
        self.assertEqual(base_hp((2, 1), 50, 100, 250, rows), 1855)

    def test_mana_chooses_result_and_casting_stat(self):
        self.assertEqual(base_mana((1, 2, 12), 50, 100, 200, 0, ROWS), 2475)
        self.assertEqual(base_mana((1,), 50, 425, 425, 0, ROWS), 0)

    def test_odd_stat_above_200_truncates_toward_zero(self):
        self.assertEqual(base_mana((12,), 50, 200, 1, 0, ROWS), 2475)
        self.assertEqual(base_mana((12,), 50, 201, 1, 0, ROWS), 2484)
        self.assertEqual(base_mana((12,), 50, 202, 1, 0, ROWS), 2484)

    def test_fractional_hp_truncates_before_heroics(self):
        self.assertEqual(base_hp((2,), 50, 101, 10, ROWS), 1779)

    def test_hp_percent_includes_items_but_not_flat_bonus(self):
        self.assertEqual(max_hp(2000, 1000, percent=1500, flat=500, leadership=100), 4050)

    def test_float32_rounding_at_large_hp_matches_engine_precision(self):
        self.assertEqual(max_hp(16777217, 0), 16777216)

    def test_mana_additions_and_noncaster_gate(self):
        self.assertEqual(max_mana((1,), 0, 1000), 0)
        self.assertEqual(max_mana((1, 2), 2475, 1000, spell=200, aa=50, leadership=10), 3735)
        self.assertEqual(max_mana((2,), 1, -10), 0)

    def test_heroics_add_stat_and_raise_cap(self):
        self.assertEqual(worn_stat(100, 500, 50, 425), 475)
        self.assertEqual(worn_stat(100, 50, 25, 425), 175)
        self.assertEqual(worn_stat(1, -100, 0, 425), 1)

    def test_heroic_mana_uses_base_class_not_held_casting_class(self):
        self.assertEqual(heroic_resources(1, 25, 50, 30), (250, 0))
        self.assertEqual(heroic_resources(13, 25, 50, 30), (250, 500))
        self.assertEqual(heroic_resources(2, 25, 50, 30), (250, 300))
        self.assertEqual(heroic_resources(8, 25, 50, 30), (250, 0))

    def test_incomplete_or_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            base_hp((1, 7), 50, 100, 0, ROWS)
        with self.assertRaises(ValueError):
            base_hp((), 50, 100, 0, ROWS)
        with self.assertRaises(ValueError):
            base_mana((17,), 50, 100, 100, 0, ROWS)
        with self.assertRaises(ValueError):
            base_hp((1,), 50, 0, 0, ROWS)
