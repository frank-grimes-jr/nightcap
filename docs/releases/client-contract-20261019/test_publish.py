import base64
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).with_name('publish.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stage, self.public = root / 'stage', root / 'public'
        self.stage.mkdir(); self.public.mkdir()
        (self.public / 'release/old').mkdir(parents=True)
        self.catalog, self.old = b'new catalog', b'old signed channel'
        retained = b'unchanged proxy'
        (self.public / 'release/old/dinput8.dll').write_bytes(retained)
        manifest = {'files': [
            {'path':'dinput8.dll','url':'https://play.nightcapgame.org/release/old/dinput8.dll','size':len(retained),'sha256':p.sha(retained)},
            {'path':'nightcap-patch-sites.json','size':len(self.catalog),'sha256':p.sha(self.catalog)}]}
        self.new = json.dumps({'manifest':base64.b64encode(json.dumps(manifest).encode()).decode()}).encode()
        for name, data in [('channel.json',self.new),('nightcap-patch-sites.json',self.catalog),('previous-channel.json',self.old)]:
            (self.stage / name).write_bytes(data)
        (self.public / 'channel.json').write_bytes(self.old)
        (self.public / 'launcher-channel.json').write_bytes(b'keep desktop')
        self.patches = patch.multiple(p, OLD=p.sha(self.old), NEW=p.sha(self.new), CATALOG=p.sha(self.catalog))
        self.patches.start(); self.addCleanup(self.patches.stop)
        if os.name == 'nt':
            sync = patch.object(p, 'sync_dir', lambda path: None)
            sync.start(); self.addCleanup(sync.stop)

    def run_publish(self, snapshot=lambda: {'game':'stable'}):
        return p.publish(self.stage, self.public, snapshot)

    def test_publish_and_repeat_preserve_assets_controls(self):
        self.run_publish(); self.run_publish()
        self.assertEqual((self.public / 'channel.json').read_bytes(),self.new)
        self.assertEqual((self.public / 'release/2026101901/nightcap-patch-sites.json').read_bytes(),self.catalog)
        self.assertEqual((self.public / 'launcher-channel.json').read_bytes(),b'keep desktop')

    def test_candidate_and_baseline_drift_fail_before_writes(self):
        for target in [self.stage/'channel.json',self.stage/'nightcap-patch-sites.json',self.public/'channel.json']:
            original=target.read_bytes(); target.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): self.run_publish()
            self.assertFalse((self.public/'release/2026101901').exists())
            target.write_bytes(original)

    def test_retained_asset_drift_keeps_old_channel(self):
        (self.public/'release/old/dinput8.dll').write_bytes(b'corrupt')
        with self.assertRaises(RuntimeError): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)

    def test_service_drift_keeps_old_channel(self):
        states=iter([{'game':'old'},{'game':'restarted'}])
        with self.assertRaisesRegex(RuntimeError,'Service drift'): self.run_publish(lambda: next(states))
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)

    def test_interrupted_channel_replace_recovers(self):
        original=p.os.replace
        def interrupt(source,target):
            if target == self.public/'channel.json': raise OSError('injected interruption')
            original(source,target)
        with patch.object(p.os,'replace',interrupt):
            with self.assertRaises(OSError): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)
        self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.new)

    def test_unknown_immutable_release_is_not_overwritten(self):
        release=self.public/'release/2026101901'; release.mkdir()
        (release/'nightcap-patch-sites.json').write_bytes(b'other')
        with self.assertRaisesRegex(RuntimeError,'Immutable release drift'): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)


if __name__ == '__main__': unittest.main()
