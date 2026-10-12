"""Exercise approved upgrade activation and recovery without any server connection."""
import importlib.util
from pathlib import Path
import sys,types,unittest
from unittest.mock import patch

sys.modules['runtime_ops']=types.SimpleNamespace(ROOT=Path('/not-a-server'))
if sys.platform=='win32':sys.modules['fcntl']=types.SimpleNamespace()
spec=importlib.util.spec_from_file_location('upgrade_rollout',Path(__file__).with_name('rollout.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

class Runtime:
    def __init__(self,failure):
        self.failure=failure;self.image='old';self.states={'game':True,'gateway':True}
        self.calls=[];self.installed=False;self.enabled=False;self.failed=False
        self.services={'game':{'image_id':'old'},'gateway':{'running':True}}
    def compact(self,name):
        return {'image_id':'drift'} if self.failure=='baseline' and name=='game' else self.services[name]
    def image_hashes(self,image):return {'bin/zone':image,'bin/world':'world'}
    def closed_ports(self):pass
    def state(self,name):return {'State':{'Running':self.states[name],'ExitCode':0,'OOMKilled':False}}
    def player_data(self):return {'inventory':'changed' if (self.failure=='data' and self.image=='new') or (self.failure=='gateway' and self.failed) else 'same'}
    def compose(self,*args):
        self.calls.append(args);self.states[args[-1]]=args[0]=='up'
        if args[0]=='up' and args[-1]=='gateway' and self.failure=='gateway' and not self.failed:
            self.failed=True;raise RuntimeError('lost gateway acknowledgment')
    def running(self,image,binaries):
        if image=='new' and self.failure=='health':raise RuntimeError('failed health')
        if image=='old' and self.failure=='recovery' and self.installed:raise RuntimeError('failed recovery')
        return {'started_at':image}
    def sql(self,query):
        if 'information_schema' in query:return '1' if self.installed else '0'
        if 'COUNT(*) FROM nightcap_item_upgrades' in query:return '1' if self.failure=='receipts' else '0'
        raise AssertionError(query)

class RolloutTests(unittest.TestCase):
    def execute(self,failure=None):
        import tempfile
        runtime=Runtime(failure);evidence={};selected=[];sql_calls=[]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'stage';stage.mkdir()
            (root/'data/server/quests/ecommons').mkdir(parents=True)
            (stage/'quests/ecommons').mkdir(parents=True)
            (stage/'quests/ecommons/999820.pl').write_text('quest')
            manifest={'binaries':{'zone':'new'},'base_binaries':{'zone':'old'},'files':{'quests/ecommons/999820.pl':'hash'}}
            prior={'manifest_sha256':'hash','old_image_id':'old','new_image_id':'new','old_hashes':{'bin/zone':'old','bin/world':'world'},'services':runtime.services,'policies':'rules','content':'content','backup':'backup'}
            def select(image):
                self.assertFalse(any(runtime.states.values()))
                selected.append(image);runtime.image=image
            def sql_file(name):
                self.assertFalse(runtime.states['gateway']);sql_calls.append(name)
                if name=='install.sql':
                    self.assertFalse(runtime.states['game']);runtime.installed=True
                    if failure=='install_ack':raise RuntimeError('lost install commit acknowledgment')
                elif name=='activate.sql':
                    runtime.enabled=True
                    if failure=='enable_ack':raise RuntimeError('lost enable acknowledgment')
                elif name=='rollback.sql':runtime.enabled=False
            def feature():return '1\t2026101201\t'+('1' if runtime.enabled else '0')
            def cache(new):
                if new and failure in ('cache','recovery'):raise RuntimeError('cache mismatch')
                return {'other_items_sha256':'same'}
            error=None
            with patch.object(q,'ROOT',root),patch.object(q,'STAGE',stage),patch.object(q,'r',runtime),\
                 patch.object(q,'manifest',return_value=manifest),patch.object(q,'load',return_value=prior),\
                 patch.object(q,'sha',return_value='hash'),patch.object(q,'policies',return_value='rules'),\
                 patch.object(q,'content',return_value='content'),patch.object(q,'extras',return_value={'old':'same'}),\
                 patch.object(q,'untouched'),patch.object(q,'select',side_effect=select),\
                 patch.object(q,'sql_file',side_effect=sql_file),patch.object(q,'feature_state',side_effect=feature),\
                 patch.object(q,'verify_content_rows'),patch.object(q,'cache_fingerprint',side_effect=cache),\
                 patch.object(q,'save',side_effect=lambda n,v:evidence.update({n:v})),patch.object(q.time,'sleep'):
                try:q.activate()
                except (AssertionError,RuntimeError) as caught:error=caught
            return runtime,evidence,selected,sql_calls,error
    def test_success(self):
        r,e,s,sql,error=self.execute();self.assertIsNone(error)
        self.assertEqual(s,['new']);self.assertTrue(r.enabled and all(r.states.values()))
        self.assertEqual(sql,['install.sql','activate.sql']);self.assertIn('verified-closed.json',e)
        self.assertFalse(e['activated.json']['database_restored'])
    def test_drift_never_stops(self):
        r,e,s,sql,error=self.execute('baseline');self.assertIsNotNone(error)
        self.assertEqual(r.calls,[]);self.assertEqual(sql,[])
    def test_failure_paths_disable_and_preserve_data(self):
        for failure in ('install_ack','health','cache','enable_ack','gateway'):
            with self.subTest(failure=failure):
                r,e,s,sql,error=self.execute(failure);self.assertIsNotNone(error)
                self.assertEqual(s[-1],'old');self.assertIn('rollback.sql',sql)
                self.assertFalse(r.enabled);self.assertTrue(all(r.states.values()))
                self.assertFalse(e['rolled-back.json']['database_restored'])
    def test_saved_data_drift_holds_gateway_closed(self):
        r,e,s,sql,error=self.execute('data');self.assertIsNotNone(error)
        self.assertFalse(r.states['gateway']);self.assertIn('held-closed.json',e)
        self.assertNotIn('rolled-back.json',e)
    def test_unexpected_receipts_hold_gateway_closed(self):
        r,e,s,sql,error=self.execute('receipts');self.assertIsNotNone(error)
        self.assertFalse(r.states['gateway']);self.assertIn('held-closed.json',e)
        self.assertNotIn('rolled-back.json',e)
    def test_failed_recovery_holds_gateway_closed(self):
        r,e,s,sql,error=self.execute('recovery');self.assertIsNotNone(error)
        self.assertFalse(r.states['gateway']);self.assertIn('held-closed.json',e)

class MaintenanceTests(unittest.TestCase):
    def test_active_maintenance_rejected(self):
        with patch.object(q.Path,'exists',return_value=True):
            with self.assertRaises(AssertionError):q.require_no_gm_work()
    def test_inflight_sql_rejected(self):
        with patch.object(q.Path,'exists',return_value=False),patch.object(q,'r',types.SimpleNamespace(sql=lambda _: '0')):
            with self.assertRaises(AssertionError):q.require_no_gm_work()

if __name__=='__main__':unittest.main(verbosity=2)
