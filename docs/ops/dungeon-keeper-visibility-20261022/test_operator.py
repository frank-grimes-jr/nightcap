import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

if sys.platform=='win32':sys.modules['fcntl']=types.ModuleType('fcntl')
spec=importlib.util.spec_from_file_location('operator_under_test',Path(__file__).with_name('remote.py'))
op=importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)

class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        op.OUT=Path(self.tmp.name)/'backup'
        op.QUEST=Path(self.tmp.name)/'keeper.pl'
        op.QUEST.write_bytes(b'old')
        op.OLD_SHA=op.sha(b'old')
        self.state={'waypoint_sha256':op.WAYPOINT_SHA,'native':['unchanged'],'services':['unchanged']}
        self.stack=contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.snap=self.stack.enter_context(patch.object(op,'snapshot',return_value=self.state))
        self.reload=self.stack.enter_context(patch.object(op,'reload'))
        self.signal=self.stack.enter_context(patch.object(op,'signal'))
        self.verify=self.stack.enter_context(patch.object(op,'verify_reload',return_value=12))
        self.stack.enter_context(patch.object(op,'install',side_effect=op.QUEST.write_bytes))
        self.stack.enter_context(patch.object(op,'game',side_effect=lambda *a:op.sha(op.QUEST.read_bytes())))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
    def apply(self):return op.execute('apply',b'new',b'recovery','reviewed')
    def test_apply_and_position_recovery(self):
        self.apply()
        self.assertEqual((op.OUT/'original.pl').read_bytes(),b'old')
        self.assertFalse((op.OUT/'apply-result.json').read_text().find('"rendered_acceptance": false')<0)
        op.execute('rollback',b'new',b'recovery','reviewed')
        self.assertEqual(op.QUEST.read_bytes(),b'recovery')
    def test_drift_refuses_before_mutation(self):
        op.QUEST.write_bytes(b'changed')
        with self.assertRaises(AssertionError):self.apply()
        self.assertFalse(op.OUT.exists())
        self.reload.assert_not_called()
    def test_signal_follows_verified_reload(self):
        events=[]
        self.reload.side_effect=lambda:events.append('reload')
        self.verify.side_effect=lambda *args:events.append('acknowledged') or 12
        self.signal.side_effect=lambda:events.append('signal')
        self.apply()
        self.assertEqual(events,['reload','acknowledged','signal','acknowledged'])
    def test_no_signal_when_reload_unacknowledged(self):
        self.verify.side_effect=AssertionError('incomplete reload')
        with self.assertRaises(AssertionError):self.apply()
        self.signal.assert_not_called()
        self.assertFalse((op.OUT/'apply-result.json').exists())
    def test_existing_attempt_refuses(self):
        op.OUT.mkdir()
        with self.assertRaises(FileExistsError):self.apply()
        self.assertEqual(op.QUEST.read_bytes(),b'old')
    def test_process_change_never_reports_success(self):
        self.snap.side_effect=[self.state,{**self.state,'native':['changed']}]
        with self.assertRaises(AssertionError):self.apply()
        self.assertFalse((op.OUT/'apply-result.json').exists())
    def test_reload_uncertainty_retains_recovery_and_blocks_replay(self):
        self.reload.side_effect=RuntimeError('uncertain')
        with self.assertRaises(RuntimeError):self.apply()
        self.assertEqual((op.OUT/'recovery.pl').read_bytes(),b'recovery')
        self.assertFalse((op.OUT/'apply-result.json').exists())
        with self.assertRaises(AssertionError):self.apply()
    def test_rollback_refuses_unrelated_content(self):
        self.apply()
        op.QUEST.write_bytes(b'unrelated')
        with self.assertRaises(AssertionError):op.execute('rollback',b'new',b'recovery','reviewed')
        self.assertEqual(op.QUEST.read_bytes(),b'unrelated')

if __name__=='__main__':unittest.main()
