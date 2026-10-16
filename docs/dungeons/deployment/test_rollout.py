"""Offline failure-boundary tests. No SSH, Docker, filesystem or SQL writes."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

runtime = types.SimpleNamespace(ROOT=Path('/not-production'))
sys.modules['runtime_ops'] = runtime
if sys.platform == 'win32':
    sys.modules['fcntl'] = types.SimpleNamespace()
old = types.ModuleType('previous_rollout')
old_loader = types.SimpleNamespace(create_module=lambda spec: None, exec_module=lambda module: module.__dict__.update(old.__dict__))
real_spec = importlib.util.spec_from_file_location
def source_spec(name, path):
    if name == 'previous_rollout':
        return importlib.util.spec_from_loader(name, old_loader)
    return real_spec(name, path)
with patch.object(importlib.util, 'spec_from_file_location', side_effect=source_spec):
    spec = real_spec('dungeon_rollout', Path(__file__).with_name('rollout.py'))
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)


class QueryTests(unittest.TestCase):
    def test_queries_stream_and_cap_session_memory(self):
        with patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='',stderr='')) as run:
            d.sql('SELECT 1;')
        self.assertIn('--quick',run.call_args.args[0])
        self.assertTrue(run.call_args.kwargs['input'].startswith('SET SESSION max_session_mem_used=134217728;'))

    def test_password_query_failure_never_echoes_credentials(self):
        with patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(returncode=1,stdout='',stderr='secret-password')):
            with self.assertRaises(RuntimeError) as caught:d.sql("CREATE USER test IDENTIFIED BY 'secret-password';")
        self.assertNotIn('secret-password',str(caught.exception))


class CacheTests(unittest.TestCase):
    def test_public_fingerprint_accepts_native_spawn2_identifier(self):
        def query(statement,database):
            return 'id\tint\n' if 'column_name,data_type' in statement else ''
        with patch.object(Path, 'read_text', return_value='{}'), patch.object(d, 'sql', side_effect=query):
            self.assertIn('spawn2', d.content())

    def test_items_unique_id_without_primary_is_preserved(self):
        def query(statement,database):
            if 's.index_name=\'ID\'' in statement:return 'id\t0\t0\tNO\n'
            if 'column_name,data_type' in statement:return 'id\tint\n'
            self.assertNotIn("table_name='items' AND index_name='PRIMARY'",statement)
            return ''
        with patch.object(Path,'read_text',return_value='{"items":[{"id":960000}]}'), patch.object(d,'sql',side_effect=query):
            self.assertIn('items',d.content())

    def test_preserves_every_existing_item(self):
        before = {1:'a',2:'b'}
        after = {**before, **{i:'new' for i in range(960000,960330)}}
        self.assertEqual(d.compare_cache(before, after)['existing_items_preserved'], 2)
        after[2] = 'different'
        with self.assertRaisesRegex(AssertionError, 'Existing item'):
            d.compare_cache(before, after)

    def test_missing_and_extra_items_rejected(self):
        after = {1:'a', **{i:'new' for i in range(960000,960330)}}
        del after[960001]
        with self.assertRaises(AssertionError):d.compare_cache({1:'a'}, after)
        after[960001]='new';after[42]='unexpected'
        with self.assertRaises(AssertionError):d.compare_cache({1:'a'}, after)

    def test_deleted_existing_item_rejected(self):
        after = {i:'new' for i in range(960000,960330)}
        with self.assertRaises(AssertionError):d.compare_cache({1:'a'}, after)


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.gateway=False;self.events=[];self.saved={};self.fail=None
        self.p={'manifest_sha256':'manifest','new_image_id':'new','old_hashes':{},'runtime':{}}
        self.a={'game':'game','runtime':{'started_at':'now'},'cache_sha256':'cache'}
        self.m={}
        self.patches=[]
        def apply(target, name, **kwargs):
            p=patch.object(target,name,create=True,**kwargs);self.patches.append(p);return p.start()
        apply(d,'manifest',return_value=self.m)
        apply(d,'load',side_effect=lambda name:{'preflight.json':self.p,'activated-closed.json':self.a,'stopped-data.json':{}}[name])
        apply(d,'sha',side_effect=lambda p:'manifest' if p.name=='manifest.json' else 'cache')
        apply(Path,'exists',return_value=False);apply(Path,'glob',return_value=[])
        apply(d.r,'state',side_effect=lambda name:{'State':{'Running':self.gateway}})
        apply(d.r,'compact',return_value='game')
        apply(d,'preserved',side_effect=lambda data:self.events.append('preserved'))
        apply(d,'unchanged',side_effect=lambda *args:self.events.append('unchanged'))
        apply(d,'sql',return_value='2026101601\t1')
        apply(d,'binaries',return_value={})
        apply(d.r,'running',side_effect=self.running)
        apply(d.q,'verify_publication',return_value={'verified':True})
        apply(d.r,'closed_ports',return_value=None)
        apply(d,'save',side_effect=self.save)
        apply(d.r,'compose',side_effect=self.compose)
        apply(d,'hold',side_effect=lambda reason, uncertain=False:self.events.append(('held',uncertain)))

    def tearDown(self):
        for p in reversed(self.patches):p.stop()

    def save(self,name,value):
        self.events.append(name);self.saved[name]=value
        if self.fail=='opening_journal' and name=='opening.json':raise OSError('disk full')

    def compose(self,*args):
        self.events.append('open');self.gateway=True
        if self.fail=='open_ack':raise RuntimeError('lost acknowledgment')

    def running(self,*args,**kwargs):
        if self.fail=='post_open' and self.gateway:raise RuntimeError('health failed')
        return {'started_at':'now'}

    def test_open_receipt_precedes_gateway_and_no_late_player_comparison(self):
        d.open_access()
        self.assertLess(self.events.index('opening.json'),self.events.index('open'))
        self.assertEqual(self.events.count('preserved'),1)
        self.assertLess(self.events.index('preserved'),self.events.index('open'))
        self.assertTrue(self.saved['activated.json']['gateway_open'])

    def test_lost_open_ack_holds_without_restore_or_replay(self):
        self.fail='open_ack'
        with self.assertRaises(RuntimeError):d.open_access()
        self.assertIn(('held',True),self.events)
        self.assertNotIn('activated.json',self.saved)
        self.assertEqual(self.events.count('open'),1)

    def test_post_open_failure_preserves_activity(self):
        self.fail='post_open'
        with self.assertRaises(RuntimeError):d.open_access()
        self.assertIn(('held',True),self.events)
        self.assertEqual(self.events.count('preserved'),1)

    def test_failed_open_journal_does_not_open(self):
        self.fail='opening_journal'
        with self.assertRaises(OSError):d.open_access()
        self.assertNotIn('open',self.events)
        self.assertIn(('held',False),self.events)

    def test_existing_open_gateway_never_replayed(self):
        self.gateway=True
        with self.assertRaises(RuntimeError):d.open_access()
        self.assertIn(('held',True),self.events)
        self.assertNotIn('open',self.events)

    def test_changed_manifest_refuses_before_open(self):
        self.p['manifest_sha256']='changed'
        with self.assertRaises(AssertionError):d.open_access()
        self.assertNotIn('open',self.events)

    def test_old_cache_refuses_before_open(self):
        self.a['cache_sha256']='stale'
        with self.assertRaises(AssertionError):d.open_access()
        self.assertNotIn('open',self.events)
        self.assertIn(('held',False),self.events)

    def test_native_failure_refuses_before_open(self):
        with patch.object(d.r,'running',side_effect=RuntimeError('native mismatch')):
            with self.assertRaises(RuntimeError):d.open_access()
        self.assertNotIn('open',self.events)

    def test_replayed_open_refused(self):
        self.gateway=True
        with patch.object(Path,'exists',return_value=True):
            with self.assertRaises(RuntimeError):d.open_access()
        self.assertNotIn('open',self.events)
        self.assertIn(('held',True),self.events)


class ActivationTests(unittest.TestCase):
    def test_schema_failure_holds_access_without_image_or_inventory_restore(self):
        from contextlib import ExitStack
        p={'manifest_sha256':'hash','services':{'game':'game','gateway':'gateway'},
           'new_image_id':'new','runtime':{d.QUEST:'hash'}}
        m={'files':{'sql/20261016_dungeons.sql':'schema','sql/20261016_dungeon_content.sql':'content'}}
        events=[]
        with ExitStack() as stack:
            def mock(obj,name,**kwargs):return stack.enter_context(patch.object(obj,name,create=True,**kwargs))
            mock(d,'manifest',return_value=m);mock(d,'load',return_value=p)
            mock(d,'sha',return_value='hash');mock(Path,'exists',return_value=False)
            mock(d.r,'compact',side_effect=lambda n:n);mock(d,'unchanged',return_value=None)
            mock(d.r,'image_hashes',return_value={});mock(d,'expected_image',return_value={})
            mock(d,'save',side_effect=lambda n,v:events.append(n))
            commands=mock(d.r,'compose',side_effect=lambda *a:events.append(a))
            mock(d.q,'stopped',return_value=None);mock(d.r,'player_data',return_value={'inventory':'present'})
            mock(d,'custom',return_value={});mock(d.r,'database_backup',return_value={'verified':True})
            mock(d.shutil,'copy2',return_value=None);mock(Path,'read_text',return_value='SCHEMA')
            query=mock(d,'sql',side_effect=RuntimeError('injected schema failure'))
            selection=mock(d.q,'select');held=mock(d,'hold',side_effect=lambda *a:events.append('held'))
            with self.assertRaisesRegex(RuntimeError,'injected schema'):d.activate()
            self.assertIn(('stop','gateway'),events)
            self.assertIn(('stop','-t','90','game'),events)
            self.assertLess(events.index('backup.json'),events.index('sql-attempted.json'))
            self.assertEqual(query.call_count,1)
            selection.assert_not_called();held.assert_called_once()
            self.assertTrue(all(call.args[0]=='stop' for call in commands.call_args_list))


if __name__=='__main__':unittest.main()
