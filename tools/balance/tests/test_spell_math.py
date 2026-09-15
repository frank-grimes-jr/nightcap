import unittest

from spell_math import effect_value, buff_duration, resist_outcomes


class SpellMathTests(unittest.TestCase):
    def test_ice_comet_and_superior_healing_use_caps(self):
        self.assertEqual(effect_value(6, -700, 808, 50), -808)
        self.assertEqual(effect_value(10, 200, 600, 50), 600)
        self.assertEqual(effect_value(100, 7500, 0, 55), 7500)

    def test_signed_growth_and_integer_rounding(self):
        self.assertEqual(effect_value(101, -30, -60, 51), -55)
        self.assertEqual(effect_value(110, 10, 0, 50), 18)

    def test_buff_duration_and_permanence(self):
        self.assertEqual(buff_duration(55, 7, 1), 1)
        self.assertEqual(buff_duration(50, 1, 7), 7)
        self.assertEqual(buff_duration(50, 10, 205), 160)
        self.assertEqual(buff_duration(50, 50, 0), -1)

    def test_unresistable_and_immunity(self):
        self.assertEqual(resist_outcomes(1000, 50, 55, no_resist=True), ((201,100),))
        self.assertEqual(resist_outcomes(0, 50, 55, immune=True), ((201,0),))

    def test_zero_resist_still_has_one_nonpartial_failure(self):
        self.assertEqual(dict((pct,n) for n,pct in resist_outcomes(0, 50, 50)), {0:1,100:200})

    def test_nagafen_cold_and_vox_cold_differ(self):
        nagafen = dict((pct,n) for n,pct in resist_outcomes(70,50,55,modifier=-10,partial=True))
        vox = resist_outcomes(1000,50,55,modifier=-10,partial=True)
        self.assertEqual(nagafen[100], 118)  # chance 70-10+12+10=82; roll 83..200
        self.assertEqual(vox, ((201,0),))

    def test_nonpartial_spell_has_no_partial_outcomes(self):
        self.assertEqual(set(p for _,p in resist_outcomes(100,55,50,target_npc=False)), {0,100})

    def test_unsupported_formula_fails_explicitly(self):
        with self.assertRaises(ValueError):
            effect_value(137, 100, 0, 50)
