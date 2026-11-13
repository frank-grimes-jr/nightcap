"""Fault tests for the actual one-shot release operator; no service mutations."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
ROOT=Path(__file__).resolve().parents[2]

class Rollout(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        path=ROOT/'docs/releases/quick-buff-20261112/rollout.py'
        spec=importlib.util.spec_from_file_location('quick_buff_rollout',path)
        self.mod=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':types.SimpleNamespace()}):spec.loader.exec_module(self.mod)
        a=self.mod;self.stage=Path(self.tmp.name);a.STAGE=self.stage;a.EVIDENCE=self.stage/'evidence';a.EVIDENCE.mkdir()
        a.save=lambda p,v:p.write_text(json.dumps(v))
        self.services={n:{'running':True} for n in ('game','gateway','db','web','tunnel')}
        self.before={'manifest_sha256':'pin','services':self.services,'image':'candidate'}
        (a.EVIDENCE/'preflight.json').write_text(json.dumps(self.before))
        a.sha=lambda p:'pin';a.unchanged=Mock();a.contract=Mock(return_value={'checks':'PASS'})
        a.r=Mock();a.r.compact.side_effect=lambda n:self.services[n]
        a.r.state.return_value={'State':{'Running':False,'OOMKilled':False,'ExitCode':0}}
        a.r.database_backup.return_value={'backup':'fresh-stopped'};a.r.out.return_value=''
        a.r.running.return_value={'started_at':'now'}
        a.a=Mock();a.a.prior.players.return_value=0;a.a.prior.saved.return_value={'inventory':'unchanged'}
        a.startup=Mock();a.h=Mock();a.base=Mock();a.base.boot_state.return_value={'inventory':'unchanged'}
        a.market=Mock();a.market.market.return_value={'rotation':'before'}
        a.market.verify_market.return_value={'rotations':1};a.m={'base_hashes':{'bin/zone':'old'},'binaries':{'zone':'new'},'source_revision':'source'}
        self.sleep=patch.object(a.time,'sleep');self.sleep.start();self.addCleanup(self.sleep.stop)
        a.publish_client=Mock(return_value={'release':2026111201,'channel_sha256':'signed'})

    def test_reject_online_before_any_mutation(self):
        a=self.mod;a.a.prior.players.return_value=1
        with self.assertRaises(AssertionError):a.activate()
        a.r.compose.assert_not_called();a.r.database_backup.assert_not_called()

    def test_player_during_drain_holds_without_stopping_game(self):
        a=self.mod;a.a.prior.players.side_effect=[0,1]
        with self.assertRaises(AssertionError):a.activate()
        self.assertEqual(a.r.compose.call_args_list,[unittest.mock.call('stop','gateway')])
        a.h.hold.assert_called_once();a.r.select.assert_not_called()

    def test_backup_failure_cannot_select_or_start_candidate(self):
        a=self.mod;a.r.database_backup.side_effect=RuntimeError('backup failed')
        with self.assertRaises(RuntimeError):a.activate()
        a.h.hold.assert_called_once();a.r.select.assert_not_called()
        self.assertEqual(a.r.compose.call_args_list[-1],unittest.mock.call('stop','-t','90','game'))

    def test_native_failure_holds_access_closed(self):
        a=self.mod;a.r.running.side_effect=RuntimeError('wrong native hash')
        with self.assertRaises(RuntimeError):a.activate()
        a.h.hold.assert_called_once()
        self.assertFalse((a.EVIDENCE/'activation/verified-closed.json').exists())
        self.assertFalse(any(c.args and c.args[-1]=='gateway' and c.args[0]=='up' for c in a.r.compose.call_args_list))

    def test_unexpected_saved_state_holds(self):
        a=self.mod;a.base.boot_state.return_value={'inventory':'different'}
        with self.assertRaises(AssertionError):a.activate()
        a.h.hold.assert_called_once();self.assertFalse((a.EVIDENCE/'activation/verified-closed.json').exists())

    def test_success_verifies_closed_and_never_opens_implicitly(self):
        a=self.mod;a.activate()
        self.assertTrue((a.EVIDENCE/'activation/verified-closed.json').is_file())
        a.r.database_backup.assert_called_once();a.h.hold.assert_not_called()
        self.assertFalse(any(c.args and c.args[-1]=='gateway' and c.args[0]=='up' for c in a.r.compose.call_args_list))
        with self.assertRaises(AssertionError):a.activate()

    def test_open_failure_holds_and_never_starts_gateway(self):
        a=self.mod;folder=a.EVIDENCE/'activation';folder.mkdir()
        (folder/'verified-closed.json').write_text(json.dumps({'game':self.services['game'],'runtime':{'started_at':'now'}}))
        (folder/'expected-boot-state.json').write_text(json.dumps({'inventory':'different'}))
        with self.assertRaises(AssertionError):a.open_access()
        a.r.compose.assert_not_called();a.h.hold.assert_called_once()

    def test_client_failure_keeps_admissions_closed(self):
        a=self.mod;folder=a.EVIDENCE/'activation';folder.mkdir()
        (folder/'verified-closed.json').write_text(json.dumps({'game':self.services['game'],'runtime':{'started_at':'now'}}))
        (folder/'expected-boot-state.json').write_text(json.dumps({'inventory':'unchanged'}))
        a.publish_client.side_effect=RuntimeError('client publication failed')
        with self.assertRaises(RuntimeError):a.open_access()
        a.r.compose.assert_not_called();a.h.hold.assert_called_once()
        self.assertFalse((folder/'opening.json').exists())

if __name__=='__main__':unittest.main()
