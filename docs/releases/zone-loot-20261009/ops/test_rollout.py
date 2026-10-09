"""Failure controls for the production controller, without SSH or live access."""
import importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *a:None))
sys.path.insert(0,str(Path(__file__).parent))
import rollout as app

class Scenario:
    def __init__(self,fault=None):
        self.fault=fault;self.game=True;self.gateway=True;self.image='old-id';self.selected='old-id';self.installed=False;self.dirty=False;self.saved={};self.events=[];self.gate=0
        self.m={'old_image_id':'old-id','new_image':'new','binaries':{'world':'new'}}
        self.p={'manifest_sha256':'manifest','new_image_id':'new-id','services':{'game':'game-before','gateway':'gateway-before'},'content':{'hash':'baseline'},'runtime':{},'backup':{},'old_hashes':{'bin/world':'old'}}
    def compose(self,*args):
        self.events.append(('compose',args));service=args[-1]
        if args[0]=='stop':
            if service=='game':self.game=False
            else:self.gateway=False
        elif service=='game':
            self.game=True;self.image='new-id' if self.selected=='new' else self.selected
            if self.image=='new-id':
                if self.fault=='start':raise RuntimeError('startup')
                if self.fault=='players':self.dirty=True
        else:
            self.gateway=True
            if self.fault=='gateway':raise RuntimeError('lost acknowledgement after gateway opened')
    def state(self,s):return {'State':{'Running':self.game if s=='game' else self.gateway,'ExitCode':0,'OOMKilled':False}}
    def player_data(self):return {'inventory':'changed' if self.dirty else 'same','character_advloot_claims':'same','zone_state_spawns':'same'}
    def select(self,image):self.selected=image;self.events.append(('select',image))
    def sql(self,q):
        self.events.append(('sql',q))
        if q=='INSTALL':
            if self.fault=='install':raise RuntimeError('install rolled back')
            self.installed=True
            if self.fault=='install-ack':raise RuntimeError('commit acknowledgement lost')
        elif q=='ACTIVATE':self.gate=1
        elif q=='DISABLE':self.gate=0
        elif q.startswith('DELIMITER'):
            self.installed=False;self.gate=0
        elif 'COUNT(*) FROM items WHERE' in q:return '448' if self.installed else '0'
        elif 'SELECT enabled' in q:return str(self.gate)
        return '0'
    def running(self,image,binaries):
        assert self.game and self.image==image
        if self.fault=='health' and image=='new-id':raise RuntimeError('health')
        return {'image_id':image,'started_at':image}
    def content(self):return {'hash':'changed' if self.fault=='content' and self.image=='new-id' else 'baseline'}
    def cache(self):
        if self.fault=='cache':raise RuntimeError('cache')
        return {'checked':448}
    def hashes(self,image):
        if image=='new-id':return {'bin/world':'bad' if self.fault=='image-drift' else 'new'}
        return self.p['old_hashes']
    def installed_check(self,enabled):assert self.installed and self.gate==enabled
    def sockets(self,installed):assert self.installed==installed
    def run(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp);(stage/'generated').mkdir()
            for name,value in [('install','INSTALL'),('activate','ACTIVATE'),('rollback','DISABLE')]:
                (stage/'generated'/f'{name}.sql').write_text(value)
            fields={'STAGE':stage,'manifest':lambda:self.m,'content':self.content,'socket_check':self.sockets,'installed_check':self.installed_check,'verify_cache':self.cache,'sql':self.sql,'item_ids':lambda:set(range(940000,940448)),'data':lambda n:[{'id':1,'socket':1,'before':{'augslot1type':'0','augslot1visible':'1'}}]}
            common={'sha':lambda p:'manifest','load':lambda n:self.p,'compact':lambda s:'drift' if self.fault=='preflight-drift' else s+'-before','untouched':lambda p:None,'closed_ports':lambda:None,'compose':self.compose,'state':self.state,'player_data':self.player_data,'save':lambda n,v:self.saved.__setitem__(n,v),'select':self.select,'running':self.running,'image_hashes':self.hashes,'verify_cache':lambda:True}
            with patch.multiple(app,**fields),patch.multiple(app.r,**common),patch.object(app.time,'sleep',lambda n:None):app.activate()

