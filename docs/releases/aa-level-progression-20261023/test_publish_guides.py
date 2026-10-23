"""Offline generated-wrapper tests; no SSH, publisher, or production execution."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).with_name('publish_guides.py')
sha=lambda data:hashlib.sha256(data).hexdigest()

class GuideWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='aa-guide-wrapper-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.base=self.root/'production';self.base.mkdir()
        self.upload=self.root/'upload';self.upload.mkdir()
        self.stage=self.root/'stage'
        (self.base/'website-history').mkdir()
        guide=self.base/'data/public/player-site/current';guide.mkdir(parents=True)
        self.guide_files={'index.html':b'old guide','site-assets/site.css':b'css',
                          'site-assets/moon.svg':b'moon','site-assets/traders-at-dusk.png':b'traders',
                          'site-assets/master-of-three.png':b'three'}
        for name,data in self.guide_files.items():
            p=guide/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        (self.base/'nginx.conf').write_bytes(b'unchanged config')
        self.before={'wiki':'old-wiki','guide':'old-guide','config_sha256':sha(b'unchanged config'),
                     'guide_manifest':{n:sha(d) for n,d in self.guide_files.items()}}
        self.pointers={str(self.base/'data/public/wiki/current'):Path('releases/old-wiki'),
                       str(guide):Path('old-guide')}
        self.events=[]
        self.fcntl=types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2)
        self.lock=None;self.on_lock=None
        def flock(lock,flags):
            self.assertEqual(flags,3);self.lock=lock;self.events.append('lock')
            if self.on_lock:self.on_lock()
        self.fcntl.flock=flock
        def record(name):
            self.assertIsNotNone(self.lock);self.assertFalse(self.lock.closed)
            self.events.append(name)
        self.fcntl.record=record
        self.update=types.ModuleType('update')
        def update(args):
            record('wiki')
            self.assertEqual(args.expected_release,'old-wiki')
            self.assertEqual(args.expected_config_sha,self.before['config_sha256'])
            print(json.dumps({'result':'PASS'}))
        self.update.main=update
        (self.upload/'player-site-deploy.py').write_text(
            "import fcntl,json,sys\ndef main():\n fcntl.record('guide-'+sys.argv[1])\n print(json.dumps({'result':sys.argv[1]}))\n",encoding='utf-8')
        self.pins={'player-site-deploy.py':sha((self.upload/'player-site-deploy.py').read_bytes())}

    def generated(self):
        tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
        assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign)
                        and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets))
        env={'upload':'/home/ubuntu/aa-level-guides-20261023','pins':self.pins,
             'before':self.before,'wiki':Path('wiki.tar.gz'),'guide':Path('guide.tar.gz'),
             'RELEASE':'20261023-aa-level-v1'}
        return eval(compile(ast.Expression(assignment.value),str(SOURCE),'eval'),env)

    def execute_generated(self):
        source=self.generated()
        # Compile the exact emitted script before replacing only its Path import
        # with a local filesystem adapter. Publisher entrypoints are test fakes.
        compile(source,'exact emitted remote source','exec')
        tree=ast.parse(source)
        tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='pathlib')]
        pointers=self.pointers
        class LocalPath(type(Path())):
            def readlink(self):
                if str(self) in pointers:return pointers[str(self)]
                return super().readlink()
        mapping={'/opt/nightcap/deploy/production':self.base,
                 '/opt/nightcap/releases/aa-level-guides-20261023':self.stage,
                 '/home/ubuntu/aa-level-guides-20261023':self.upload}
        def local_path(value):return LocalPath(mapping.get(str(value),value))
        original_argv=sys.argv[:];original_path=sys.path[:]
        try:
            with patch.dict(sys.modules,{'fcntl':self.fcntl,'update':self.update}),contextlib.redirect_stdout(io.StringIO()):
                exec(compile(tree,'isolated generated remote source','exec'),{'Path':local_path})
        finally:
            sys.argv[:]=original_argv;sys.path[:]=original_path

    def test_exact_generated_source_compiles_and_calls_publishers_under_one_lock(self):
        self.execute_generated()
        self.assertEqual(self.events,['lock','wiki','guide-stage','guide-activate'])
        self.assertTrue(self.lock.closed)
        report=json.loads((self.stage/'published.json').read_text())
        self.assertTrue(report['config_unchanged'])
        self.assertEqual(report['guide']['result'],'activate')

    def test_wiki_pointer_drift_at_lock_acquisition_blocks_both_publishers(self):
        self.on_lock=lambda:self.pointers.update({str(self.base/'data/public/wiki/current'):Path('releases/newer')})
        with self.assertRaises(AssertionError):self.execute_generated()
        self.assertEqual(self.events,['lock'])

    def test_guide_pointer_drift_at_lock_acquisition_blocks_both_publishers(self):
        self.on_lock=lambda:self.pointers.update({str(self.base/'data/public/player-site/current'):Path('newer')})
        with self.assertRaises(AssertionError):self.execute_generated()
        self.assertEqual(self.events,['lock'])

    def test_guide_hash_drift_at_lock_acquisition_blocks_both_publishers(self):
        self.on_lock=lambda:(self.base/'data/public/player-site/current/site-assets/site.css').write_bytes(b'newer')
        with self.assertRaises(AssertionError):self.execute_generated()
        self.assertEqual(self.events,['lock'])

    def test_config_drift_at_lock_acquisition_blocks_both_publishers(self):
        self.on_lock=lambda:(self.base/'nginx.conf').write_bytes(b'newer')
        with self.assertRaises(AssertionError):self.execute_generated()
        self.assertEqual(self.events,['lock'])

    def test_contended_lock_never_calls_publishers(self):
        def held(*args):raise BlockingIOError('existing publisher')
        self.fcntl.flock=held
        with self.assertRaises(BlockingIOError):self.execute_generated()
        self.assertEqual(self.events,[])

if __name__=='__main__':unittest.main()
