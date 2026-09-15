import unittest

from melee import hit_succeeds, damage_interval, npc_damage, legacy_round_attacks, Melee


class MeleeTests(unittest.TestCase):
    def test_hit_order_and_auto_disc_precedence(self):
        self.assertTrue(hit_succeeds(10, 10, 9, 1, False))
        self.assertFalse(hit_succeeds(10, 10, 1, 9, True))
        self.assertTrue(hit_succeeds(10, 10, 5, 5, True))
        self.assertFalse(hit_succeeds(10, 10, 5, 5, False))
        self.assertFalse(hit_succeeds(-1, -1, 0, 0, True))
        self.assertTrue(hit_succeeds(-1, -1, 0, 0, True, sitting=True))

    def test_d20_extremes_and_sitting(self):
        self.assertEqual(damage_interval(500, 500, 0, 504), 0.1)
        self.assertEqual(damage_interval(500, 500, 504, 0), 2.0)
        self.assertEqual(damage_interval(500, 500, 0, 0, sitting=True), 2.0)

    def test_real_dragon_min_max_and_shielding(self):
        self.assertEqual(npc_damage(85, 218, 0.1), 85)
        self.assertEqual(npc_damage(85, 218, 2.0), 218)
        self.assertEqual(npc_damage(85, 218, 2.0, shielding=35), 191)
        self.assertEqual(npc_damage(85, 218, 2.0, damage_modifier=-5), 211)

    def test_active_rounds_double_exactly_305_of_500_rolls_at_55(self):
        class FixedRoll:
            def __init__(self, value):
                self.value = value
            def randint(self, low, high):
                return self.value
        m = Melee(85, 218, 1800, 500, 500, 55, double_skill=250)
        self.assertEqual(sum(m.round_attacks(FixedRoll(r))-1 for r in range(1, 501)), 305)
        self.assertEqual(m.round_attacks(FixedRoll(1), offhand=True), 0)
        no_skill = Melee(85, 218, 1800, 500, 500, 55, offhand=True)
        self.assertEqual(no_skill.round_attacks(FixedRoll(1), offhand=True), 0)

    def test_round_attacks_share_one_roll(self):
        self.assertEqual(legacy_round_attacks(55, 0, double=True, quad=True), 4)
        self.assertEqual(legacy_round_attacks(55, 35, double=True, quad=True), 3)
        self.assertEqual(legacy_round_attacks(55, 55, double=True, quad=True), 2)
        self.assertEqual(legacy_round_attacks(55, 75, double=True, quad=True), 1)
        self.assertEqual(legacy_round_attacks(55, 0, count=3, double=True), 4)

    def test_invalid_rolls_or_stats_fail(self):
        with self.assertRaises(ValueError):
            damage_interval(50, 50, 55, 0)
        with self.assertRaises(ValueError):
            npc_damage(218, 85, 1)
        with self.assertRaises(ValueError):
            legacy_round_attacks(55, 100)