class Tests(unittest.TestCase):
    def test_image_build_rejects_tag_and_layer_drift(self):
        for fault in (None,'tag','layers'):
            events=[]
            def out(*args):
                if '--format' in args:return ('bad' if fault=='tag' else 'old-id') if args[-1]=='old-tag' else 'new-id'
                layers=['old'] if args[-1]=='old-id' else (['wrong','new'] if fault=='layers' else ['old','new'])
                return json.dumps([{'RootFS':{'Layers':layers}}])
            with patch.object(app.r,'out',out),patch.object(app.r,'call',lambda *a:events.append(a)):
                m={'old_image':'old-tag','old_image_id':'old-id','new_image':'new-tag'}
                if fault:
                    with self.assertRaises(AssertionError):app.build_image(m)
                else:self.assertEqual(app.build_image(m),'new-id')
            if fault=='tag':self.assertEqual(events,[])
    def test_success_preserves_then_opens(self):
        s=Scenario();s.run();self.assertTrue(s.gateway and s.installed);self.assertEqual(s.gate,1);self.assertIn('verified-closed.json',s.saved);self.assertIn('activated.json',s.saved)
    def test_preflight_drift_does_not_stop_or_write(self):
        s=Scenario('preflight-drift')
        with self.assertRaises(AssertionError):s.run()
        self.assertEqual(s.events,[])
    def test_image_drift_is_rejected_before_downtime(self):
        s=Scenario('image-drift')
        with self.assertRaises(AssertionError):s.run()
        self.assertEqual(s.events,[])
    def test_failed_install_returns_to_old_without_database_restore(self):
        s=Scenario('install')
        with self.assertRaises(RuntimeError):s.run()
        self.assertEqual(s.image,'old-id');self.assertTrue(s.gateway);self.assertFalse(s.saved['rolled-back.json']['database_restored'])
    def test_uncertain_install_commit_holds_closed(self):
        s=Scenario('install-ack')
        with self.assertRaises(Exception):s.run()
        self.assertFalse(s.gateway);self.assertTrue(s.installed);self.assertIn('held-closed.json',s.saved)
    def test_preopening_failure_reverses_only_unearned_initial_content(self):
        for fault in ('start','health','cache'):
            with self.subTest(fault=fault):
                s=Scenario(fault)
                with self.assertRaises(RuntimeError):s.run()
                self.assertFalse(s.installed);self.assertTrue(s.gateway);self.assertEqual(s.image,'old-id');self.assertTrue(s.saved['rolled-back.json']['initial_install_reversed'])
                inverse=[q for kind,q in s.events if kind=='sql' and q.startswith('DELIMITER')]
                self.assertEqual(len(inverse),1);self.assertNotIn('DELETE FROM inventory',inverse[0])
    def test_player_or_content_drift_prevents_inverse(self):
        for fault in ('players','content'):
            with self.subTest(fault=fault):
                s=Scenario(fault)
                with self.assertRaises(Exception):s.run()
                self.assertTrue(s.installed);self.assertFalse(s.gateway);self.assertIn('held-closed.json',s.saved)
                self.assertFalse(any(k=='sql' and q.startswith('DELIMITER') for k,q in s.events))
    def test_lost_gateway_ack_preserves_rewards_and_disables(self):
        s=Scenario('gateway')
        with self.assertRaises(Exception):s.run()
        self.assertTrue(s.installed);self.assertEqual(s.gate,0);self.assertFalse(s.gateway);self.assertIn('held-closed.json',s.saved)
        self.assertFalse(any(k=='sql' and q.startswith('DELIMITER') for k,q in s.events))

if __name__=='__main__':unittest.main()
