"""Exercise actual resume admission guards without remote access or mutations."""
import ast,copy,json,shutil,tempfile,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
source=Path(__file__).with_name('resume_oom.py').read_text();tree=ast.parse(source)
functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
class Reached(Exception):pass
class ResumeGuards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.original=self.root/'evidence';self.original.mkdir();(self.original/'01-aa-spells-attempted.json').write_text('{}')
  base={'id':'same','image_id':'same','started_at':'old','restarts':1,'health':'healthy','running':True,'oom_killed':False}
  self.p={'before':{'items':'same'},'services':{n:dict(base) for n in ['db','web','tunnel','game','gateway']}}
  self.now=copy.deepcopy(self.p['services']);self.now['db'].update(restarts=2,started_at='new');self.now['game']['running']=self.now['gateway']['running']=False
  self.op=Mock();self.op.load.side_effect=lambda p:self.p if p.name=='preflight.json' else {'owned':'same'} if p.name=='stopped-state.json' else ['market']
  self.op.checksums.return_value=self.p['before'];self.op.saved_state.return_value={'owned':'same'};self.op.b.market.return_value=['market'];self.op.ROOT=self.root
  self.r=Mock();self.r.compact.side_effect=lambda n:self.now[n];self.r.state.return_value={'State':{'ExitCode':0}}
  self.env=dict(op=self.op,r=self.r,ORIGINAL=self.original,RESUME=self.root/'resume',STAGE=self.root,Path=Path,shutil=shutil,time=Mock());exec(compile(functions,'resume_oom.py','exec'),self.env)
 def run_guard(self,error):
  with patch.object(shutil,'disk_usage',return_value=types.SimpleNamespace(free=3*1024**3)),patch.object(Path,'mkdir',side_effect=Reached),self.assertRaises(error):self.env['activate']()
  self.op.sql.assert_not_called();self.r.database_backup.assert_not_called()
 def test_verified_prewrite_restart_admitted(self):self.run_guard(Reached)
 def test_content_drift_rejected(self):self.op.checksums.return_value={'items':'changed'};self.run_guard(AssertionError)
 def test_owned_drift_rejected(self):self.op.saved_state.return_value={'owned':'changed'};self.run_guard(AssertionError)
 def test_market_drift_rejected(self):self.op.b.market.return_value=['changed'];self.run_guard(AssertionError)
 def test_extra_db_restart_rejected(self):self.now['db']['restarts']=3;self.run_guard(AssertionError)
 def test_db_replacement_rejected(self):self.now['db']['id']='new';self.run_guard(AssertionError)
 def test_running_game_rejected(self):self.now['game']['running']=True;self.run_guard(AssertionError)
 def test_committed_component_rejected(self):(self.original/'01-aa-spells-committed.json').write_text('{}');self.run_guard(AssertionError)
 def test_prior_access_rejected(self):(self.original/'opening.json').write_text('{}');self.run_guard(AssertionError)
 def test_prior_cache_generation_rejected(self):(self.original/'generated-caches.json').write_text('{}');self.run_guard(AssertionError)
 def test_unclean_stop_rejected(self):self.r.state.return_value={'State':{'ExitCode':137}};self.run_guard(AssertionError)
if __name__=='__main__':unittest.main()
