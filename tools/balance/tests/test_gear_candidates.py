import unittest

from gear_candidates import assign_items, equipment, score_item, socket_augments


def item(item_id, **changes):
    row = dict(id=item_id, classes=65535, races=65535, slots=sum(1 << s for s in range(1, 21)),
               deity=0, reqlevel=0, reclevel=0, loregroup=-1, itemclass=0, itemtype=10,
               augtype=0, augrestrict=0, damage=0, delay=0, hp=100, mana=0, ac=0,
               asta=0, aint=0, awis=0, heroic_sta=0, heroic_int=0, heroic_wis=0)
    for socket in range(1, 7):
        row[f'augslot{socket}type'] = 7 if socket == 1 else 0
        row[f'augslot{socket}visible'] = 1
    return row | changes


class ExpandedGearTests(unittest.TestCase):
    def test_recommended_scaling_applies_to_combined_stat_and_heroic(self):
        candidate = item(1, hp=100, reclevel=100, asta=1, heroic_sta=1)
        self.assertEqual(score_item(candidate, 50, 'int', 'balanced'), 61)

    def test_assignment_lore_and_reserved_item_are_global(self):
        selected = assign_items([1, 4], [item(1, hp=200), item(2), item(3, loregroup=0)],
                                lambda s, i: True, lambda s, i: i['hp'], [('id', 1)])
        self.assertNotIn(1, [i['id'] for i in selected.values()])

    def test_high_recommended_weapon_and_two_hand_layout_are_allowed(self):
        pool = [item(1, loregroup=0), item(2, itemtype=1, damage=42, delay=37, reclevel=62)]
        selected = equipment(pool, (1, 2, 12), 50, 'int', 'balanced', 'two_hand')
        self.assertEqual(selected[13]['id'], 2)
        self.assertNotIn(14, selected)
        with self.assertRaises(ValueError):
            equipment(pool, (1, 2, 12), 50, 'int', 'balanced', 'two_hand', {14: 1})

    def test_shield_layout_rejects_fake_weapon_and_augment_as_armor(self):
        pool = [item(1, loregroup=0), item(2, itemtype=0, damage=18, delay=20),
                item(3, itemtype=8), item(4, augtype=64, hp=10000)]
        selected = equipment(pool, (1, 2, 12), 50, 'int', 'balanced', 'shield')
        self.assertEqual(selected[13]['id'], 2)
        self.assertEqual(selected[14]['id'], 3)
        self.assertNotIn(4, [i['id'] for i in selected.values()])

    def test_dual_wield_requires_supported_held_class(self):
        with self.assertRaises(ValueError):
            equipment([], (13, 11, 10), 50, 'int', 'melee', 'dual')

    def test_socket_assignment_respects_global_lore_and_parent_scaling(self):
        gear = {1: item(1, reclevel=100), 4: item(2)}
        augs = [item(3, hp=100, augtype=64), item(4, hp=10, augtype=64)]
        result = socket_augments(gear, augs, (1, 2, 12), 50, 'int', 'balanced')
        self.assertEqual(result, {1: [{'socket': 0, 'id': 4}], 4: [{'socket': 0, 'id': 3}]})

    def test_socket_masks_visibility_required_level_and_base_lore(self):
        gear = {1: item(1), 4: item(2, augslot1visible=0), 13: item(3, augslot1type=4)}
        augs = [item(1, augtype=64), item(5, augtype=64, slots=1 << 4),
                item(6, augtype=64, reqlevel=51), item(7, augtype=64, augrestrict=1),
                item(8, augtype=64, reclevel=51), item(9, augtype=64)]
        result = socket_augments(gear, augs, (1, 2, 12), 50, 'int', 'balanced')
        self.assertEqual(result, {1: [{'socket': 0, 'id': 9}], 4: [], 13: []})

    def test_empty_sockets_are_allowed_when_every_choice_is_harmful(self):
        result = socket_augments({1: item(1)}, [item(2, augtype=64, hp=-100)],
                                 (1, 2, 12), 50, 'int', 'balanced')
        self.assertEqual(result, {1: []})


if __name__ == '__main__':
    unittest.main()
