import unittest

from gear_haste_controls import recommended_bonus, verify_controls


class GearHasteTests(unittest.TestCase):
    def test_recommended_is_scaling_not_required_level(self):
        self.assertEqual(recommended_bonus(324, 50, 62), 261)
        self.assertEqual(recommended_bonus(348, 50, 62), 281)
        self.assertEqual(recommended_bonus(324, 62, 62), 324)
        self.assertEqual(recommended_bonus(324, 50, 0), 324)

    def test_signed_rounding_and_zero(self):
        self.assertEqual(recommended_bonus(-324, 50, 62), -261)
        self.assertEqual(recommended_bonus(1, 1, 2), 1)
        self.assertEqual(recommended_bonus(-1, 1, 2), -1)
        self.assertEqual(recommended_bonus(1, 1, 3), 0)
        self.assertEqual(recommended_bonus(0, 50, 62), 0)

    def controls(self):
        build = {'profile': 'war-clr-wiz', 'tier': 'isolated/both', 'level': 50,
                 'equipment': [{'id': 1}, {'id': 2}], 'aa_rank_ids': [100]}
        tables = {'items': [dict(id=1, hp=324, mana=348, reclevel=62, haste=41, worneffect=-1),
                            dict(id=2, hp=120, mana=0, reclevel=0, haste=36, worneffect=-1)]}
        result = {'profile': 'war-clr-wiz', 'tier': 'isolated/both', 'item_hp': 381,
                  'item_mana': 281, 'haste': 141, 'aa_purchases': [{'rank_id': 100}]}
        return {'builds': [build]}, {'builds': [result]}, tables

    def test_haste_maximum_not_sum_or_recommended_scaled(self):
        inputs, native, tables = self.controls()
        self.assertEqual(verify_controls(inputs, native, tables), [])
        for wrong in [177, 133, 136]:
            native['builds'][0]['haste'] = wrong
            self.assertEqual(verify_controls(inputs, native, tables)[0]['field'], 'haste')

    def test_missing_output_and_changed_purchase_are_rejected(self):
        inputs, native, tables = self.controls()
        with self.assertRaises(ValueError):
            verify_controls(inputs, {'builds': []}, tables)
        native['builds'][0]['aa_purchases'] = []
        self.assertEqual(verify_controls(inputs, native, tables)[0]['field'], 'aa_purchases')

    def test_unknown_worn_effect_cannot_be_silently_omitted(self):
        inputs, native, tables = self.controls()
        tables['items'][0]['worneffect'] = 80
        with self.assertRaises(ValueError):
            verify_controls(inputs, native, tables)
        spell = {'id': 80} | {f'effectid{s}': 254 for s in range(1, 13)}
        spell['effectid1'] = 13
        tables['spells_new'] = [spell]
        self.assertEqual(verify_controls(inputs, native, tables), [])
        spell['effectid1'] = 69
        with self.assertRaises(ValueError):
            verify_controls(inputs, native, tables)


if __name__ == '__main__':
    unittest.main()
