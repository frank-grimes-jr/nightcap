"""Keeper release gates; inherited current release already covers the native lifecycle."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock,patch,call

spec=importlib.util.spec_from_file_location('keeper_rollout',Path(__file__).with_name('rollout.py'))
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)


class KeeperRollout(unittest.TestCase):
    def test_every_compiled_schema_content_check_runs_without_overrides(self):
        checks={f:[dict(label=str(i),sql='SELECT 1',expected='1') for i in range(n)] for f,n in [('schema',51),('content',671)]}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'runtime-contract.json').write_text(json.dumps(checks))
            query=Mock(side_effect=['1\n'*51,'1\n'*671])
            with patch.object(op,'STAGE',root),patch.object(op,'p',SimpleNamespace(sql=query),create=True):
                self.assertEqual(op.contract(),{'schema':51,'content':671})
            query=Mock(side_effect=['1\n'*51,'1\n'*670+'0\n'])
            with patch.object(op,'STAGE',root),patch.object(op,'p',SimpleNamespace(sql=query),create=True):
                with self.assertRaisesRegex(AssertionError,'Compiled contract: content/670'):op.contract()

    def test_latest_baseline_and_unrelated_native_binaries_are_preserved(self):
        base={'zone':'current-stats','world':'world','shared_memory':'cache-loader'}
        with patch.object(op,'base_binaries',base,create=True),patch.object(op,'m',{'zone_sha256':'keeper'},create=True):
            self.assertEqual(op.binaries(),{**base,'zone':'keeper'})
            self.assertEqual(op.binaries(False),base)

    def test_connected_clients_stop_preflight_and_activation_before_mutation(self):
        prior=SimpleNamespace(preflight=Mock(),activate=Mock())
        with patch.object(op,'player_count',return_value=1),patch.object(op,'p',prior,create=True):
            for action in (op.preflight,op.activate):
                with self.assertRaisesRegex(AssertionError,'fully exit'):action()
        prior.preflight.assert_not_called();prior.activate.assert_not_called()

    def test_closed_ingress_drains_native_auth_before_whole_game_stop(self):
        events=[]
        compose=Mock(side_effect=lambda *args:events.append(args))
        runtime=SimpleNamespace(compose=compose,out=Mock(return_value=''))
        prior=SimpleNamespace(r=runtime,time=SimpleNamespace(sleep=Mock()),h=SimpleNamespace(hold=Mock()))
        def activate():
            prior.r.compose('stop','gateway')
            self.assertEqual(prior.time.sleep.call_args_list,[call(25)]*5)
            prior.r.compose('stop','-t','90','game')
        prior.activate=activate
        with patch.object(op,'p',prior,create=True),patch.object(op,'player_count',return_value=0) as count,patch.object(op,'read',return_value={'runtime':{'started_at':'now'}}):
            op.activate()
        self.assertEqual(events,[('stop','gateway'),('stop','-t','90','game')])
        self.assertEqual(count.call_count,3)
        self.assertIs(prior.r.compose,compose)
        prior.h.hold.assert_not_called()

    def test_open_never_releases_admissions_after_preservation_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'activation';folder.mkdir()
            (root/'preflight.json').write_text('{}')
            (folder/'verified-closed.json').write_text(json.dumps({'game':{'identity':'same'}}))
            (folder/'expected-boot-state.json').write_text('{}')
            runtime=SimpleNamespace(state=Mock(return_value={'State':{'Running':False}}),compact=Mock(return_value={'identity':'same'}),compose=Mock())
            prior=SimpleNamespace(r=runtime,base=SimpleNamespace(saved_state=Mock(return_value={})),command_state=Mock(),unchanged=Mock(side_effect=AssertionError('cache drift')),h=SimpleNamespace(hold=Mock()))
            with patch.object(op,'EVIDENCE',root),patch.object(op,'p',prior,create=True):
                with self.assertRaisesRegex(AssertionError,'cache drift'):op.open_access()
            runtime.compose.assert_not_called();prior.h.hold.assert_called_once_with(folder)
            self.assertFalse((folder/'opening.json').exists())

    def test_bad_native_count_response_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'world_count.py').write_text('read-only count')
            runtime=SimpleNamespace(state=lambda _: {'Id':'game'},out=Mock(return_value='true'))
            with patch.object(op,'STAGE',root),patch.object(op,'p',SimpleNamespace(r=runtime),create=True):
                with self.assertRaisesRegex(AssertionError,'Unexpected native client-count'):op.player_count()


if __name__=='__main__':unittest.main()
