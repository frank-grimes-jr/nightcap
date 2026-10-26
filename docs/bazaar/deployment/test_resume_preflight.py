"""Continuation fault tests; no network, container or database changes."""
import contextlib,importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch,Mock
import test_rollout as fixture
try:import fcntl
except ImportError:sys.modules['fcntl']=types.ModuleType('fcntl')
import resume_preflight as continuation
op=fixture.op

@contextlib.contextmanager
def ready():
    with fixture.lifecycle(False) as state,patch.object(continuation,'op',op):
        state.evidence.mkdir();state.plan['checks']={'required':3}
        fixture.receipt(state.evidence/'preflight-started.json',state.plan)
        (op.STAGE/'preflight.log').write_text('assert shutil.disk_usage(ROOT).free>=RESERVE\nAssertionError\n')
        fixture.receipt(state.evidence/'scoped-cache-reclaim-reconciled.json',dict(cache_id='pyf6j6rkzq4pvi7al04hdmr6d',cache_absent=True,services_unchanged=True,activation_attempted=False,base_image='base',candidate_image='candidate'))
        def output(*args):
            if args[:3]==('docker','image','inspect'):
                if '--format' in args:return 'candidate'
                return json.dumps([{'RootFS':{'Layers':['base']+(['new'] if args[-1]=='candidate' else [])}}])
            return ''
        state.runtime.out=Mock(side_effect=output);state.runtime.call=Mock()
        yield state

class ContinuationTests(unittest.TestCase):
    def test_pass_without_service_mutations_and_no_replay(self):
        with ready() as s:
            continuation.resume()
            self.assertTrue((s.evidence/'preflight.json').exists())
            self.assertFalse(any(e[0] in ('stop','select','migration','enable') for e in s.runtime.events))
            with self.assertRaises(AssertionError):continuation.resume()
    def test_low_space_rejects(self):
        with ready() as s,patch.object(op.shutil,'disk_usage',return_value=types.SimpleNamespace(free=op.RESERVE-1)):
            with self.assertRaises(AssertionError):continuation.resume()
            self.assertFalse((s.evidence/'preflight.json').exists())
    def test_wrong_image_rejects(self):
        with ready() as s:
            s.runtime.image_hashes=lambda _:{}
            with self.assertRaises(AssertionError):continuation.resume()
    def test_service_drift_rejects(self):
        with ready() as s:
            s.runtime.running_services['gateway']=False
            with self.assertRaises(AssertionError):continuation.resume()
    def test_other_failure_rejects(self):
        with ready() as s:
            (op.STAGE/'preflight.log').write_text('unexpected failure')
            with self.assertRaises(AssertionError):continuation.resume()
    def test_rehearsal_failure_cannot_replay(self):
        with ready() as s,patch.object(op,'rehearse_storage',side_effect=RuntimeError('schema')):
            with self.assertRaises(RuntimeError):continuation.resume()
            self.assertTrue((s.evidence/'preflight-resume-started.json').exists())
            self.assertFalse((s.evidence/'preflight.json').exists())
            with self.assertRaises(AssertionError):continuation.resume()

if __name__=='__main__':unittest.main()
