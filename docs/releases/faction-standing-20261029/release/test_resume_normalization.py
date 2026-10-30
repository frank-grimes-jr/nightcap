import copy,unittest
from resume_normalization import reconcile,dispatch,original_preflight_read
from unittest.mock import Mock
from pathlib import Path

class NormalizationTests(unittest.TestCase):
 def setUp(self):
  self.before={'content':{'zone':'old','items':'same'},'services':{'game':'original'},'commands':[['faction',80,'']]}
  self.proof={'before':'old','after':'new','public':{'exact_preflight_checksum_reproduced':True,'fields':['map_file_name','content_flags','content_flags_disabled']}}
 def test_only_zone_checksum_changes(self):
  original=copy.deepcopy(self.before);result=reconcile(self.before,{'zone':'new','items':'same'},self.proof)
  self.assertEqual(self.before,original);self.assertEqual(result,{**original,'content':{'zone':'new','items':'same'}})
 def test_other_content_drift_rejected(self):
  for current in ({'zone':'new','items':'changed'},{'zone':'other','items':'same'},{'zone':'new','items':'same','extra':'value'}):
   with self.assertRaises(AssertionError):reconcile(self.before,current,self.proof)
 def test_wrong_proof_or_no_change_rejected(self):
  for key,value in [('before','wrong'),('after','old')]:
   p=copy.deepcopy(self.proof);p[key]=value
   with self.assertRaises(AssertionError):reconcile(self.before,{'zone':'new','items':'same'},p)
 def test_failed_or_expanded_scope_proof_rejected(self):
  for key,value in [('exact_preflight_checksum_reproduced',False),('fields',['map_file_name','safe_x'])]:
   p=copy.deepcopy(self.proof);p['public'][key]=value
   with self.assertRaises(AssertionError):reconcile(self.before,{'zone':'new','items':'same'},p)

class RecoveryRoutingTests(unittest.TestCase):
 def test_each_route_uses_correct_recovery_flag(self):
  for action,method,args in [('activate','transition',()),('open','open_access',()),('rollback','transition',(True,)),('open-rollback','open_access',(True,))]:
   op=Mock();dispatch(op,action);getattr(op,method).assert_called_once_with(*args)
 def test_preflight_substitution_preserves_all_other_reads(self):
  import resume_normalization as m
  op=Mock();original=op.read;read=original_preflight_read(op)
  read(m.STAGE/'evidence/preflight.json');original.assert_called_with(m.STAGE/'evidence/preflight-resumed.json')
  read(m.STAGE/'evidence/recovery/verified-closed.json');original.assert_called_with(m.STAGE/'evidence/recovery/verified-closed.json')

if __name__=='__main__':unittest.main(verbosity=2)
