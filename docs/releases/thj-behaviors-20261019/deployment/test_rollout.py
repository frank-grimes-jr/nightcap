"""Fault injection for the paired operator; no production connection."""
import contextlib
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

if os.name == 'nt':
    sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=2,LOCK_NB=4,flock=lambda *a:None))
spec = importlib.util.spec_from_file_location('thj_rollout',Path(__file__).with_name('rollout.py'))
op = importlib.util.module_from_spec(spec); spec.loader.exec_module(op)


class Runtime:
    def __init__(self, root):
        self.root=root; self.events=[]; self.services={'game':True,'gateway':True,'db':True,'web':True,'tunnel':True}
        self.image='old'; self.fail=None
    def compact(self,n): return {'running':self.services[n],'image':self.image if n=='game' else n}
    def state(self,n): return {'Id':n,'State':{'Running':self.services[n],'ExitCode':0,'OOMKilled':False}}
    def compose(self,*args):
        self.events.append(args)
        if args[0]=='stop': self.services[args[-1]]=False
        elif args[0]=='up': self.services[args[-1]]=True
        if self.fail: self.fail(args)
    def database_backup(self):
        self.events.append(('backup',)); (self.root/'private-backup').mkdir()
        return {'gzip_integrity':'passed'}
    def select(self,image): self.events.append(('select',image)); self.image=image
    def running(self,*args): return {'started_at':'2026-10-19T01:00:00Z'}
    def closed_ports(self): pass


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as d, contextlib.ExitStack() as stack:
        root=Path(d); evidence=root/'evidence'; evidence.mkdir()
        (root/'data/server/shared').mkdir(parents=True)
        for n in ('items','spells'): (root/'data/server/shared'/n).write_bytes(b'x'*1000001)
        runtime=Runtime(root); data={'player':{'inventory':'owned'},'custom':{'timers':'saved'}}
        for n,v in {'ROOT':root,'STAGE':root,'EVIDENCE':evidence,'r':runtime,'b':Mock()}.items():
            stack.enter_context(patch.object(op,n,v))
        components=['01.sql','02.sql']
        for n in components: (root/n).write_text(n)
        stack.enter_context(patch.object(op,'manifest',return_value={'components':components,'files':{n:'hash' for n in components}}))
        stack.enter_context(patch.object(op,'sha',return_value='digest'))
        stack.enter_context(patch.object(op,'untouched'))
        stack.enter_context(patch.object(op,'guards'))
        stack.enter_context(patch.object(op,'health'))
        stack.enter_context(patch.object(op,'binaries',return_value={'zone':'new'}))
        stack.enter_context(patch.object(op,'saved_state',return_value=data))
        stack.enter_context(patch.object(op.time,'sleep'))
        stack.enter_context(patch.object(op.shutil,'disk_usage',return_value=types.SimpleNamespace(free=10*1024**3)))
        op.b.market.return_value=['before']; op.b.verify_market.return_value={'rotation':'once'}
        queries=[]
        def sql(q): queries.append(q); return 'rules' if q.startswith('SELECT') else ''
        stack.enter_context(patch.object(op,'sql',side_effect=sql))
        op.save(evidence/'preflight.json',{'manifest_sha256':'digest','services':{s:runtime.compact(s) for s in runtime.services},'new_image_id':'new','rules_after':'rules'})
        yield root,evidence,runtime,queries


