"""Exercise actual activation ordering, fail-closed boundaries and cache guards."""
import importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch

class Release(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  spec=importlib.util.spec_from_file_location('release',Path(__file__).with_name('rollout.py'))
  self.o=importlib.util.module_from_spec(spec)
  with patch.dict(sys.modules,{'fcntl':types.SimpleNamespace()}):spec.loader.exec_module(self.o)
  o=self.o;o.STAGE=Path(self.tmp.name);o.ROOT=o.STAGE;o.EVIDENCE=o.STAGE/'evidence';o.EVIDENCE.mkdir()
  (o.STAGE/'manifest.json').write_text('{}');(o.STAGE/'schema.sql').write_text('CREATE SCHEMA FIXTURE')
  (o.STAGE/'content.sql').write_text('INSTALL CONTENT FIXTURE')
  self.events=[];self.fail=None;self.held=False;self.enabled=0
  self.services={s:{'running':True} for s in ('game','gateway','db','web','tunnel')}
  self.m={'components':['schema.sql','content.sql'],'files':{'schema.sql':'s','content.sql':'c'},'binaries':{},'scripts':[]}
  self.p={'manifest_sha256':o.sha(o.STAGE/'manifest.json'),'services':self.services,'new_image_id':'candidate','after':{'items':'new'}}
  self.evidence={'preflight.json':self.p,'market-before.json':{}}
  self.real_compare=o.compare_cache
  o.manifest=lambda:self.m;o.script_guards=lambda m:self.event('script_guards')
  o.sha=lambda p:self.p['manifest_sha256'] if p.name=='manifest.json' else 'cache'
  o.shutil=types.SimpleNamespace(disk_usage=lambda p:types.SimpleNamespace(free=9*1024**3))
  o.time=types.SimpleNamespace(sleep=lambda _:None)
  o.contract=lambda:self.event('contract') or {'schema':45,'content':532}
  o.campaign=lambda v:self.event('campaign-'+str(v))
  o.records=lambda p:{1:'old'};o.compare_cache=lambda a,b:self.event('cache-compare') or {}
  o.cache_contract=lambda *args:self.event('cache-contract') or {}
  o.install_scripts=lambda m:self.event('install-scripts')
  o.prior=types.SimpleNamespace(startup_guards=lambda:self.event('startup-guards') or {})
  o.base=types.SimpleNamespace(load=lambda n:self.evidence[n],save=self.save,
   unchanged=lambda *args:self.event('unchanged'),saved_state=lambda:{'player':'preserved'},
   market=lambda:{},sql=self.sql,toggle=lambda a,b:self.event('dungeon-'+str(b)),PUBLIC={'items'},
   hashes=lambda t:{'items':'new'},boot_state=lambda data:data,health=lambda:self.event('health'),
   verify_market=lambda *args:{},hold=self.hold)
  o.r=types.SimpleNamespace(compact=lambda s:self.services[s],compose=self.compose,
   state=lambda s:{'State':{'Running':False,'ExitCode':0,'OOMKilled':False}},
   database_backup=lambda:self.event('backup') or {'verified':True},select=lambda image:self.event('select'),
   running=lambda *args:self.event('running') or {'started_at':'same'},closed_ports=lambda:None)
 def event(self,name):
  self.events.append(name)
  if name==self.fail:raise RuntimeError('injected '+name)
 def save(self,name,data):self.event('save-'+name);self.evidence[name]=data
 def hold(self):self.held=True;self.events.append('hold')
 def compose(self,*args):
  if args[0]=='stop':self.event('stop-'+args[-1])
  elif args[0]=='run':self.event('generate-cache')
  elif args[0]=='up':self.event('start-'+args[-1])
  else:raise AssertionError(args)
 def sql(self,q):
  if q.startswith('SELECT COUNT(*)'):return '0'
  if q.startswith('UPDATE nightcap_vigil_state'):self.event('enable-campaign');return '1'
  self.event('sql-'+q);return ''
 def test_success_order_and_closed_gateway(self):
  self.o.activate();self.assertFalse(self.held)
  stages=['stop-gateway','stop-game','backup','sql-CREATE SCHEMA FIXTURE','sql-INSTALL CONTENT FIXTURE',
   'contract','install-scripts','generate-cache','cache-contract','enable-campaign','start-game','save-verified-closed.json']
  indexes=[self.events.index(x) for x in stages];self.assertEqual(indexes,sorted(indexes))
  self.assertNotIn('start-gateway',self.events)
 def test_each_activation_failure_holds_without_restore_or_reopen(self):
  points=['stop-gateway','stop-game','backup','sql-CREATE SCHEMA FIXTURE','sql-INSTALL CONTENT FIXTURE',
   'contract','install-scripts','generate-cache','cache-contract','cache-compare','select',
   'enable-campaign','start-game','running','health','save-verified-closed.json']
  for point in points:
   with self.subTest(point=point):
    self.events=[];self.evidence={'preflight.json':self.p,'market-before.json':{}};self.held=False;self.fail=point
    with self.assertRaises(RuntimeError):self.o.activate()
    self.assertTrue(self.held);self.assertNotIn('start-gateway',self.events)
    self.assertFalse(any('restore' in e for e in self.events))
 def test_cache_rejects_modified_old_or_missing_new_items(self):
  before={1:'keep',990500:'helm'};after={**before,**{i:'new' for i in self.o.NEW_ITEMS}}
  self.assertEqual(self.real_compare(before,after)['existing_changed'],0)
  for case in ({**after,990500:'changed'},{k:v for k,v in after.items() if k!=961003},{**after,999999:'extra'}):
   with self.assertRaises(AssertionError):self.real_compare(before,case)
 def test_campaign_must_be_enabled_and_unenrolled_before_open(self):
  self.o.campaign=lambda v:(_ for _ in ()).throw(AssertionError('closed'))
  self.o.original_open=lambda:self.event('open')
  with self.assertRaises(AssertionError):self.o.open_access()
  self.assertNotIn('open',self.events)

 def test_resume_reconciles_only_authenticated_public_waypoint_checksum(self):
  spec=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('resume.py'))
  module=importlib.util.module_from_spec(spec)
  with patch.dict(sys.modules,{'fcntl':types.SimpleNamespace()}):spec.loader.exec_module(module)
  before={'nightcap_waypoints':'old','inventory':'keep','character_data':'keep','nightcap_dungeon_runs':'keep'}
  pre={'before':{'nightcap_waypoints':'old'},'after':{'nightcap_waypoints':'new'}}
  expected=module.expected_state(before,pre)
  self.assertEqual({k:v for k,v in expected.items() if k!='nightcap_waypoints'},
                   {k:v for k,v in before.items() if k!='nightcap_waypoints'})
  self.assertEqual(before['nightcap_waypoints'],'old')
  with self.assertRaises(AssertionError):module.expected_state({**before,'nightcap_waypoints':'unrelated'},pre)
  with self.assertRaises(AssertionError):module.expected_state(before,{'before':pre['before'],'after':pre['before']})
  stopped={'Running':False,'OOMKilled':False,'Error':'','ExitCode':0}
  module.stopped('game',stopped)
  module.stopped('gateway',{**stopped,'ExitCode':143})
  for service,state in [('game',{**stopped,'ExitCode':143}),('gateway',{**stopped,'OOMKilled':True,'ExitCode':143}),('game',{**stopped,'Running':True})]:
   with self.assertRaises(AssertionError):module.stopped(service,state)

if __name__=='__main__':unittest.main()
