"""Release-specific cache, policy and access-failure controls; no remote calls."""
import importlib.util,json,os,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
if os.name=='nt':sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=2,LOCK_NB=4,flock=lambda *a:None))
spec=importlib.util.spec_from_file_location('rollout',Path(__file__).with_name('rollout.py'));op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)

class ReleaseTests(unittest.TestCase):
    def test_rule_scope_preserves_other_rules(self):
        before='1\tAA:PassiveExpPercent\t10\n1\tCharacter:DeathExpLossLevel\t10\n1\tZone:KillProcessOnDynamicShutdown\tfalse\n2\tOther:Rule\t123\n'
        self.assertEqual(op.expected_rules(before),before.replace('DeathExpLossLevel\t10','DeathExpLossLevel\t256'))
        for bad in [before.replace('AA:PassiveExpPercent\t10','AA:PassiveExpPercent\t20'),before+'2\tCharacter:DeathExpLossLevel\t10\n',before.replace('Shutdown\tfalse','Shutdown\ttrue')]:
            with self.assertRaises(AssertionError):op.expected_rules(bad)
    def cache(self,p):
        count=5;current=2;data=bytearray(20+4*count+1332*current)
        struct.pack_into('<IIII',data,0,len(data)-8,count,current,current)
        for i in range(count):struct.pack_into('<I',data,16+4*i,0xffffffff)
        for i,(item,size) in enumerate([(1,20),(3,200)]):
            struct.pack_into('<I',data,16+4*item,i);start=16+4*count+1332*i
            struct.pack_into('<I',data,start+440,item);data[start+799]=1;struct.pack_into('<h',data,start+802,size)
        p.write_bytes(data);return data
    def test_cache_changes_only_planned_two_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'items';data=self.cache(p);actual=op.expected_cache(p,[(1,20)])
            struct.pack_into('<h',data,16+4*5+802,100)
            self.assertEqual(actual['sha256'],op.hashlib.sha256(data).hexdigest());self.assertEqual(actual['changed_fields'],1)
            # An unrelated price/stat byte must produce a different whole-cache hash.
            data[16+4*5+650]^=1;self.assertNotEqual(actual['sha256'],op.hashlib.sha256(data).hexdigest())
    def test_cache_rejects_stale_size_identity_or_stack_flag(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'items'
            for offset,value in [(802,21),(440,2),(799,0)]:
                data=self.cache(p);data[16+4*5+offset]=value;p.write_bytes(data)
                with self.assertRaises(AssertionError):op.expected_cache(p,[(1,20)])
    def test_death_rehearsal_rejection_never_attempts_mutation(self):
        with patch.object(op,'sql',return_value='0\n1\n'),patch.object(op,'save') as save:
            with self.assertRaises(AssertionError):op.apply_sql({'rules':''})
            save.assert_not_called()
    def test_activation_failure_holds_access_without_sql_restore(self):
        events=[];services={'game':{},'gateway':{}}
        r=types.SimpleNamespace(compact=lambda s:services[s],compose=lambda *args:(_ for _ in ()).throw(RuntimeError('stop failed')))
        with patch.object(op,'r',r),patch.object(op,'manifest',return_value={}),patch.object(op,'load',return_value={'manifest_sha256':'x','services':services}),patch.object(op,'sha',return_value='x'),patch.object(op,'untouched'),patch.object(op,'save'),patch.object(op,'hold',side_effect=lambda reason:events.append(reason)):
            with self.assertRaisesRegex(RuntimeError,'stop failed'):op.activate()
        self.assertEqual(len(events),1)
    def test_open_failure_before_or_after_access_always_holds(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p={'new_image_id':'new'};a={'game':{'id':'game'},'cache':{'sha256':'cache'},'runtime':{'started_at':'now'}}
            for failure in ['preservation','publish','open','post-open']:
                events=[]
                def fail_at(label):
                    if label==failure:raise RuntimeError(label)
                def compose(*args):events.append('open');fail_at('open')
                r=types.SimpleNamespace(state=lambda s:{'State':{'Running':'open' in events}},compact=lambda s:a['game'],compose=compose,closed_ports=lambda:None,running=lambda *args:(_ for _ in ()).throw(RuntimeError('post-open')) if failure=='post-open' else {'started_at':'now'})
                with patch.object(op,'EVIDENCE',root),patch.object(op,'r',r),patch.object(op,'manifest',return_value={'client_channel_sha256':'new'}),patch.object(op,'load',side_effect=lambda n:p if n=='preflight.json' else a if n=='activated-closed.json' else {}),patch.object(op,'preserved',side_effect=lambda d:fail_at('preservation')),patch.object(op,'untouched',side_effect=lambda *a:fail_at('publish')),patch.object(op,'health'),patch.object(op,'sha',return_value='cache'),patch.object(op,'binaries',return_value={}),patch.object(op,'save'),patch.object(op,'hold',side_effect=lambda why:events.append('hold')):
                    with self.assertRaises(RuntimeError):op.open_access()
                self.assertEqual(events[-1],'hold')
                if failure in ('preservation','publish'):self.assertNotIn('open',events)
    def test_existing_open_receipt_prevents_replay(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'opening.json').write_text('{}')
            with patch.object(op,'EVIDENCE',root),patch.object(op,'manifest'),patch.object(op,'load'),patch.object(op,'r') as r:
                with self.assertRaises(AssertionError):op.open_access()
                r.compose.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
