"""Exercise the actual native-only activation with injected failures; no server I/O."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock,patch

if sys.platform=='win32':sys.modules['fcntl']=SimpleNamespace()
spec=importlib.util.spec_from_file_location('journal_rollout',Path(__file__).with_name('rollout.py'))
j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)


class Activation(unittest.TestCase):
    def setUp(self):
        self.events=[]
        self.p={'manifest_sha256':'hash','services':{'game':'game','gateway':'gateway'},
                'new_image_id':'new','cache_sha256':'hash'}
        j.r=SimpleNamespace(ROOT=Path('/not-a-server'),EVIDENCE=Path('/no-evidence'),
            compact=MagicMock(side_effect=lambda name:name),image_hashes=MagicMock(return_value={}),
            compose=MagicMock(side_effect=lambda *args:self.events.append(args)),
            player_data=MagicMock(return_value={'inventory':'unchanged'}),
            database_backup=MagicMock(side_effect=lambda:self.events.append('backup') or {'verified':True}),
            running=MagicMock(return_value={'started_at':'now'}),state=MagicMock(return_value={'State':{'Running':False}}))
        j.q=SimpleNamespace(stopped=MagicMock(),select=MagicMock(side_effect=lambda x:self.events.append('select')),
                            verify_publication=MagicMock())
        j.d=SimpleNamespace(load=MagicMock(return_value=self.p),unchanged=MagicMock(),expected_image=MagicMock(return_value={}),
            save=MagicMock(side_effect=lambda n,v:self.events.append(n)),custom=MagicMock(return_value={'run':'unchanged'}),
            challenge_health=MagicMock(),binaries=MagicMock(return_value={}),
            sql=MagicMock(return_value='2026101601\t1'),preserved=MagicMock(),hold=MagicMock())
        self.patches=[patch.object(j,'manifest',return_value={}),patch.object(j,'sha',return_value='hash'),
            patch.object(Path,'exists',return_value=False),patch.object(j.time,'sleep')]
        for p in self.patches:p.start()

    def tearDown(self):
        for p in reversed(self.patches):p.stop()

    def test_success_preserves_before_open_and_never_mutates_sql(self):
        j.activate()
        self.assertLess(self.events.index('backup'),self.events.index('select'))
        self.assertIn('activated-closed.json',self.events)
        self.assertNotIn(('up','-d','--wait','--wait-timeout','60','gateway'),self.events)
        self.assertTrue(all(c.args[0].startswith('SELECT') for c in j.d.sql.call_args_list))
        j.d.preserved.assert_called_once();j.d.hold.assert_not_called()

    def test_failed_backup_never_selects_candidate(self):
        j.r.database_backup.side_effect=RuntimeError('backup')
        with self.assertRaises(RuntimeError):j.activate()
        j.q.select.assert_not_called();j.d.hold.assert_called_once()

    def test_failed_start_holds_without_restoring_data(self):
        def compose(*args):
            self.events.append(args)
            if args[0]=='up':raise RuntimeError('start')
        j.r.compose.side_effect=compose
        with self.assertRaises(RuntimeError):j.activate()
        j.q.select.assert_called_once_with('new');j.d.hold.assert_called_once()

    def test_cache_mismatch_holds(self):
        with patch.object(j,'sha',side_effect=lambda p:'bad' if p.name=='items' else 'hash'):
            with self.assertRaises(AssertionError):j.activate()
        j.d.hold.assert_called_once();self.assertNotIn('activated-closed.json',self.events)

    def test_player_drift_holds(self):
        j.d.preserved.side_effect=AssertionError('player drift')
        with self.assertRaises(AssertionError):j.activate()
        j.d.hold.assert_called_once();self.assertNotIn('activated-closed.json',self.events)

    def test_activation_replay_refuses_before_stop(self):
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaises(AssertionError):j.activate()
        j.r.compose.assert_not_called()

    def test_fingerprint_includes_completed_history_and_native_instances(self):
        j.q.extras=MagicMock(return_value={'nightcap_dungeon_runs':'42'})
        j.d.sql.return_value='peq.table\t123'
        result=j.custom()
        self.assertEqual(set(result),{'nightcap_dungeon_runs','completed_tasks','instance_list','instance_list_player','respawn_times'})


if __name__=='__main__':unittest.main()
