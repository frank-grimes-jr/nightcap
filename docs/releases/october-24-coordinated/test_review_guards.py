"""Independent checks of the release-specific guards, without live services."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


def operator():
    spec = importlib.util.spec_from_file_location('reviewed_release', Path(__file__).with_name('rollout.py'))
    result = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace()}):
        spec.loader.exec_module(result)
    return result


class ReviewGuards(unittest.TestCase):
    def test_campaign_rejects_each_unexpected_enrollment_and_disabled_flag(self):
        release = operator()
        for drift in ('nightcap_ashen_state', 'nightcap_highkeep_state',
                      'nightcap_ashen_characters', 'nightcap_highkeep_runs'):
            with self.subTest(drift=drift):
                def sql(query):
                    table = query.rsplit('FROM ', 1)[1].rstrip(';')
                    if query.startswith('SELECT revision'):
                        return '2026102401\t' + ('0' if table == drift else '1')
                    return '1' if table == drift else '0'
                release.base = types.SimpleNamespace(sql=sql)
                with self.assertRaises(AssertionError):
                    release.campaign(1)

    def test_new_schema_drift_cannot_pass_exact_rehearsal_comparison(self):
        release = operator()
        release.base = types.SimpleNamespace(load=lambda _: {'table': 'expected DDL'})
        release.storage = lambda: {'table': 'different DDL'}
        with self.assertRaises(AssertionError):
            release.check_new_storage()

    def test_new_open_guards_hold_on_failure_before_delegating(self):
        for failing_guard in ('campaign', 'check_new_storage'):
            with self.subTest(guard=failing_guard):
                release = operator()
                events = []
                release.base = types.SimpleNamespace(hold=lambda: events.append('hold'))
                release.campaign = lambda _: events.append('campaign')
                release.check_new_storage = lambda: events.append('storage')
                release.original_open = lambda: events.append('open')
                def fail(*_):
                    raise RuntimeError('injected guard failure')
                setattr(release, failing_guard, fail)
                with self.assertRaises(RuntimeError):
                    release.open_access()
                self.assertEqual(events.count('hold'), 1)
                self.assertNotIn('open', events)


if __name__ == '__main__':
    unittest.main()
