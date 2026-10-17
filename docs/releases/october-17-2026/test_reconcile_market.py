import importlib.util,os,sys,types,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
if os.name=='nt':sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=2,LOCK_NB=4))
sys.path.insert(0,str(Path(__file__).parent));import reconcile_market as r
class Reconciliation(unittest.TestCase):
 def test_only_two_market_tables_may_differ(self):
  old={'nightcap_market_state':'a','nightcap_market_offers':'b','timers':'c'};new={**old,'nightcap_market_state':'x','nightcap_market_offers':'y'};r.validate_change(old,new)
  for bad in [{**new,'timers':'z'},{**new,'new':'z'},old]:
   with self.assertRaises(AssertionError):r.validate_change(old,bad)
 def test_exact_single_boot_epoch_and_policy(self):
  before=['1','1','79','0','4','2.500000','2026-10-17 14:42:51'];after=[*before[:2],'80',*before[3:6],'2026-10-17 17:58:06'];start='2026-10-17T17:57:51.372601517Z';r.validate_state(before,after,start)
  for index,value in [(2,'81'),(1,'0'),(3,'1'),(4,'5'),(5,'3.000000'),(6,'2026-10-17 17:57:50'),(6,'2026-10-17 18:00:00')]:
   bad=after.copy();bad[index]=value
   with self.assertRaises(AssertionError):r.validate_state(before,bad,start)
 def test_unknown_hold_cannot_reopen(self):
  resolution={'held_receipts':{'known':'x'},'operator_sha256':'x'}
  with patch.object(r,'paired',return_value=({},{})),patch.object(r.op,'load',return_value=resolution),patch.object(r,'holds',return_value={'unknown':'x'}),patch.object(r.op,'r',types.SimpleNamespace()) as native:
   with self.assertRaises(AssertionError):r.open_access()
 def test_failure_before_or_after_open_holds_access(self):
  for point in ['preserve','publish','open','after']:
   with tempfile.TemporaryDirectory() as t:
    events=[];a={'game':{},'runtime':{'started_at':'now'},'cache':{},'player_tables_preserved':47,'custom_tables_preserved':14};resolution={'held_receipts':{},'operator_sha256':'x','data':{}}
    def fail(label):
     if point==label:raise RuntimeError(label)
    def compose(*args):events.append('open');fail('open')
    native=types.SimpleNamespace(compact=lambda s:{},compose=compose,state=lambda s:{'State':{'Running':True}},closed_ports=lambda:None,running=lambda *args:fail('after') or {'started_at':'now'})
    with patch.object(r,'paired',return_value=({'new_image_id':'new'},{'started_at':'now'})),patch.object(r.op,'load',side_effect=lambda n:a if n=='activated-closed.json' else resolution),patch.object(r,'holds',return_value={}),patch.object(r.op,'sha',return_value='x'),patch.object(r.op,'EVIDENCE',Path(t)),patch.object(r.op,'r',native),patch.object(r.op,'preserved',side_effect=lambda d:fail('preserve')),patch.object(r.op,'untouched',side_effect=lambda *a:fail('publish')),patch.object(r.op,'save'),patch.object(r.op,'manifest',return_value={'client_channel_sha256':'new'}),patch.object(r.op,'health'),patch.object(r.op,'binaries',return_value={}),patch.object(r.op,'hold',side_effect=lambda why:events.append('hold')):
     with self.assertRaises(RuntimeError):r.open_access()
     self.assertEqual(events[-1],'hold')
     if point in ('preserve','publish'):self.assertNotIn('open',events)
if __name__=='__main__':unittest.main(verbosity=2)
