"""Fault-inject the actual operator; no Docker, network or production writes."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/tests')]
from test_unrest_waypoint_content import fixture


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.stage=Path(self.tmp.name);(self.stage/'evidence').mkdir()
        self.before=fixture();self.current=copy.deepcopy(self.before)
        self.players={'inventory':'100'};self.states='outside';self.events=[]
        self.gateway=True;self.game=True;self.sql_targets={};self.fail_sql=False
        self.market={'state':dict(id=1,enabled=1,epoch=10,expansion=0,loot_multiplier=4,buy_cost_mod='2.500000',rotated_at='old'),'offers_checksum':'123'}
        self.p={'manifest_sha256':'hash','services':{'game':{'id':'game'},'gateway':{'id':'gateway'}}}
        r=types.ModuleType('runtime_ops');r.ROOT=self.stage
        r.sql=self.sql;r.compact=lambda name:self.p['services'][name]
        r.compose=lambda *args:self.close();r.database_backup=lambda:{'path':str(self.stage/'private.sql.gz')}
        spec=importlib.util.spec_from_file_location('unrest_operator',Path(__file__).with_name('rollout.py'))
        self.op=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':types.ModuleType('fcntl'),'runtime_ops':r}):spec.loader.exec_module(self.op)
        self.op.STAGE=self.stage;r.EVIDENCE=self.stage/'evidence'
        (self.stage/'reviewed-before.json').write_text(json.dumps(self.before))
        self.op.save('preflight.json',self.p)
        patches={
            'manifest':lambda:{'source_commit':'reviewed'},'sha':lambda path:'hash',
            'guard':lambda p:None,'stop':self.stop,'start_game':self.start,
            'open_gateway':self.open,'restore_rehearsal':lambda *args:None,
            'preservation':lambda:copy.deepcopy(self.players),'outside_states':lambda:self.states,
            'market':lambda query=None:copy.deepcopy(self.market),
        }
        for name,value in patches.items():
            handle=patch.object(self.op,name,value);handle.start();self.addCleanup(handle.stop)
        for name,value in {'capture':lambda query:copy.deepcopy(self.current),'patch_sql':self.patch_sql}.items():
            handle=patch.object(self.op.content,name,value);handle.start();self.addCleanup(handle.stop)
    def close(self):self.gateway=False;self.events.append('close')
    def stop(self):self.close();self.game=False;self.events.append('stop')
    def open(self,p):self.gateway=True;self.events.append('open')
    def start(self,p):
        self.game=True;self.events.append('start');self.market['state']['epoch']+=1
        self.market['state']['rotated_at']='new';return {'started_at':'new'}
    def patch_sql(self,before,after):
        token='sql-'+str(len(self.sql_targets));self.sql_targets[token]=copy.deepcopy(after);return token
    def sql(self,query):
        if query in self.sql_targets:
            self.current=copy.deepcopy(self.sql_targets[query]);self.events.append('sql')
            if self.fail_sql:self.fail_sql=False;raise RuntimeError('Lost acknowledgment after commit')
            return ''
        if query.startswith('SELECT COUNT(*)'):return '0'
        if query.startswith('SELECT id,y+0e0'):return '1\t3.750000238418579\t-141\t4\t0\n'
        raise AssertionError('Unexpected query')
    def assert_original(self):
        for table in self.op.content.KEYS:
            if table!='zone_state_spawns':self.assertEqual(self.current['rows'][table],self.before['rows'][table])
    def test_success_opens_only_after_verified_receipt(self):
        self.op.activate();self.assertTrue(self.gateway)
        self.assertTrue((self.stage/'evidence/verified-closed.json').exists())
        self.assertEqual(self.events,['close','stop','sql','start','open'])
        self.assertEqual(self.players,{'inventory':'100'})
    def test_preflight_content_drift_never_stops(self):
        self.current['rows']['spawn2'][0]['x']='99999'
        with self.assertRaisesRegex(AssertionError,'Content drift'):self.op.activate()
        self.assertEqual(self.events,[])
    def test_stopped_content_drift_holds_closed_without_baseline(self):
        def drift():self.stop();self.current['rows']['spawn2'][0]['x']='99999'
        with patch.object(self.op,'stop',drift):
            with self.assertRaisesRegex(AssertionError,'No verified recovery baseline'):self.op.activate()
        self.assertFalse(self.gateway);self.assertNotIn('start',self.events)
    def test_rehearsal_failure_recovers_without_live_sql(self):
        with patch.object(self.op,'restore_rehearsal',side_effect=RuntimeError('restore failed')):
            with self.assertRaisesRegex(RuntimeError,'restore failed'):self.op.activate()
        self.assertTrue(self.gateway);self.assertNotIn('sql',self.events);self.assert_original()
    def test_uncertain_commit_is_detected_and_scoped_back(self):
        self.fail_sql=True
        with self.assertRaisesRegex(RuntimeError,'Lost acknowledgment'):self.op.activate()
        self.assert_original();self.assertTrue(self.gateway);self.assertEqual(self.events.count('sql'),2)
    def test_persistent_player_drift_holds_closed(self):
        def drift(p):result=self.start(p);self.players['inventory']='200';return result
        with patch.object(self.op,'start_game',drift):
            with self.assertRaisesRegex(AssertionError,'Persistent data drift'):self.op.activate()
        self.assertFalse(self.gateway);self.assert_original()
    def test_unrelated_saved_state_drift_holds_closed(self):
        def drift(p):
            result=self.start(p);self.current['rows']['zone_state_spawns'][0]['is_corpse']='1';return result
        with patch.object(self.op,'start_game',drift):
            with self.assertRaisesRegex(AssertionError,'saved-state drift'):self.op.activate()
        self.assertFalse(self.gateway)
    def test_possible_access_preserves_fresh_players_and_corpse(self):
        calls=0
        def uncertain_open(p):
            nonlocal calls
            calls+=1;self.open(p)
            if calls==1:
                self.players['inventory']='300'
                corpse=dict(self.current['rows']['zone_state_spawns'][0],id='9000000',is_corpse='1')
                self.current['rows']['zone_state_spawns'].append(corpse)
                raise RuntimeError('Gateway acknowledgment lost')
        with patch.object(self.op,'open_gateway',uncertain_open):
            with self.assertRaisesRegex(RuntimeError,'Gateway acknowledgment'):self.op.activate()
        self.assert_original();self.assertTrue(self.gateway);self.assertEqual(self.players['inventory'],'300')
        self.assertTrue(any(row['id']=='9000000' for row in self.current['rows']['zone_state_spawns']))
    def test_recovery_open_failure_closes_again(self):
        def fail(p):self.open(p);raise RuntimeError('gateway check failed')
        with patch.object(self.op,'open_gateway',fail):
            with self.assertRaisesRegex(RuntimeError,'gateway check failed'):self.op.activate()
        self.assertFalse(self.gateway);self.assertEqual(self.events[-1],'close')
    def test_recovery_receipt_failure_closes_again(self):
        original=self.op.save
        def save(name,value):
            if name=='recovered.json':raise OSError('disk full')
            return original(name,value)
        with patch.object(self.op,'save',save),patch.object(self.op,'restore_rehearsal',side_effect=RuntimeError('restore failed')):
            with self.assertRaisesRegex(OSError,'disk full'):self.op.activate()
        self.assertFalse(self.gateway)
    def test_market_policy_drift_holds_closed(self):
        def drift(p):result=self.start(p);self.market['state']['enabled']=0;return result
        with patch.object(self.op,'start_game',drift):
            with self.assertRaisesRegex(AssertionError,'Market policy drift'):self.op.activate()
        self.assertFalse(self.gateway)
    def test_market_exact_guard_rejects_sql_side_effects(self):
        def sql(query):result=self.sql(query);self.market['offers_checksum']='456';return result
        with patch.object(self.op.r,'sql',sql):
            with self.assertRaises(AssertionError):self.op.activate()
        self.assertNotIn('start',self.events);self.assertFalse(self.gateway)
    def test_backup_sidecar_keeps_round_trip_precision_and_rejects_bad_fields(self):
        sql=self.op.precise_character_positions()
        self.assertIn('`y`=3.750000238418579',sql)
        self.assertTrue(sql.startswith('START TRANSACTION;'))
        for malformed in ('1\tNaN\t0\t0\t0','1\t0;DELETE FROM inventory\t0\t0\t0','bad\t0\t0\t0\t0'):
            with self.assertRaises(AssertionError):self.op.precise_character_positions(lambda query:malformed)

if __name__=='__main__':unittest.main()
