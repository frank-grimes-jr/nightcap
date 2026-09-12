import itertools
import random
import unittest

from gear import assign_maximum, legal_item, optimize_gear


class GearTests(unittest.TestCase):
    def test_assignment_beats_greedy_slot_selection(self):
        self.assertEqual(assign_maximum([[10, 9], [10, 0]]), [1, 0])

    def test_assignment_matches_exhaustive_small_cases(self):
        rng = random.Random(7)
        for _ in range(50):
            matrix = [[rng.randint(-20, 40) for _ in range(4)] for _ in range(3)]
            result = assign_maximum(matrix)
            expected = max(sum(matrix[i][j] for i, j in enumerate(p))
                           for p in itertools.permutations(range(4), 3))
            self.assertEqual(sum(matrix[i][j] for i, j in enumerate(result)), expected)

    def test_assignment_rejects_impossible_or_ragged_matrix(self):
        for matrix in ([[1], [2]], [[1, 2], [3]]):
            with self.assertRaises(ValueError):
                assign_maximum(matrix)

    def item(self, item_id, score, lore=-1):
        return dict(id=item_id, slots=(1 << 1) | (1 << 4), classes=3, races=1,
                    deity=0, reqlevel=0, reclevel=0, itemtype=10, loregroup=lore, hp=score)

    def test_lore_item_cannot_fill_both_ears(self):
        items = [self.item(1, 100), self.item(2, 99)]
        result = optimize_gear(items, (1, 4), lambda i: i['hp'], (1,), 50)
        self.assertEqual({i['id'] for i in result.values()}, {1, 2})

    def test_nonlore_item_can_fill_both_ears(self):
        result = optimize_gear([self.item(1, 100, 0)], (1, 4), lambda i: i['hp'], (1,), 50)
        self.assertEqual([i['id'] for i in result.values()], [1, 1])

    def test_positive_lore_group_conflicts_across_different_items(self):
        items = [self.item(1, 100, 77), self.item(2, 99, 77), self.item(3, 1, 0)]
        result = optimize_gear(items, (1, 4), lambda i: i['hp'], (1,), 50)
        self.assertEqual(sum(i['hp'] for i in result.values()), 101)

    def test_missing_legal_slot_fails(self):
        with self.assertRaises(ValueError):
            optimize_gear([self.item(1, 100)], (1, 4), lambda i: i['hp'], (1,), 50)

    def test_duplicate_slots_and_too_many_classes_are_rejected(self):
        with self.assertRaises(ValueError):
            optimize_gear([self.item(1, 100)], (1, 1), lambda i: i['hp'], (1,), 50)
        with self.assertRaises(ValueError):
            legal_item(self.item(1, 100), 1, (1, 2, 3, 4), 50)

    def test_class_union_race_level_deity_and_slot_are_enforced(self):
        item = self.item(1, 100)
        item['classes'] = 2
        self.assertTrue(legal_item(item, 1, (1, 2), 50))
        for changes in ({'classes': 4}, {'races': 2}, {'reqlevel': 51}, {'deity': 2}, {'slots': 0}):
            with self.subTest(changes=changes):
                self.assertFalse(legal_item(item | changes, 1, (1, 2), 50))
