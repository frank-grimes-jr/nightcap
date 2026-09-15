import copy
import unittest

from augment_controls import verify_equipment


class NativeEquipmentVerificationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {'builds': [{'profile': 'test', 'tier': 'test', 'equipment': [
            {'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 651903}]}]}]}
        self.report = {'builds': [{'profile': 'test', 'tier': 'test', 'equipped_items': [
            {'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 651903}],
             'required_level': 20, 'recommended_level': 0}]}]}

    def test_inventory_verification_does_not_require_display_metadata(self):
        verify_equipment(self.inputs, self.report)

    def test_missing_replaced_or_repositioned_augment_is_rejected(self):
        for augments in ([], [{'socket': 0, 'id': 679626}], [{'socket': 1, 'id': 651903}]):
            changed = copy.deepcopy(self.report)
            changed['builds'][0]['equipped_items'][0]['augments'] = augments
            with self.subTest(augments=augments), self.assertRaises(ValueError):
                verify_equipment(self.inputs, changed)

    def test_duplicate_or_missing_build_is_rejected(self):
        for builds in ([], self.report['builds']*2):
            with self.subTest(builds=builds), self.assertRaises(ValueError):
                verify_equipment(self.inputs, {'builds': builds})


if __name__ == '__main__':
    unittest.main()