class DeploymentTests(unittest.TestCase):
    def test_content_names_allow_spawn2_without_allowing_sql(self):
        with patch.object(op,'sql',return_value='peq.spawn2\t123\n'):
            self.assertEqual(op.checksums(['spawn2']),{'spawn2':'123'})
            with self.assertRaises(AssertionError): op.checksums(['spawn2;DROP'])

    def test_exact_pet_constraint_only(self):
        old='CONSTRAINT `pet_armor_slot` CHECK (`slot_id` in (2,17,7,9,12,18,19,20))'
        self.assertIn('between 0 and 21',op.expected_schema(old))
        for bad in (old.replace('20','21'),old+old,'CHECK (slot_id between 0 and 7)'):
            with self.assertRaises(AssertionError): op.expected_schema(bad)

    def test_routing_preserves_actual_classic_mask(self):
        actual='Character:MaxLevel\t50\nWorld:ExpansionSettings\t2097151\nExpansion:CurrentExpansion\t0\n'
        with patch.object(op,'sql',side_effect=['1',actual,'sets','selection']):
            self.assertEqual(op.routing(),{'sets':'sets','selection':'selection'})
        for bad in ('10',):
            with patch.object(op,'sql',return_value=bad), self.assertRaises(AssertionError): op.routing()
        with patch.object(op,'sql',side_effect=['1',actual.replace('\t50','\t65')]), self.assertRaises(AssertionError): op.routing()

    def test_rule_changes_are_not_mistaken_for_player_drift(self):
        r=Mock(); r.player_data.return_value={'inventory':{'hash':'saved'},'rule_values':{'hash':'old'}}
        with patch.object(op,'r',r), patch.object(op,'sql',return_value='timers\nnightcap_market_state\n'), patch.object(op,'checksums',return_value={'timers':'saved'}) as check:
            self.assertEqual(op.saved_state(),{'player':{'inventory':{'hash':'saved'}},'custom':{'timers':'saved'}})
            check.assert_called_once_with(['timers'])

    def test_activation_order_and_closed_gateway(self):
        with fixture() as (root,e,r,queries):
            op.activate()
            self.assertFalse(r.services['gateway']); self.assertTrue(r.services['game'])
            self.assertEqual(r.events[:3],[('stop','gateway'),('stop','-t','90','game'),('backup',)])
            self.assertLess(r.events.index(('select','new')),r.events.index(('run','--rm','--no-deps','--entrypoint','/opt/nightcap/bin/shared_memory','game')))
            self.assertTrue((e/'02-committed.json').exists())
            self.assertTrue((e/'activated-closed.json').exists())
            with self.assertRaises(AssertionError): op.activate()

    def test_component_failure_holds_both_and_never_replays(self):
        with fixture() as (root,e,r,queries):
            def fail(q):
                queries.append(q)
                if q=='02.sql': raise RuntimeError('component rejected')
                return ''
            with patch.object(op,'sql',side_effect=fail),self.assertRaises(RuntimeError): op.activate()
            self.assertEqual(queries,['01.sql','02.sql'])
            self.assertTrue((e/'01-committed.json').exists())
            self.assertTrue((e/'02-attempted.json').exists()); self.assertFalse((e/'02-committed.json').exists())
            self.assertFalse(r.services['game']); self.assertFalse(r.services['gateway'])
            self.assertNotIn(('select','new'),r.events)
            with self.assertRaises(AssertionError): op.activate()

    def test_backup_failure_never_writes_content(self):
        with fixture() as (root,e,r,queries):
            with patch.object(r,'database_backup',side_effect=RuntimeError('backup')),self.assertRaises(RuntimeError): op.activate()
            self.assertEqual(queries,[]); self.assertFalse(r.services['game']); self.assertFalse(r.services['gateway'])

    def test_cache_generation_failure_keeps_world_stopped(self):
        with fixture() as (root,e,r,queries):
            def fail(args):
                if args[0]=='run': raise RuntimeError('loader failed')
            r.fail=fail
            with self.assertRaises(RuntimeError): op.activate()
            self.assertFalse(r.services['game']); self.assertFalse(r.services['gateway'])
            self.assertFalse(any(x[0]=='up' for x in r.events))

    def test_public_assets_all_required_before_access(self):
        with tempfile.TemporaryDirectory() as d, patch.object(op,'ROOT',Path(d)),patch.object(op,'STAGE',Path(d)):
            root=Path(d); (root/'client').mkdir(); (root/'data/public/release/2026101902').mkdir(parents=True)
            entries={}
            for i in range(138):
                p=root/'data/public/release/2026101902'/str(i); p.write_bytes(b'asset')
                entries['release/2026101902/'+str(i)]={'size':5,'sha256':op.sha(p)}
            p=root/'data/public/channel.json'; p.write_bytes(b'channel'); digest=op.sha(p)
            entries['channel.json']={'size':7,'sha256':digest}
            op.save(root/'client/publication-files.json',entries)
            op.save(root/'client/published.json',{'release':2026101902,'verified_files':138,'channel_sha256':digest})
            op.save(root/'client/hosted-verification.json',{'release':2026101902,'hosted':True,'managed_files':138,
                'channel_sha256':digest,'signature':'valid against shipped production key','verified_bytes':690})
            with patch.object(op,'manifest',return_value={'files':{'client/channel.json':digest}}):
                op.published_client()
                (root/'data/public/release/2026101902/137').write_bytes(b'wrong')
                with self.assertRaises(AssertionError): op.published_client()


if __name__=='__main__': unittest.main()
