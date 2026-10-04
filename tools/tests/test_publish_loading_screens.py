import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

if sys.platform == 'win32':
    sys.modules.setdefault('fcntl', types.SimpleNamespace())
spec = importlib.util.spec_from_file_location('gallery_publisher', Path(__file__).resolve().parents[1]/'publish_loading_screens.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublicationRecovery(unittest.TestCase):
    def fixture(self, root):
        stage, public = root/'stage', root/'public'
        stage.mkdir()
        public.mkdir()
        inventory, baseline = {}, {'public':{}, 'services':{}}
        for name in (*publisher.CHANNELS, 'nightcap-friends.zip', 'guide.html'):
            (public/name).write_bytes(('previous '+name).encode())
            baseline['public'][name] = {'sha256':publisher.sha(public/name)}
        for name in (*publisher.CHANNELS, publisher.GAME+'/resources/loadscreen.jpg', publisher.DESKTOP+'/nightcap-desktop.exe'):
            dest = stage/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(('candidate '+name).encode())
            inventory[name] = {'size':dest.stat().st_size, 'sha256':publisher.sha(dest)}
        return stage, public, inventory, baseline

    def test_interrupt_each_commit_and_resume_without_lowering_channels(self):
        for interruption in ('immutable', 'desktop', 'game', 'none'):
            with self.subTest(interruption=interruption), tempfile.TemporaryDirectory() as tmp:
                stage, public, entries, baseline = self.fixture(Path(tmp))
                real_copy = publisher.copy_verified
                interrupted = False
                order = []
                def copy(source,target,digest):
                    nonlocal interrupted
                    real_copy(source,target,digest)
                    point = ('desktop' if target == public/'launcher-channel.json' else
                             'game' if target == public/'channel.json' else 'immutable')
                    if point != 'immutable':
                        order.append(point)
                        self.assertTrue((public/publisher.GAME/'resources/loadscreen.jpg').is_file())
                        self.assertTrue((public/publisher.DESKTOP/'nightcap-desktop.exe').is_file())
                    if not interrupted and interruption == point:
                        interrupted = True
                        raise OSError('simulated interruption after write')
                with patch.object(publisher,'PUBLIC',public), patch.object(publisher,'sync'), patch.object(publisher,'copy_verified',copy):
                    if interruption != 'none':
                        with self.assertRaises(OSError): publisher.publish(stage,entries,baseline)
                    publisher.publish(stage,entries,baseline)
                    publisher.publish(stage,entries,baseline)  # idempotent recovery
                    self.assertEqual(order[0], 'desktop')
                    for name,entry in entries.items():
                        self.assertEqual(publisher.sha(public/name),entry['sha256'])
                    for name in publisher.CHANNELS:
                        self.assertEqual(publisher.sha(stage/('previous-'+name)),baseline['public'][name]['sha256'])
                    for name in ('nightcap-friends.zip','guide.html'):
                        self.assertEqual(publisher.sha(public/name),baseline['public'][name]['sha256'])

    def test_reject_public_drift_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage,public,entries,baseline = self.fixture(Path(tmp))
            (public/'channel.json').write_bytes(b'concurrent newer release')
            with patch.object(publisher,'PUBLIC',public), patch.object(publisher,'sync'):
                with self.assertRaises(AssertionError): publisher.publish(stage,entries,baseline)
            self.assertFalse((public/publisher.GAME).exists())

    def test_reuse_hosted_files_only_with_matching_signed_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage,public,entries,baseline = self.fixture(Path(tmp))
            prior = public/'release/2026100406/dinput8.dll'
            prior.parent.mkdir(parents=True)
            prior.write_bytes(b'already hosted')
            record = {'size':prior.stat().st_size,'sha256':publisher.sha(prior)}
            baseline['public']['channel.json']['signed'] = {
                'release':2026100406,'files':[{'path':'dinput8.dll',**record}]}
            with patch.object(publisher,'PUBLIC',public), patch.object(publisher,'sync'):
                path = publisher.source_file(stage,publisher.GAME+'/dinput8.dll',record,baseline)
                self.assertEqual(path,prior)
                entries[publisher.GAME+'/dinput8.dll'] = record
                publisher.publish(stage,entries,baseline)
                self.assertEqual((public/publisher.GAME/'dinput8.dll').read_bytes(),b'already hosted')
                with self.assertRaises(AssertionError):
                    publisher.source_file(stage,publisher.GAME+'/dinput8.dll',{'size':1,'sha256':'wrong'},baseline)


if __name__ == '__main__': unittest.main()
