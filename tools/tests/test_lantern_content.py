"""Campaign catalog contracts: earned appearance, fixed budgets and task authority."""
import unittest
from last_lantern_content import compile_items, compile_tasks, compile_npcs, SCENES


class LanternContentTests(unittest.TestCase):
    def test_four_complete_fits_and_earned_refit_grades(self):
        items = compile_items()
        self.assertEqual({i['id'] for i in items}, set(range(964000, 964128)))
        self.assertTrue(all(i['nopet'] == 1 and i['nodrop'] == 0 and i['notransfer'] == 1 for i in items))
        self.assertTrue(all(i['price'] == 0 and i['sellrate'] == 0 and not i['stackable'] for i in items))
        for fit in range(4):
            for grade in range(4):
                outfit = items[fit * 32 + grade * 8:fit * 32 + grade * 8 + 8]
                self.assertEqual(len({i['slots'] for i in outfit}), 8)
                self.assertTrue(all(i['classes'] == outfit[0]['classes'] for i in outfit))
                self.assertEqual(sum(bool(i['augslot1type']) for i in outfit), 6)
                self.assertTrue(all(i['clickeffect'] == -1 and i['focuseffect'] == -1 for i in outfit))
                self.assertTrue(all(not i['heroic_sta'] and not i['regen'] and not i['haste'] for i in outfit))
            for slot in range(8):
                grades = [items[fit * 32 + grade * 8 + slot] for grade in range(4)]
                self.assertEqual(grades[-1]['reqlevel'], 50)
                self.assertTrue(all(a['hp'] <= b['hp'] and a['mana'] <= b['mana'] and a['ac'] <= b['ac']
                                    for a, b in zip(grades, grades[1:])))
        self.assertEqual(items[7]['material'], 11)  # existing Classic robe material

    def test_native_tasks_are_the_only_completion_ledger(self):
        tasks, activities = compile_tasks()
        self.assertEqual({t['id'] for t in tasks}, set(range(9500, 9516)))
        self.assertTrue(all(not t['repeatable'] and not t['reward_id_list'] and not t['cash_reward'] for t in tasks))
        self.assertEqual(len({(a['taskid'], a['activityid']) for a in activities}), len(activities))
        for task in tasks:
            rows = [a for a in activities if a['taskid'] == task['id']]
            self.assertTrue(rows)
            self.assertEqual([a['activityid'] for a in rows], list(range(len(rows))))
            self.assertTrue(any(a['step'] > 0 for a in rows), 'all-zero steps select native sequential mode')
            self.assertTrue(all(a['zone_version'] in (0, 80) for a in rows))
        final = [a for a in activities if a['taskid'] == 9515]
        self.assertEqual(final[-1]['zones'], '22')
        self.assertGreater(final[-1]['step'], final[0]['step'])

    def test_story_scenes_have_separate_population_and_no_farm_rewards(self):
        npcs = compile_npcs()
        self.assertEqual(len({n['id'] for n in npcs}), len(npcs))
        self.assertTrue(all(n['loottable_id'] == 0 and n['skip_global_loot'] == 1 for n in npcs))
        self.assertTrue(all(n['exp_mod'] == 0 and n['merchant_id'] == 0 for n in npcs))
        self.assertEqual(len(SCENES), 8)
        self.assertEqual(SCENES[-1]['task'], 9515)
        self.assertEqual(SCENES[-1]['level'], 50)
        self.assertTrue(all(s['version'] == 80 and s['zone'] in (63, 66, 32, 48, 39, 72, 76) for s in SCENES))


if __name__ == '__main__':
    unittest.main()
