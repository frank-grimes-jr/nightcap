"""Fault injection for five-binary and cache rollout. No SSH, Docker or database access."""
import importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *a:None))
spec=importlib.util.spec_from_file_location('rollout',Path(__file__).with_name('rollout.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class Scenario:
    def __init__(self,fault=None):
        self.fault=fault;self.events=[];self.game_on=self.gateway_on=True;self.image='old-id';self.selected='old-id';self.saved={};self.dirty=False;self.failed=False;self.ports_changed=False;self.rule=fault=='rule-drift';self.rule_deleted=False
        self.m={'old_image_id':'old-id','old_hashes':{'bin/world':'old'},'new_image':'new','binaries':{'world':'new'},'client_channel_sha256':'channel','client_release':203}
        self.p={'manifest_sha256':'manifest','services':{'game':'game-before','gateway':'gateway-before'},'new_image_id':'new-id','public':{'channel.json':'channel'},'runtime':{},'backup':{'verified':True}}
    def compose(self,*args):
        self.events.append(args);service=args[-1]
        if args[0]=='stop':
            if service=='gateway':self.gateway_on=False
            else:self.game_on=False
        elif service=='game':
            self.game_on=True;self.image='new-id' if self.selected=='new' else self.selected
            if self.fault=='start' and self.image=='new-id':raise RuntimeError('Injected start failure')
            if self.fault=='data' and self.image=='new-id':self.dirty=True
        else:
            self.gateway_on=True
            if self.fault=='ports':self.ports_changed=True
            if self.fault=='gateway' and not self.failed:self.failed=True;raise RuntimeError('Injected gateway start failure')
    def state(self,s):return {'State':{'Running':self.game_on if s=='game' else self.gateway_on,'ExitCode':0,'OOMKilled':False}}
    def select(self,image):self.selected=image
    def running(self,image,binaries):
        assert self.game_on and self.image==image
        if self.fault=='health' and image=='new-id':raise RuntimeError('Injected health failure')
        return {'image_id':image,'started_at':image}
    def data(self):return {'inventory':'changed' if self.dirty else 'same','zone_state_spawns':'saved','character_advloot_claims':'receipts'}
    def sql(self,q):
        if q.startswith('INSERT'):
            if self.fault=='insert':raise RuntimeError('Injected insert failure')
            assert not self.rule;self.rule=True
        elif q.startswith('DELETE'):
            assert "ruleset_id=1" in q and "rule_value='true'" in q
            self.rule=False;self.rule_deleted=True
        return ''
    def content(self):
        if self.fault=='content':raise RuntimeError('Injected checksum capture failure')
        return {'items':'same'}
    def cache(self):
        if self.fault=='cache':raise RuntimeError('Injected cache mismatch')
        return {'items_checked':300000}
    def closed_ports(self):
        if self.ports_changed:raise RuntimeError('Injected host port exposure after gateway recreation')
    def run(self):
        replacements={'manifest':lambda:self.m,'load':lambda n:self.saved[n] if n in self.saved else self.p,'sha':lambda p:'manifest','compact':lambda s:s+'-before','closed_ports':self.closed_ports,'untouched':lambda p:None,'out':lambda *a:'new-id','compose':self.compose,'state':self.state,'player_data':self.data,'select':self.select,'running':self.running,'save':lambda n,v:self.saved.__setitem__(n,v),'image_hashes':lambda i:self.m['old_hashes'],'content_data':self.content,'policy_rows':lambda:['1\ttrue'] if self.rule else [],'verify_cache':self.cache,'old_cache_valid':lambda:True,'sql':self.sql}
        with patch.multiple(r,**replacements),patch.object(r.time,'sleep',lambda n:None):r.activate()

class RolloutTests(unittest.TestCase):
    def test_prior_restart_must_be_explicit_and_new_runtime_still_requires_zero(self):
        i={'Id':'container','Image':'id','RestartCount':1,'State':{'Running':True,'Health':{'Status':'healthy'},'StartedAt':'now'}}
        binaries={n:n for n in ('world','zone','ucs','loginserver')}
        rows=[['zone','zone']]*12+[[n,n] for n in ('world','ucs','loginserver')]
        def out(*args):return r.json.dumps(rows) if args[0:2]==('docker','exec') else ''
        with patch.object(r,'state',lambda s:i),patch.object(r,'out',out):
            with self.assertRaises(AssertionError):r.running('id',binaries)
            self.assertEqual(r.running('id',binaries,expected_restarts=1)['restart_count'],1)
            i['RestartCount']=2
            with self.assertRaises(AssertionError):r.running('id',binaries,expected_restarts=1)
    def test_recreated_gateway_with_host_ports_is_held_closed(self):
        s=Scenario('ports')
        with self.assertRaises(RuntimeError):s.run()
        self.assertFalse(s.gateway_on);self.assertIn('held-closed.json',s.saved)
        self.assertNotIn('activated.json',s.saved);self.assertNotIn('rolled-back.json',s.saved)
    def test_channel_drift_rejected_before_stopping_services(self):
        s=Scenario();s.p['public']['channel.json']='changed'
        with self.assertRaises(AssertionError):s.run()
        self.assertTrue(s.game_on and s.gateway_on);self.assertEqual(s.events,[])
    def test_rule_drift_rejected_without_services_or_sql_changes(self):
        s=Scenario('rule-drift')
        with self.assertRaises(AssertionError):s.run()
        self.assertTrue(s.rule and s.game_on and s.gateway_on)
        self.assertFalse(s.rule_deleted);self.assertEqual(s.events,[])
    def test_insert_failure_never_deletes_unowned_rule(self):
        s=Scenario('insert')
        with self.assertRaises(RuntimeError):s.run()
        self.assertFalse(s.rule_deleted);self.assertTrue(s.gateway_on)
    def test_success_preserves_data_before_open(self):
        s=Scenario();s.run();self.assertTrue(s.gateway_on);self.assertEqual(s.image,'new-id');self.assertIn('verified-closed.json',s.saved);self.assertFalse(s.saved['activated.json']['database_restored'])
    def test_start_health_and_gateway_failures_restore_receipt_aware_image(self):
        for fault in ('start','health','gateway','cache','insert','content'):
            with self.subTest(fault=fault):
                s=Scenario(fault)
                with self.assertRaises(Exception):s.run()
                self.assertEqual(s.image,'old-id');self.assertTrue(s.gateway_on);self.assertFalse(s.saved['rolled-back.json']['database_restored'])
    def test_data_drift_stays_closed_and_does_not_restore_database(self):
        s=Scenario('data')
        with self.assertRaises(Exception):s.run()
        self.assertFalse(s.gateway_on);self.assertTrue(s.dirty);self.assertIn('held-closed.json',s.saved);self.assertNotIn('rolled-back.json',s.saved)
    def test_saved_corpse_state_in_actual_fingerprint(self):
        names=['inventory','character_advloot_claims','character_advloot_filters','character_advloot_settings','zone_state_spawns'];queries=[]
        def sql(q):
            queries.append(q)
            return '\n'.join(names) if 'information_schema' in q else '2\tb\n1\ta\n'
        with patch.object(r,'sql',sql):result=r.player_data()
        self.assertIn('zone_state_spawns',queries[0]);self.assertEqual(set(result),set(names));self.assertEqual(result['zone_state_spawns']['rows'],2)

if __name__=='__main__':unittest.main()
