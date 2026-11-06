"""New report-specific boundaries, alongside retained native release guards."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

spec=importlib.util.spec_from_file_location('report_rollout',Path(__file__).with_name('rollout.py'))
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)


class ReportRollout(unittest.TestCase):
    def test_command_is_exactly_player_access_without_aliases(self):
        with patch.object(op,'sql',Mock(return_value=''),create=True): op.command_state(False)
        with patch.object(op,'sql',Mock(return_value='0\t\n'),create=True): op.command_state(True)
        for value in ('1\t\n','0\tother\n','0\t\n0\t\n',''):
            with patch.object(op,'sql',Mock(return_value=value),create=True):
                with self.assertRaises(AssertionError):op.command_state(True)

    def test_native_only_delta_retains_all_other_binaries(self):
        old={'zone':'old','world':'world','shared_memory':'shared'}
        with patch.object(op,'pl',SimpleNamespace(binaries=lambda:old),create=True),patch.object(op,'m',{'zone_sha256':'new'},create=True):
            self.assertEqual(op.binaries(),{**old,'zone':'new'})
            self.assertEqual(op.binaries(False),old)

    def test_only_new_command_row_is_outside_preservation_scope(self):
        scope=Mock(return_value={'rows':400,'sha256':'same'})
        prior=SimpleNamespace(content=lambda:{'items':'keep','command_settings':'old'},scope_hash=scope)
        with patch.object(op,'pl',prior,create=True):
            self.assertEqual(op.content(),{'items':'keep','command_settings/outside-augstats':{'rows':400,'sha256':'same'}})
        scope.assert_called_once_with('command_settings',"command<>'augstats'")

    def test_existing_full_contract_still_runs_with_bound_aug_overrides(self):
        contract=Mock(return_value={'checks':671})
        with patch.object(op,'pl',SimpleNamespace(contract=contract),create=True),patch.object(op,'overrides',{'owned':'exact'},create=True):
            self.assertEqual(op.contract(),{'checks':671})
        contract.assert_called_once_with({'owned':'exact'})


if __name__=='__main__':unittest.main()
