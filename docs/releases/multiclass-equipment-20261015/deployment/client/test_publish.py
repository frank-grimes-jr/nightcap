"""Focused publisher recovery tests. No remote calls; temporary filesystem only."""
import contextlib,copy,hashlib,importlib.util,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
sys.dont_write_bytecode = True
from unittest.mock import patch
if os.name=='nt':sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=2,LOCK_NB=4,flock=lambda *args:None))
source=Path(__file__).parent/"stage/publish.py"
spec=importlib.util.spec_from_file_location('publisher',source);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PublisherTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);root=Path(t.name)
  self.stage=root/'stage';self.public=root/'deploy/production/data/public';self.stage.mkdir();self.public.mkdir(parents=True)
  for name,value in [('STAGE',self.stage),('PUBLIC',self.public)]:
   guard=patch.object(p,name,value);guard.start();self.addCleanup(guard.stop)
  if os.name=='nt':
   guard=patch.object(p,'sync_directory');guard.start();self.addCleanup(guard.stop)
  self.old={n:('old-'+n).encode() for n in ('channel.json','launcher-channel.json','nightcap-friends.zip','guide.html')}
  for n,b in self.old.items():(self.public/n).write_bytes(b)
  self.baseline={'public':{n:{'sha256':hashlib.sha256(b).hexdigest()} for n,b in self.old.items()},'services':{}}
  self.baseline['public']['channel.json']['signed']={'release':2026100407}
  for s in ('db','game','gateway','web','tunnel'):
   self.baseline['services'][s]={'id':s+'-id','image_id':s+'-image','started_at':'original','restarts':0,'running':True,'health':'healthy' if s in ('game','db') else None,'oom_killed':False}
  self.live=copy.deepcopy(self.baseline['services']);self.commands=[]
  guard=patch.object(p.subprocess,'check_output',side_effect=self.docker_read);guard.start();self.addCleanup(guard.stop)
  self.entries={};rows=[]
  for i in range(106):
   name=f'nested/asset-{i:02d}';f=self.stage/p.RELEASE/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(('new-'+name).encode())
   row={'size':f.stat().st_size,'sha256':p.sha(f)};self.entries[p.RELEASE+'/'+name]=row;rows.append({'path':name,**row})
  (self.stage/'channel.json').write_bytes(b'new-channel');self.entries['channel.json']={'size':11,'sha256':p.sha(self.stage/'channel.json')}
  self.audit={'release':2026101501,'files':rows,'channel_sha256':self.entries['channel.json']['sha256']};self.save_inventory()
 def save_inventory(self):
  (self.stage/'publication-files.json').write_text(json.dumps(self.entries));(self.stage/'release-audit.json').write_text(json.dumps(self.audit))
 def docker_read(self,command,**kwargs):
  self.commands.append(command);self.assertEqual(kwargs['timeout'],30)
  if command[:4]==['docker','compose','ps','-q']:
   self.assertEqual(len(command),5);self.assertEqual(kwargs['cwd'],self.public.parent.parent);return self.live[command[-1]]['id']+'\n'
  self.assertEqual(command[:2],['docker','inspect']);self.assertEqual(len(command),3)
  x=next(v for v in self.live.values() if v['id']==command[2])
  return json.dumps([{'Image':x['image_id'],'RestartCount':x['restarts'],'State':{'StartedAt':x['started_at'],'Running':x['running'],'OOMKilled':x['oom_killed'],'Health':{'Status':x['health']}}}])
 def publish(self):
  with contextlib.redirect_stdout(io.StringIO()):p.publish(p.inventory(),self.baseline)
 def old_channel(self):self.assertEqual((self.public/'channel.json').read_bytes(),self.old['channel.json'])
 def complete(self):
  for name,entry in self.entries.items():self.assertEqual(p.sha(self.public/name),entry['sha256'])
  self.assertEqual((self.stage/'previous-channel.json').read_bytes(),self.old['channel.json'])
  for name,data in self.old.items():
   if name!='channel.json':self.assertEqual((self.public/name).read_bytes(),data)
  self.assertEqual(self.live,self.baseline['services']);self.assertTrue(self.commands)
 def test_channel_last_and_idempotent_replay(self):
  original=p.os.replace;events=[]
  def observe(src,dst):
   self.old_channel()
   if dst==self.public/'channel.json':
    for name,entry in self.entries.items():
     if name!='channel.json':self.assertEqual(p.sha(self.public/name),entry['sha256'])
    self.assertEqual((self.stage/'previous-channel.json').read_bytes(),self.old['channel.json']);events.append('channel')
   else:events.append('asset')
   return original(src,dst)
  with patch.object(p.os,'replace',observe):self.publish()
  self.assertEqual(events,['asset']*106+['channel']);self.complete();self.publish();self.complete()
 def test_public_baseline_drift_refused_before_writes(self):
  for name in self.old:
   with self.subTest(name=name):
    (self.public/name).write_bytes(b'drift')
    with self.assertRaisesRegex(AssertionError,'Public drift'):self.publish()
    self.assertFalse((self.stage/'previous-channel.json').exists());self.assertFalse((self.public/p.RELEASE).exists());(self.public/name).write_bytes(self.old[name])
 def test_nested_directories_synced_before_release_rename(self):
  old=self.stage/p.RELEASE/'nested/asset-00';new=self.stage/p.RELEASE/'uifiles/default/skin/asset-00'
  new.parent.mkdir(parents=True);old.rename(new)
  self.entries[p.RELEASE+'/uifiles/default/skin/asset-00']=self.entries.pop(p.RELEASE+'/nested/asset-00')
  self.audit['files'][0]['path']='uifiles/default/skin/asset-00';self.save_inventory()
  pending=(self.public/p.RELEASE).with_name('.2026101501.incident-pending')
  events=[];original=p.os.rename
  def rename(src,dst):
   expected=[pending/'uifiles/default/skin',pending/'uifiles/default',pending/'uifiles',pending]
   indices=[max(i for i,path in enumerate(events) if path==d) for d in expected]
   self.assertEqual(indices,sorted(indices));self.old_channel();return original(src,dst)
  with patch.object(p,'sync_directory',side_effect=events.append),patch.object(p.os,'rename',side_effect=rename):self.publish()
  self.complete()
 def test_service_baseline_drift_refused_before_writes(self):
  for key,value in [('id','new-id'),('image_id','new-image'),('started_at','new-start'),('restarts',1),('running',False),('health','unhealthy'),('oom_killed',True)]:
   with self.subTest(field=key):
    self.live['game'][key]=value
    with self.assertRaisesRegex(AssertionError,'Service drift'):self.publish()
    self.old_channel();self.assertFalse((self.public/p.RELEASE).exists());self.live=copy.deepcopy(self.baseline['services'])
 def test_corrupt_staged_asset_refused(self):
  (self.stage/p.RELEASE/'nested/asset-00').write_bytes(b'corrupt')
  with self.assertRaises(AssertionError):self.publish()
  self.old_channel();self.assertFalse((self.public/p.RELEASE).exists())
 def test_path_escape_refused(self):
  self.entries[p.RELEASE+'/../../escape']=self.entries.pop(p.RELEASE+'/nested/asset-00');self.audit['files'][0]['path']='../../escape';self.save_inventory()
  with self.assertRaises(AssertionError):self.publish()
  self.old_channel();self.assertFalse((self.public/p.RELEASE).exists())
 def test_partial_copy_resumes(self):
  original=p.shutil.copyfile;count=0
  def interrupt(src,dst):
   nonlocal count
   count+=1
   if count==23:Path(dst).write_bytes(b'partial');raise OSError('copy interrupted')
   return original(src,dst)
  with patch.object(p.shutil,'copyfile',interrupt):
   with self.assertRaises(OSError):self.publish()
  self.old_channel();self.publish();self.complete()
 def test_after_release_rename_resumes(self):
  original=p.os.rename
  def interrupt(src,dst):original(src,dst);raise OSError('after rename')
  with patch.object(p.os,'rename',interrupt):
   with self.assertRaises(OSError):self.publish()
  self.old_channel();self.assertTrue((self.public/p.RELEASE).is_dir());self.publish();self.complete()
 def test_before_channel_replace_resumes(self):
  original=p.os.replace
  def interrupt(src,dst):
   if dst==self.public/'channel.json':raise OSError('before channel')
   return original(src,dst)
  with patch.object(p.os,'replace',interrupt):
   with self.assertRaises(OSError):self.publish()
  self.old_channel();self.publish();self.complete()
 def test_after_channel_replace_resumes(self):
  original=p.os.replace
  def interrupt(src,dst):
   original(src,dst)
   if dst==self.public/'channel.json':raise OSError('after channel')
  with patch.object(p.os,'replace',interrupt):
   with self.assertRaises(OSError):self.publish()
  self.assertEqual((self.public/'channel.json').read_bytes(),b'new-channel');self.publish();self.complete()
 def test_corrupt_backup_retained_and_refused(self):
  backup=self.stage/'previous-channel.json';backup.write_bytes(b'corrupt-backup')
  with self.assertRaises(AssertionError):self.publish()
  self.assertEqual(backup.read_bytes(),b'corrupt-backup');self.old_channel();self.assertFalse((self.public/p.RELEASE).exists())
 def test_corrupt_existing_immutable_release_retained_and_refused(self):
  original=p.copy_verified
  def interrupt(src,dst,digest):
   if dst==self.public/'channel.json':raise OSError('before channel')
   return original(src,dst,digest)
  with patch.object(p,'copy_verified',interrupt):
   with self.assertRaises(OSError):self.publish()
  f=self.public/p.RELEASE/'nested/asset-00';f.write_bytes(b'corrupt-immutable')
  with self.assertRaises(AssertionError):self.publish()
  self.assertEqual(f.read_bytes(),b'corrupt-immutable');self.old_channel();self.assertEqual((self.stage/'previous-channel.json').read_bytes(),self.old['channel.json'])
 def test_drift_during_copy_refuses_channel_switch(self):
  original=p.copy_verified
  def concurrent_change(*args):
   result=original(*args);(self.public/'guide.html').write_bytes(b'concurrent-guide');return result
  with patch.object(p,'copy_verified',concurrent_change):
   with self.assertRaisesRegex(AssertionError,'Public drift'):self.publish()
  self.old_channel();self.assertEqual((self.public/'guide.html').read_bytes(),b'concurrent-guide')

if __name__=='__main__':
 out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PublisherTests));print(out.getvalue())
 Path(__file__).with_name('publisher-test-results.txt').write_text(out.getvalue()+'\nWindows fcntl/directory-fsync stubs; actual copy/rename/replace; Docker is fake and strictly read-only.\nPublisher SHA256 '+hashlib.sha256(source.read_bytes()).hexdigest()+'\n')
 sys.exit(not result.wasSuccessful())
