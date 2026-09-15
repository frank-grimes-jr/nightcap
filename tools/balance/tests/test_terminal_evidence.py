import copy
import unittest

from pet_support_controls import verify_terminal


class NativeTerminalTests(unittest.TestCase):
    def fixture(self):
        return {'input': {'capture_terminal': True}, 'player_id': 1, 'boss_id': 5,
                'result': 'player_death',
                'trace': [{'player': {'hp': 732}, 'boss_hp': 24353}],
                'terminal_events': [{'entity_id': 1, 'ms': 164650, 'hp': -17, 'max_hp': 5093}]}

    def test_callback_proves_death_despite_later_same_pulse_healing(self):
        c = self.fixture()
        self.assertEqual(verify_terminal(c,164650), c['terminal_events'])
        c['input'].clear()
        with self.assertRaisesRegex(ValueError, 'terminal HP'):
            verify_terminal(c,164650)

    def test_positive_hp_wrong_actor_or_wrong_time_cannot_prove_death(self):
        for key, value in (('hp', 1), ('entity_id', 99), ('ms', 164600), ('max_hp', 0),
                           ('hp', True), ('entity_id', True), ('ms', 164650.0), ('hp', float('nan'))):
            c = self.fixture()
            c['terminal_events'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'callback evidence'):
                verify_terminal(c,164650)

    def test_first_callback_decides_same_pulse_double_death(self):
        c = self.fixture()
        c['terminal_events'].append({'entity_id': 5, 'ms': 164650, 'hp': -2, 'max_hp': 32000})
        verify_terminal(c,164650)
        c['result'] = 'boss_death'
        with self.assertRaisesRegex(ValueError, 'first native'):
            verify_terminal(c,164650)
        c['terminal_events'].reverse()
        verify_terminal(c,164650)

    def test_missing_or_duplicated_death_and_false_timeout_are_rejected(self):
        c = self.fixture()
        c['terminal_events'].append(copy.deepcopy(c['terminal_events'][0]))
        with self.assertRaises(ValueError):
            verify_terminal(c,164650)
        c = self.fixture()
        c['result'] = 'timeout'
        with self.assertRaises(ValueError):
            verify_terminal(c,164650)
        c['terminal_events'] = []
        self.assertEqual(verify_terminal(c,164650), [])
        c['result'] = 'player_death'
        with self.assertRaises(ValueError):
            verify_terminal(c,164650)


if __name__ == '__main__':
    unittest.main()
