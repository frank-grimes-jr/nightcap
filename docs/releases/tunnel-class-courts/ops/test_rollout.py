"""Fault tests for the production orchestration; never contacts a server."""
import copy
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,MagicMock
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tools/tests'))
from test_tunnel_courts import fixture
spec=importlib.util.spec_from_file_location('courts_rollout',Path(__file__).with_name('rollout.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class RolloutTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(r,'EVIDENCE',self.base))
        (self.base/'forward.sql').write_text('FORWARD')
        self.before={'character_currency':dict(rows=1,sha256='preserved')}
        self.m={'runtime':[],'scene_sha256':'scene'}
        self.records={'preservation-before.json':self.before,'epoch-before.json':{'epoch':5},
                      'preflight.json':{'runtime':{}},'before-content.json':{'rows':{}},'after-content.json':{'rows':{}}}
        self.mocks={}
        for name in ['manifest','stopped','new_files','verified_target','fingerprints','install',
                     'verify_geometry_inputs','scene_hash','runtime_files','verify_quests','installed_files','compose','running','exact','call','save','state','load','sql']:
            self.mocks[name]=self.stack.enter_context(patch.object(r,name))
        self.mocks['manifest'].return_value=self.m
        self.mocks['scene_hash'].return_value='scene'
        self.mocks['runtime_files'].side_effect=lambda: {e['target']:e['sha256'] for e in self.m['runtime']} if self.mocks['install'].called else {}
        self.m['source_commit']='approved'
        self.mocks['fingerprints'].side_effect=lambda:self.before.copy()
        self.mocks['load'].side_effect=lambda name:self.records[name]
        self.mocks['running'].return_value={'healthy':True}
        self.mocks['state'].return_value={'State':{'Running':True}}
        def sql(q):
            if 'SELECT epoch' in q:return '6'
            if 'SELECT kind' in q:return 'find\t10\t10\nsell\t20\t20\nbuy\t12\t12\n'
            return ''
        self.mocks['sql'].side_effect=sql
    def gateway_opened(self):
        return any(c.args==('up','-d','--wait','--wait-timeout','60','gateway') for c in self.mocks['compose'].call_args_list)
    def fails_closed(self):
        with self.assertRaises((AssertionError,RuntimeError)):r.apply()
        self.assertFalse(self.gateway_opened())
    def test_success_opens_only_after_verification_record(self):
        events=[]
        self.mocks['save'].side_effect=lambda n,v:events.append(n)
        self.mocks['compose'].side_effect=lambda *a:events.append('open' if a[-1]=='gateway' else 'start')
        r.apply();self.assertTrue(self.gateway_opened())
        self.assertLess(events.index('verified-before-open.json'),events.index('open'))
    def test_target_drift_prevents_sql_and_start(self):
        self.mocks['verified_target'].side_effect=AssertionError('drift');self.fails_closed()
        self.mocks['sql'].assert_not_called();self.mocks['compose'].assert_not_called()
    def test_occupied_runtime_path_prevents_sql(self):
        self.mocks['new_files'].side_effect=AssertionError('occupied');self.fails_closed()
        self.mocks['sql'].assert_not_called()
    def test_sql_failure_never_installs_or_starts(self):
        self.mocks['sql'].side_effect=RuntimeError('SQL guard');self.fails_closed()
        self.mocks['install'].assert_not_called();self.mocks['compose'].assert_not_called()
    def test_afterimage_failure_prevents_install(self):
        self.mocks['exact'].side_effect=AssertionError('afterimage');self.fails_closed()
        self.mocks['install'].assert_not_called()
    def test_file_failure_leaves_gateway_closed(self):
        self.mocks['install'].side_effect=RuntimeError('disk');self.fails_closed()
        self.mocks['compose'].assert_not_called()
    def test_startup_failure_leaves_gateway_closed(self):
        self.mocks['running'].side_effect=AssertionError('unhealthy');self.fails_closed()
    def test_post_start_preservation_failure_leaves_gateway_closed(self):
        self.mocks['fingerprints'].side_effect=[self.before,self.before,{'currency':'changed'}]
        self.fails_closed()
    def test_runtime_hash_failure_leaves_gateway_closed(self):
        self.mocks['installed_files'].side_effect=[None,AssertionError('hash')];self.fails_closed()
    def test_unexpected_epoch_leaves_gateway_closed(self):
        self.mocks['sql'].side_effect=lambda q:'8' if 'SELECT epoch' in q else ''
        self.fails_closed()
    def test_quest_compile_failure_leaves_gateway_closed(self):
        self.m['runtime']=[{'target':'quests/ecommons/999527.pl','sha256':'file'}]
        self.mocks['call'].side_effect=RuntimeError('compile');self.fails_closed()
    def test_matching_rows_are_order_independent(self):
        a={'rows':{t:[{'id':'2'},{'id':'1'}] for t in r.content.KEYS}}
        b=copy.deepcopy(a)
        for rows in b['rows'].values():rows.reverse()
        self.assertTrue(r.matches(a,b))
        b['rows']['npc_types'][0]['id']='3';self.assertFalse(r.matches(a,b))
    def test_rollback_drift_leaves_gateway_closed_and_files_intact(self):
        (self.base/'apply-started.json').write_text('{}')
        with patch.object(r.content,'capture',return_value={'rows':{}}),patch.object(r,'matches',return_value=False),patch.object(r.content,'rollback_target',side_effect=ValueError('ambiguous guide state')):
            with self.assertRaises(ValueError):r.rollback()
        self.assertFalse(self.gateway_opened());self.mocks['sql'].assert_not_called()
    def test_rollback_uses_fresh_preservation_after_open(self):
        (self.base/'verified-before-open.json').write_text('{}')
        self.records['preservation-before.json']={'outdated':'before play'}
        r.rollback();self.assertTrue(self.gateway_opened())

    def test_map_drift_prevents_sql_and_install(self):
        self.mocks['verify_geometry_inputs'].side_effect=AssertionError('map changed');self.fails_closed()
        self.mocks['sql'].assert_not_called();self.mocks['install'].assert_not_called()
    def test_scene_drift_prevents_sql(self):
        self.mocks['scene_hash'].return_value='changed';self.fails_closed()
        self.mocks['sql'].assert_not_called()
    def test_existing_plugin_drift_prevents_sql(self):
        self.mocks['runtime_files'].side_effect=lambda:{'unrelated.pl':'changed'};self.fails_closed()
        self.mocks['sql'].assert_not_called()
    def test_installed_quest_failure_never_opens_gateway(self):
        self.mocks['verify_quests'].side_effect=RuntimeError('quest failure');self.fails_closed()

class FileTests(unittest.TestCase):
    def test_after_start_saved_state_rejects_other_instances(self):
        before=fixture()
        after=r.content.desired(before);current=copy.deepcopy(after)
        current['rows']['zone_state_spawns']=[dict(id='1',npc_id='999527',spawngroup_id='999527',spawn2_id='999527',zone_id='22',instance_id='1',is_corpse='0',is_zone='0')]
        with patch.object(r.content,'capture',return_value=current),patch.object(r,'load',return_value=before):
            with self.assertRaises(ValueError):r.exact(after,allow_saved=True)
        current['rows']['zone_state_spawns'][0]['instance_id']='0'
        with patch.object(r.content,'capture',return_value=current),patch.object(r,'load',return_value=before):
            self.assertIs(r.exact(after,allow_saved=True),current)
    def test_atomic_install_rejects_collision_without_removing_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);target=base/'data/server/quests/a.pl';target.parent.mkdir(parents=True)
            source=base/'source.pl';source.write_bytes(b'new');target.write_bytes(b'existing')
            m={'runtime':[dict(source='source.pl',target='quests/a.pl',sha256=r.digest(b'new'))]}
            with patch.object(r,'ROOT',base),patch.object(r,'STAGE',base),patch.object(r.os,'chown',create=True):
                with self.assertRaises(FileExistsError):r.install(m)
            self.assertEqual(target.read_bytes(),b'existing');self.assertFalse(target.with_name('a.pl.courts-pending').exists())
    def test_atomic_install_success(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);target=base/'data/server/quests/a.pl';target.parent.mkdir(parents=True)
            (base/'source.pl').write_bytes(b'new')
            m={'runtime':[dict(source='source.pl',target='quests/a.pl',sha256=r.digest(b'new'))]}
            with patch.object(r,'ROOT',base),patch.object(r,'STAGE',base),patch.object(r.os,'chown',create=True):r.install(m)
            self.assertEqual(target.read_bytes(),b'new');self.assertFalse(target.with_name('a.pl.courts-pending').exists())

if __name__=='__main__':unittest.main(verbosity=2)
