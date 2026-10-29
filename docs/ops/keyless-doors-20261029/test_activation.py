import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if sys.platform == 'win32':
    sys.modules.setdefault('fcntl', types.SimpleNamespace())


def load(name):
    spec = importlib.util.spec_from_file_location('door_' + name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.op = load('activate')
        self.op.ROOT = Path(self.tmp.name)
        self.op.OUT = self.op.ROOT/'evidence'
        self.op.EXPECTED = {'doors': [{'id':1,'zone':'paineel','keyitem':6378,'lockpick':60,'guild':0}]}
        self.current = copy.deepcopy(self.op.EXPECTED)
        self.op.CAPTURE_SOURCE = ''
        self.op.RUNTIME_SOURCE = 'unused at mocked game boundary'
        self.op.FORWARD = 'reviewed forward'
        self.op.ROLLBACK = 'reviewed inverse'
        self.op.MAIN_REVISION = 'reviewed'
        self.op.EXPECTED_IMAGE = 'same-image'
        self.state = {'/nightcap-production-game-1':{'image':'same-image'}}
        self.workers = {'workers':[{'pid':31,'start':'123'}],
                        'targets':[{'server_id':6,'pid':31,'zone':'paineel','logs':{}}], 'locks':[]}
        self.calls = []

    def call(self, args, source=None):
        self.calls.append((args,source))
        if source == self.op.FORWARD:
            self.current = self.op.expected_after(self.current)
        return ''

    def execute(self, fail_reload=False, bad_postimage=False, fail_hold=False, fail_release=False, occupied=False):
        op=self.op
        def execute_capture(source, namespace):
            namespace['capture'] = lambda: copy.deepcopy(self.current)
        held=False
        def remote(mode, targets=None, expected_locks=None):
            nonlocal held
            if mode=='hold':
                held=True
                if fail_hold:raise RuntimeError('Lost hold acknowledgment')
                return {'before':[],'after':[75],'held':True}
            if mode=='release':
                if fail_release:raise RuntimeError('Lost release acknowledgment')
                return {'before':[75],'after':[],'held':False}
            if mode=='probe' and held and occupied:raise AssertionError('Affected zone occupied')
            if mode=='reload' and fail_reload:
                raise RuntimeError('Injected reload failure')
            return copy.deepcopy(self.workers)
        def call(args, source=None):
            value=self.call(args,source)
            if bad_postimage and source==op.FORWARD:self.current['doors'][0]['guild']=7
            return value
        proc=types.SimpleNamespace(stdout=io.BytesIO(b'x'*1100000),wait=lambda **kw:0,poll=lambda:0)
        with patch.object(op,'exec',execute_capture,create=True), \
             patch.object(op,'services',lambda:self.state), \
             patch.object(op,'runtime',remote), patch.object(op,'run',call), \
             patch.object(op,'game',lambda source:{'31':['Zone Static Data Reloaded']}), \
             patch.object(op.subprocess,'Popen',lambda *a,**k:proc), \
             patch.object(op.shutil,'disk_usage',lambda p:types.SimpleNamespace(free=1024**3)), \
             patch.object(op.time,'sleep',lambda n:None):
            return op.execute()

    def test_success_preserves_nonlock_fields_and_records_backup_and_refresh(self):
        result=self.execute()
        self.assertEqual(result['status'],'activated_verified')
        self.assertTrue(result['backup_verified'])
        self.assertEqual(self.current['doors'][0]['guild'],0)
        self.assertEqual(sum(src==self.op.FORWARD for _,src in self.calls),1)

    def test_preimage_drift_prevents_backup_and_commit(self):
        self.current['doors'][0]['guild']=7
        with self.assertRaisesRegex(AssertionError,'preimage'):self.execute()
        self.assertFalse(self.op.OUT.exists())
        self.assertEqual(self.calls,[])

    def test_existing_operation_cannot_replay(self):
        self.op.OUT.mkdir()
        with self.assertRaisesRegex(AssertionError,'Existing operation'):self.execute()
        self.assertEqual(self.calls,[])

    def test_uncertain_refresh_retains_committed_state_and_receipt(self):
        with self.assertRaisesRegex(RuntimeError,'reload failure'):self.execute(fail_reload=True)
        result=json.loads((self.op.OUT/'result.json').read_text())
        self.assertEqual(result['status'],'committed_reload_pending')
        self.assertEqual(self.current['doors'][0]['keyitem'],0)
        self.assertFalse(any(src==self.op.ROLLBACK for _,src in self.calls))

    def test_wrong_postimage_cannot_claim_success(self):
        with self.assertRaisesRegex(AssertionError,'Post-write'):self.execute(bad_postimage=True)
        self.assertEqual(json.loads((self.op.OUT/'result.json').read_text())['status'],'commit_started')

    def test_existing_native_hold_is_not_owned(self):
        self.workers['locks']=[75]
        with self.assertRaisesRegex(AssertionError,'already locked'):self.execute()
        self.assertEqual(self.calls,[])
        self.assertFalse(self.op.OUT.exists())

    def test_lost_hold_ack_preserves_preimage_without_sql(self):
        with self.assertRaisesRegex(RuntimeError,'Lost hold'):self.execute(fail_hold=True)
        receipt=json.loads((self.op.OUT/'result.json').read_text())
        self.assertEqual(receipt['admission_locks_before'],[])
        self.assertEqual(receipt['status'],'admission_hold_requested')
        self.assertFalse(any(src==self.op.FORWARD for _,src in self.calls))

    def test_occupied_after_drain_retains_hold_without_sql(self):
        with self.assertRaisesRegex(AssertionError,'occupied'):self.execute(occupied=True)
        receipt=json.loads((self.op.OUT/'result.json').read_text())
        self.assertEqual(receipt['status'],'admission_held_draining')
        self.assertTrue(receipt['admission_hold']['held'])
        self.assertFalse(any(src==self.op.FORWARD for _,src in self.calls))

    def test_lost_release_ack_preserves_uncertainty(self):
        with self.assertRaisesRegex(RuntimeError,'Lost release'):self.execute(fail_release=True)
        receipt=json.loads((self.op.OUT/'result.json').read_text())
        self.assertEqual(receipt['status'],'refreshed_admission_release_pending')
        self.assertFalse(any(src==self.op.ROLLBACK for _,src in self.calls))


class RuntimeTests(unittest.TestCase):
    def test_status_parse_and_empty_affected_selection(self):
        runtime=load('runtime')
        rows=[f'#{i} :: D :: 127.0.0.1:9001 :: 0 :: 127.77.0.1:7001 :: '+
              ('paineel (75)' if i==6 else '')+f' :: ({i+20})' for i in range(1,13)]
        parsed=runtime.parse_status('^'.join(rows)+'^13 servers listed. 13 servers online.^1 zones available.')
        self.assertEqual([r['server_id'] for r in runtime.selected(parsed,['Paineel'])],[6])
        parsed[5]['players']=1
        with self.assertRaisesRegex(AssertionError,'occupied'):runtime.selected(parsed,['paineel'])
        with self.assertRaises(AssertionError):runtime.parse_status('^'.join(rows[:-1]))


if __name__=='__main__':
    unittest.main()
