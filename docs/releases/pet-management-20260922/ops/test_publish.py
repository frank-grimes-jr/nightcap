import importlib.util,json,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).with_name('publish-client.py');spec=importlib.util.spec_from_file_location('pub',p);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class PublisherTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
  self.stage=root/'stage';self.public=root/'public';self.stage.mkdir();self.public.mkdir()
  self.activation=root/'activated.json';self.activation.write_text(json.dumps({'native_processes':15,'restart_count':0,'errors':{}}))
  self.live_guard=patch.object(r,'live_server');self.live=self.live_guard.start();self.addCleanup(self.live_guard.stop)
  guard=patch.object(r.subprocess,'check_output',side_effect=AssertionError('Live Docker forbidden'));guard.start();self.addCleanup(guard.stop)
  for name,value in [('STAGE',self.stage),('PUBLIC',self.public),('ACTIVATION',self.activation)]:
   p=patch.object(r,name,value);p.start();self.addCleanup(p.stop)
  self.old={}
  for name in r.OLD:
   f=self.public/name;f.write_bytes(('old-'+name).encode());self.old[name]=r.sha(f)
  p=patch.object(r,'OLD',self.old);p.start();self.addCleanup(p.stop)
  files={};rows=[]
  for i in range(23):
   name='nested/f'+str(i);f=self.stage/r.RELEASE/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(('new-'+name).encode());files[r.RELEASE+'/'+name]={'size':f.stat().st_size,'sha256':r.sha(f)};rows.append({'path':name})
  f=self.stage/'channel.json';f.write_bytes(b'new-channel');files['channel.json']={'size':f.stat().st_size,'sha256':r.sha(f)}
  (self.stage/'publication-files.json').write_text(json.dumps(files));(self.stage/'release-audit.json').write_text(json.dumps({'files':rows,'channel_sha256':r.sha(f)}))
 def old_channel(self):self.assertEqual(r.sha(self.public/'channel.json'),self.old['channel.json'])
 def test_success_and_replay(self):
  r.publish();r.publish();self.assertEqual((self.public/'channel.json').read_bytes(),b'new-channel')
  self.assertEqual(r.sha(self.stage/'previous-channel.json'),self.old['channel.json'])
  for n,h in self.old.items():
   if n!='channel.json':self.assertEqual(r.sha(self.public/n),h)
 def test_missing_activation(self):
  self.activation.unlink()
  with self.assertRaises(FileNotFoundError):r.publish()
  self.old_channel()
 def test_unhealthy_activation(self):
  self.activation.write_text(json.dumps({'native_processes':14,'restart_count':0,'errors':{}}))
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_archive_corruption(self):
  (self.stage/r.RELEASE/'nested/f0').write_bytes(b'corrupt')
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_public_drift(self):
  (self.public/'guide.html').write_bytes(b'changed')
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_wrong_existing_immutable(self):
  path=self.public/r.RELEASE/'unrelated';path.parent.mkdir(parents=True);path.write_text('unrelated')
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_asset_interruption_replays(self):
  orig=r.copy_verified;count=0
  def interrupted(*args):
   nonlocal count
   count+=1
   if count==4:raise OSError('disk')
   return orig(*args)
  with patch.object(r,'copy_verified',interrupted):
   with self.assertRaises(OSError):r.publish()
  self.old_channel();r.publish();self.assertEqual((self.public/'channel.json').read_bytes(),b'new-channel')
 def test_pointer_failure_and_resume(self):
  orig=r.copy_verified
  def interrupted(source,target,digest):
   if target==self.public/'channel.json':raise OSError('channel replace')
   return orig(source,target,digest)
  with patch.object(r,'copy_verified',interrupted):
   with self.assertRaises(OSError):r.publish()
  self.old_channel();self.assertTrue((self.public/r.RELEASE/'nested/f22').exists());r.publish()
 def test_after_pointer_commit_replays(self):
  orig=r.copy_verified
  def interrupted(source,target,digest):
   result=orig(source,target,digest)
   if target==self.public/'channel.json':raise OSError('lost completion')
   return result
  with patch.object(r,'copy_verified',interrupted):
   with self.assertRaises(OSError):r.publish()
  self.assertEqual((self.public/'channel.json').read_bytes(),b'new-channel');r.publish()
 def test_changed_backup_rejected(self):
  (self.stage/'previous-channel.json').write_bytes(b'wrong')
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_server_rolled_back_before_publication(self):
  self.live.side_effect=AssertionError('matching image no longer running')
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel();self.assertFalse((self.public/r.RELEASE).exists())
 def test_server_crashes_while_assets_are_copying(self):
  self.live.side_effect=[None,AssertionError('server unhealthy')]
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel();self.assertTrue((self.public/r.RELEASE).exists())
 def test_public_drift_during_copy_never_replaces_channel(self):
  original=r.copy_verified;changed=False
  def drift(*args):
   nonlocal changed
   result=original(*args)
   if not changed:(self.public/'guide.html').write_bytes(b'concurrent change');changed=True
   return result
  with patch.object(r,'copy_verified',drift):
   with self.assertRaises(AssertionError):r.publish()
  self.old_channel()
 def test_parent_path_rejected_before_public_writes(self):
  files=json.loads((self.stage/'publication-files.json').read_text());audit=json.loads((self.stage/'release-audit.json').read_text())
  old=r.RELEASE+'/nested/f0';bad=r.RELEASE+'/../../escape';entry=files.pop(old);files[bad]=entry;audit['files'][0]['path']='../../escape'
  (self.stage/'publication-files.json').write_text(json.dumps(files));(self.stage/'release-audit.json').write_text(json.dumps(audit))
  with self.assertRaises(AssertionError):r.publish()
  self.old_channel();self.assertFalse((self.public/'escape').exists())
 def test_live_server_rejects_current_drift(self):
  self.live_guard.stop()
  activation={'image_id':'new-id','started_at':'validated-start'}
  def responses(game,gateway):return ['game-id',json.dumps([game]),'gateway-id',json.dumps([gateway])]
  good={'Image':'new-id','RestartCount':0,'State':{'Running':True,'OOMKilled':False,'Health':{'Status':'healthy'},'StartedAt':'validated-start'}}
  gateway={'State':{'Running':True}}
  with patch.object(r.subprocess,'check_output',side_effect=responses(good,gateway)):r.live_server(activation)
  variants=[]
  for key,value in [('Image','old-id'),('RestartCount',1)]:
   changed=json.loads(json.dumps(good));changed[key]=value;variants.append((changed,gateway))
  for key,value in [('Running',False),('OOMKilled',True),('Health',{'Status':'unhealthy'}),('StartedAt','later-start')]:
   changed=json.loads(json.dumps(good));changed['State'][key]=value;variants.append((changed,gateway))
  variants.append((good,{'State':{'Running':False}}))
  for game,gate in variants:
   with self.subTest(game=game,gateway=gate),patch.object(r.subprocess,'check_output',side_effect=responses(game,gate)):
    with self.assertRaises(AssertionError):r.live_server(activation)
if __name__=='__main__':unittest.main()
