"""Exercise activation and recovery with fake services; never contacts a server."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.modules['runtime_ops']=types.SimpleNamespace(ROOT=Path('/not-a-server'))
if sys.platform=='win32':
    sys.modules['fcntl']=types.SimpleNamespace()
spec=importlib.util.spec_from_file_location('food_rollout',Path(__file__).with_name('rollout.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

class Runtime:
    def __init__(self, failure=None):
        self.failure=failure;self.image='old';self.states={'game':True,'gateway':True};self.calls=[]
        self.services={'game':{'image_id':'old'},'gateway':{'running':True}}
        self.failed=False;self.drift=False;self.custom_drift=False
    def compact(self,name):
        if self.failure=='baseline' and name=='game':return {'image_id':'different'}
        return self.services[name]
    def image_hashes(self,image):return {'bin/zone':image,'bin/world':'world'}
    def untouched(self,p):pass
    def closed_ports(self):pass
    def content_data(self):return 'content'
    def state(self,name):return {'State':{'Running':self.states[name],'ExitCode':0,'OOMKilled':False}}
    def player_data(self):
        if self.image=='new' and self.failure=='data':self.drift=True
        return {'inventory':('changed' if self.drift else 'same')}
    def extras(self):
        if self.image=='new' and self.failure=='custom':self.custom_drift=True
        return {'loot':('2' if self.custom_drift else '1')}
    def compose(self,*args):
        self.calls.append(args);service=args[-1]
        self.states[service]=args[0]=='up'
        if args[0]=='up' and service=='gateway' and self.failure=='gateway' and not self.failed:
            self.failed=True;raise RuntimeError('Lost gateway acknowledgment')
    def running(self,image,binaries):
        if image=='new' and self.failure=='health':raise RuntimeError('Unhealthy candidate')
        return {'started_at':image}

class RolloutTests(unittest.TestCase):
    def execute(self,failure=None):
        runtime=Runtime(failure);evidence={};selected=[]
        manifest={'binaries':{'zone':'new','world':'world'},'base_binaries':{'zone':'old','world':'world'}}
        preflight={'manifest_sha256':'manifest','old_image_id':'old','new_image_id':'new',
                   'old_hashes':{'bin/zone':'old','bin/world':'world'},'services':runtime.services,
                   'policies':'rules','content':'content','backup':'backup'}
        def select(image):
            self.assertFalse(any(runtime.states.values()),'image selected while services still running')
            selected.append(image);runtime.image=image
        error=None
        with patch.object(q,'r',runtime),patch.object(q,'manifest',return_value=manifest),\
             patch.object(q,'load',return_value=preflight),patch.object(q,'sha',return_value='manifest'),\
             patch.object(q,'policies',return_value='rules'),patch.object(q,'extras',side_effect=runtime.extras),\
             patch.object(q,'select',side_effect=select),patch.object(q,'save',side_effect=lambda n,v:evidence.update({n:v})),\
             patch.object(q.time,'sleep'):
            try:q.activate()
            except (AssertionError,RuntimeError) as e:error=e
        return runtime,evidence,selected,error
    def test_success_opens_after_saved_data_check(self):
        r,e,s,error=self.execute();self.assertIsNone(error)
        self.assertEqual(s,['new']);self.assertTrue(all(r.states.values()))
        self.assertIn('verified-closed.json',e);self.assertIn('activated.json',e)
        self.assertFalse(e['activated.json']['database_restored'])
    def test_baseline_drift_never_stops_live_services(self):
        r,e,s,error=self.execute('baseline');self.assertIsNotNone(error)
        self.assertEqual(r.calls,[]);self.assertEqual(s,[])
    def test_unhealthy_candidate_restores_prior_image(self):
        r,e,s,error=self.execute('health');self.assertIsNotNone(error)
        self.assertEqual(s,['new','old']);self.assertTrue(all(r.states.values()))
        self.assertFalse(e['rolled-back.json']['database_restored'])
    def test_saved_data_drift_rejects_candidate(self):
        r,e,s,error=self.execute('data');self.assertIsNotNone(error)
        self.assertEqual(s,['new','old']);self.assertNotIn('activated.json',e)
        self.assertFalse(r.states['gateway']);self.assertTrue(r.states['game'])
        self.assertIn('recovery-held.json',e);self.assertNotIn('rolled-back.json',e)
    def test_custom_data_drift_keeps_gateway_closed(self):
        r,e,s,error=self.execute('custom');self.assertIsNotNone(error)
        self.assertEqual(s,['new','old']);self.assertFalse(r.states['gateway'])
        self.assertIn('recovery-held.json',e);self.assertNotIn('rolled-back.json',e)
    def test_lost_gateway_ack_closes_before_recovery(self):
        r,e,s,error=self.execute('gateway');self.assertIsNotNone(error)
        self.assertEqual(s,['new','old']);self.assertTrue(all(r.states.values()))
        self.assertFalse(e['rolled-back.json']['database_restored'])

class MaintenanceTests(unittest.TestCase):
    def test_inflight_gm_sql_rejected(self):
        with patch.object(q.Path,'exists',return_value=False), patch.object(q,'r',types.SimpleNamespace(sql=lambda _: '0')):
            with self.assertRaisesRegex(AssertionError,'GM SQL'): q.require_no_gm_work()
    def test_existing_gm_maintenance_rejected(self):
        with patch.object(q.Path,'exists',return_value=True):
            with self.assertRaisesRegex(AssertionError,'GM maintenance'): q.require_no_gm_work()
    def test_idle_gm_is_allowed(self):
        with patch.object(q.Path,'exists',return_value=False), patch.object(q,'r',types.SimpleNamespace(sql=lambda _: '1')):
            q.require_no_gm_work()

if __name__=='__main__':unittest.main(verbosity=2)
