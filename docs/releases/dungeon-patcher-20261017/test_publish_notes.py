import base64, copy, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('notes',Path(__file__).with_name('publish-notes.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class NotesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.public=root/'public';self.public.mkdir();self.stage=root/'stage';self.stage.mkdir()
        self.state={n:dict(running=True,oom_killed=False,health='healthy',image_id='unchanged') for n in ('db','game','gateway','web','tunnel')}
        files=[]
        for i in range(106):
            name='asset'+str(i);b=name.encode();(self.public/name).write_bytes(b)
            files.append(dict(path=name,url='https://play.nightcapgame.org/'+name,size=len(b),sha256=hashlib.sha256(b).hexdigest()))
        self.old=dict(release=2026101501,files=files,patch_notes=[dict(release=2026101501)],tombstones=[],minimum_launcher='0.6.0')
        self.new=copy.deepcopy(self.old);self.new['release']=2026101701;self.new['patch_notes'].insert(0,dict(release=2026101701))
        for name in ('channel.json','launcher-channel.json','nightcap-friends.zip','guide.html'):(self.public/name).write_bytes(b'old public')
        baseline={'public':{n:{'sha256':p.sha(self.public/n)} for n in ('channel.json','launcher-channel.json','nightcap-friends.zip','guide.html')},'services':self.state}
        baseline['public']['channel.json']['signed']=self.old
        (self.stage/'baseline.json').write_text(json.dumps(baseline));self.write_candidate()
        for mock in (patch.object(p,'PUBLIC',self.public),patch.object(p,'services',return_value=self.state),patch.object(p,'sync_directory')):
            mock.start();self.addCleanup(mock.stop)
    def write_candidate(self):
        (self.stage/'channel.json').write_text(json.dumps({'manifest':base64.b64encode(json.dumps(self.new).encode()).decode()}))
        (self.stage/'signed-receipt.json').write_text(json.dumps({'channel_sha256':p.sha(self.stage/'channel.json')}))
    def test_valid_publication_and_resume_preserve_assets(self):
        before={x.name:p.sha(x) for x in self.public.iterdir() if x.name!='channel.json'}
        p.publish(self.stage);p.publish(self.stage)
        self.assertEqual(before,{x.name:p.sha(x) for x in self.public.iterdir() if x.name!='channel.json'})
        self.assertEqual((self.stage/'previous-channel.json').read_bytes(),b'old public')
    def test_asset_drift_rejected_before_channel_write(self):
        (self.public/'asset0').write_bytes(b'drift')
        with self.assertRaises(AssertionError):p.publish(self.stage)
        self.assertEqual((self.public/'channel.json').read_bytes(),b'old public')
    def test_history_loss_rejected(self):
        self.new['patch_notes'].pop();self.write_candidate()
        with self.assertRaises(AssertionError):p.validate(self.stage)
    def test_changed_asset_url_rejected(self):
        self.new['files'][0]['url']='https://play.nightcapgame.org/replaced';self.write_candidate()
        with self.assertRaises(AssertionError):p.validate(self.stage)
    def test_unsigned_staged_channel_change_rejected(self):
        (self.stage/'channel.json').write_bytes(b'changed')
        with self.assertRaises(AssertionError):p.validate(self.stage)
    def test_service_drift_rejected(self):
        changed=copy.deepcopy(self.state);changed['game']['image_id']='other'
        with patch.object(p,'services',return_value=changed),self.assertRaises(AssertionError):p.validate(self.stage)
    def test_incomplete_baseline_rejected(self):
        baseline=json.loads((self.stage/'baseline.json').read_text());del baseline['public']['guide.html']
        (self.stage/'baseline.json').write_text(json.dumps(baseline))
        with self.assertRaisesRegex(AssertionError,'Incomplete public baseline'):p.validate(self.stage)

if __name__=='__main__':unittest.main()
