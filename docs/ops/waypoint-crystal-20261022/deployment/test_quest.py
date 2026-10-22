import contextlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

if sys.platform=='win32': sys.modules['fcntl']=types.ModuleType('fcntl')
spec=importlib.util.spec_from_file_location('quest_operator',Path(__file__).with_name('quest_remote.py'))
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
REAL_INSTALL=op.install

class QuestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        op.ROOT=Path(self.temp.name);op.OUT=op.ROOT/'backup';op.QUEST=op.ROOT/'999240.pl'
        self.original=b'old $signal == 20261011 race => 127 gender => 0'
        self.candidate=b'new crystal';op.QUEST.write_bytes(self.original)
        op.OLD_SHA=op.sha(self.original);op.NEW_SHA=op.sha(self.candidate)
        self.state={'count':0,'locked':False,'paused':False};self.events=[]
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        def mock(name,**kwargs):return self.stack.enter_context(patch.object(op,name,**kwargs))
        self.snap=mock('snapshot',return_value={'native':'same','services':'same','channel':'paired','keeper':'same'})
        def control(action):
            if action=='count':return self.state['count']
            if action=='status':return self.state['locked']
            self.state['locked']=action=='lock';self.events.append(action)
        mock('control',side_effect=control)
        mock('gateway_paused',side_effect=lambda:self.state['paused'])
        mock('pause',side_effect=lambda:self.state.update(paused=True))
        mock('unpause',side_effect=lambda:self.state.update(paused=False))
        self.install=mock('install',side_effect=op.QUEST.write_bytes)
        self.reload=mock('reload',side_effect=lambda:self.events.append('reload'))
        self.verify=mock('verify_reload',side_effect=lambda *a:self.events.append('verified') or 12)
        self.signal=mock('signal',side_effect=lambda value:self.events.append(value))
        mock('game',side_effect=lambda *a:op.sha(op.QUEST.read_bytes()))
        self.stack.enter_context(patch.object(op.time,'sleep'))
    def apply(self):return op.execute('apply',self.candidate,'main')
    def test_apply_reopens_and_keeps_exact_backup(self):
        result=self.apply()
        self.assertEqual((op.OUT/'original.pl').read_bytes(),self.original)
        self.assertEqual(op.QUEST.read_bytes(),self.candidate)
        self.assertFalse(self.state['locked'] or self.state['paused'])
        self.assertFalse(result['rendered_acceptance'])
        self.assertLess(self.events.index('verified'),self.events.index(20261022))
    def test_connected_clients_refuse_without_writes(self):
        self.state['count']=1
        with self.assertRaisesRegex(AssertionError,'Clients'):self.apply()
        self.assertFalse(op.OUT.exists());self.install.assert_not_called()
    def test_preimage_drift_refuses(self):
        op.QUEST.write_bytes(b'other')
        with self.assertRaisesRegex(AssertionError,'preimage'):self.apply()
        self.assertFalse(op.OUT.exists())
    def test_existing_world_lock_is_preserved(self):
        self.state['locked']=True;self.apply()
        self.assertTrue(self.state['locked']);self.assertFalse(self.state['paused'])
    def test_existing_gateway_hold_is_not_owned(self):
        self.state['paused']=True
        with self.assertRaisesRegex(AssertionError,'already held'):self.apply()
        self.assertTrue(self.state['paused']);self.assertFalse(op.OUT.exists())
    def test_arrival_during_hold_refuses_and_reopens_before_write(self):
        with patch.object(op.time,'sleep',side_effect=lambda *a:self.state.update(count=1)):
            with self.assertRaisesRegex(AssertionError,'entered'):self.apply()
        self.assertEqual(op.QUEST.read_bytes(),self.original)
        self.assertFalse(self.state['paused'] or self.state['locked'])
    def test_reload_failure_keeps_hold_and_recovery_restores_old_illusion(self):
        self.verify.side_effect=AssertionError('unacknowledged')
        with self.assertRaises(AssertionError):self.apply()
        self.assertTrue(self.state['paused'] and self.state['locked']);self.signal.assert_not_called()
        self.verify.side_effect=None;self.verify.return_value=12
        result=op.execute('rollback',self.candidate,'main')
        self.assertEqual(op.QUEST.read_bytes(),self.original)
        self.assertIn(20261011,self.events)
        self.assertFalse(self.state['paused'] or self.state['locked'])
        self.assertEqual(result['quest_sha256'],op.OLD_SHA)
    def test_service_drift_retains_hold(self):
        self.snap.side_effect=[{'same':True},{'same':False}]
        with self.assertRaisesRegex(AssertionError,'drift'):self.apply()
        self.assertTrue(self.state['paused'] and self.state['locked'])
        self.assertFalse((op.OUT/'apply-result.json').exists())
    def test_replay_refuses_and_unrelated_quest_cannot_rollback(self):
        self.apply()
        with self.assertRaises(AssertionError):self.apply()
        op.QUEST.write_bytes(b'unrelated')
        with self.assertRaisesRegex(AssertionError,'Unrelated'):op.execute('rollback',self.candidate,'main')
        self.assertEqual(op.QUEST.read_bytes(),b'unrelated')
    def test_failed_final_check_reestablishes_hold(self):
        self.snap.side_effect=[{'same':True},{'same':True},{'same':False}]
        with self.assertRaises(AssertionError):self.apply()
        self.assertTrue(self.state['paused'] and self.state['locked'])
    def real_installer(self):
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(op,'install',side_effect=REAL_INSTALL))
        if sys.platform=='win32':
            stack.enter_context(patch.object(op.os,'fchmod',create=True))
            stack.enter_context(patch.object(op.os,'fchown',create=True))
            stack.enter_context(patch.object(op,'sync_dir'))
        return stack
    def test_interrupted_actual_install_recovers_owned_partial(self):
        with self.real_installer():
            with patch.object(op.os,'replace',side_effect=OSError('injected rename failure')):
                with self.assertRaises(OSError):self.apply()
            partial=op.QUEST.with_suffix('.pl.waypoint-partial')
            self.assertEqual(partial.read_bytes(),self.candidate)
            self.assertTrue(self.state['paused'] and self.state['locked'])
            op.execute('rollback',self.candidate,'main')
            self.assertEqual(op.QUEST.read_bytes(),self.original)
            self.assertFalse(partial.exists() or self.state['paused'] or self.state['locked'])
    def test_interrupted_actual_rollback_is_retryable(self):
        self.apply()
        with self.real_installer():
            with patch.object(op.os,'replace',side_effect=OSError('interrupted rollback')):
                with self.assertRaises(OSError):op.execute('rollback',self.candidate,'main')
            self.assertTrue((op.OUT/'rollback-started.json').exists())
            op.execute('rollback',self.candidate,'main')
        self.assertEqual(op.QUEST.read_bytes(),self.original)
        self.assertFalse(self.state['paused'] or self.state['locked'])
    def test_foreign_partial_is_never_removed(self):
        partial=op.QUEST.with_suffix('.pl.waypoint-partial');partial.write_bytes(b'foreign')
        with self.real_installer():
            with self.assertRaisesRegex(AssertionError,'Foreign partial'):self.apply()
        self.assertEqual(partial.read_bytes(),b'foreign')
        self.assertEqual(op.QUEST.read_bytes(),self.original)

if __name__=='__main__':unittest.main()
