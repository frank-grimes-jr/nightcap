import unittest

from verify_native_movement import verify


class NativeMovementTests(unittest.TestCase):
    def report(self):
        event = dict(ms=50, controlled=False, casting=False, in_range=False,
                     speed=28, limit=0.812, accepted=True,
                     **{'from': [0, 0, 0], 'to': [0.812, 0, 0], 'actual': [0.812, 0, 0]})
        return {'encounter': {'elapsed_ms': 500, 'result': 'npc_death',
                'trace': [{'ms': 500, 'player_combat': {'range': True}}],
                'movement': {'events': [event], 'history_packets': 1, 'failed_paths': 0}}}

    def test_applied_bounded_movement_restores_range(self):
        self.assertTrue(verify(self.report(), require_movement=True)['passed'])

    def test_speed_control_casting_and_application_regressions_fail(self):
        changes = [{'controlled': True}, {'casting': True}, {'speed': 0},
                   {'to': [100, 0, 0], 'actual': [100, 0, 0]},
                   {'accepted': False}, {'actual': [0, 0, 0]},
                   {'to': [float('nan'), 0, 0]}, {'limit': 100}, {'ms': 600}]
        for change in changes:
            report = self.report()
            report['encounter']['movement']['events'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify(report, require_movement=True)

    def test_empty_or_unproductive_pursuit_cannot_pass_required_control(self):
        for empty in (True, False):
            report = self.report()
            if empty:
                report['encounter']['movement']['events'] = []
            else:
                report['encounter']['trace'][0]['player_combat']['range'] = False
            with self.assertRaises(ValueError):
                verify(report, require_movement=True)


if __name__ == '__main__':
    unittest.main()
