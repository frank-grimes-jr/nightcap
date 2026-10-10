import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# Windows owner tests do not have fcntl; helper main is never executed locally.
sys.modules.setdefault('fcntl', types.SimpleNamespace(LOCK_EX=2, flock=lambda *args: None))
spec = importlib.util.spec_from_file_location('gm_helper', pathlib.Path(__file__).parents[1] / 'api/lib/production_helper.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

class HelperTests(unittest.TestCase):
    def test_rejects_unknown_operations_and_fields(self):
        for request in ({'operation': 'shell'}, {'operation': 'status', 'command': 'oops'}, {'operation': 'lease', 'offline': True}):
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                helper.execute(request)

    def test_status_keeps_resume_available_after_partial_start(self):
        state = {'game': {'State': {'Running': True}}, 'gateway': {'State': {'Running': False}, 'Config': {'Env': []}}}
        with tempfile.TemporaryDirectory() as tmp:
            marker = pathlib.Path(tmp) / 'maintenance.json'; marker.write_text('{}')
            with patch.object(helper, 'MAINTENANCE', marker), patch.object(helper, 'containers', return_value=state):
                status = helper.status()
                self.assertTrue(status['maintenance_active'])
                self.assertFalse(status['maintenance'])
                with self.assertRaisesRegex(ValueError, 'Start maintenance'): helper.require_offline()

    def test_resume_refuses_inflight_database_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = pathlib.Path(tmp) / 'maintenance.json'; marker.write_text('{}')
            with patch.object(helper, 'MAINTENANCE', marker), patch.object(helper, 'status', return_value={}), patch.object(helper.subprocess, 'check_output', return_value='0\n'), patch.object(helper.subprocess, 'run') as runtime:
                with self.assertRaisesRegex(ValueError, 'database action'): helper.maintenance(False)
                runtime.assert_not_called()
                self.assertTrue(marker.exists())

    def test_failed_game_health_retains_marker_and_gateway_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = pathlib.Path(tmp) / 'maintenance.json'; marker.write_text('{}')
            with patch.object(helper, 'MAINTENANCE', marker), patch.object(helper, 'status', return_value={}), patch.object(helper.subprocess, 'check_output', return_value='1\n'), patch.object(helper.subprocess, 'run') as runtime, patch.object(helper, 'containers', return_value={'game': {'State': {'Health': {'Status': 'unhealthy'}}}}), patch('time.sleep'):
                with self.assertRaisesRegex(ValueError, 'did not become healthy'): helper.maintenance(False)
                self.assertEqual(runtime.call_count, 1)
                self.assertIn('nightcap-production-game-1', runtime.call_args.args[0])
                self.assertTrue(marker.exists())

    def test_backup_rejects_untrusted_scope_before_docker(self):
        for tables in (['mysql.user'], ['--all-databases'], [], 'character_data'):
            with self.assertRaisesRegex(ValueError, 'backup scope'): helper.backup(tables)

    def test_access_list_before_deployment_is_honest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(helper, 'REGISTRY', pathlib.Path(tmp) / 'absent.json'), patch.object(helper, 'access_module') as module:
                self.assertEqual(helper.execute({'operation': 'access_list'}), {'ready': False, 'credentials': []})
                module.assert_not_called()

if __name__ == '__main__': unittest.main()
