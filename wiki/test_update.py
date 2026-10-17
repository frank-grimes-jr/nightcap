"""Use real temporary POSIX symlinks; all production I/O is patched out."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch
if sys.platform == 'win32':
    sys.modules['fcntl'] = types.SimpleNamespace()
import deploy
import update


@unittest.skipIf(os.name == 'nt', 'Atomic POSIX pointer tests run on Linux before publication')
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'data/public/wiki'
        self.old = '20261009-wiki-v2'
        self.new = '20261010-equipment'
        (self.root/'releases'/self.old).mkdir(parents=True)
        self.pointer = self.root/'current'
        self.pointer.symlink_to(Path('releases')/self.old)
        self.config = self.base/'nginx.conf'
        self.config.write_bytes(b'unchanged nginx')
        receipt = self.base/'website-history'/self.old
        receipt.mkdir(parents=True)
        self.old_manifest = {'index.html':deploy.sha(b'old')}
        (receipt/'manifest.json').write_text(json.dumps(self.old_manifest))
        self.manifest = {'index.html':deploy.sha(b'new')}
        manifest_file = self.base/'new.json'
        manifest_file.write_text(json.dumps(self.manifest))
        archive = self.base/'new.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            info = tarfile.TarInfo('index.html'); info.size = 3
            tar.addfile(info, io.BytesIO(b'new'))
        self.args = argparse.Namespace(release=self.new, expected_release=self.old, expected_config_sha=deploy.sha(self.config.read_bytes()), archive=archive, manifest=manifest_file)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(deploy, 'BASE', self.base))
        self.stack.enter_context(patch.object(deploy, 'services', return_value=list(range(5))))
        self.stack.enter_context(patch.object(deploy, 'protected', return_value={'/':(200,'unchanged')}))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def test_success_rehearses_old_new_old_new_and_preserves_config(self):
        seen = []
        with patch.object(deploy, 'verify', side_effect=lambda m:seen.append((self.pointer.readlink(),m))):
            update.main(self.args)
        self.assertEqual([str(target) for target, m in seen], ['releases/'+self.old,'releases/'+self.new,'releases/'+self.old,'releases/'+self.new])
        self.assertEqual(self.config.read_bytes(), b'unchanged nginx')
        self.assertEqual((self.pointer/'index.html').read_bytes(), b'new')

    def test_candidate_failure_restores_previous_pointer(self):
        def verify(manifest):
            if manifest == self.manifest: raise RuntimeError('bad candidate bytes')
        with patch.object(deploy, 'verify', side_effect=verify), self.assertRaisesRegex(RuntimeError, 'bad candidate'):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases')/self.old)

    def test_stale_config_and_pointer_abort_before_staging(self):
        self.args.expected_config_sha = '0'*64
        with self.assertRaisesRegex(ValueError, 'Web config changed'): update.main(self.args)
        self.args.expected_config_sha = deploy.sha(self.config.read_bytes())
        self.args.expected_release = '20261001-wrong'
        with self.assertRaisesRegex(RuntimeError, 'pointer changed'): update.main(self.args)
        self.assertFalse((self.root/'releases'/self.new).exists())

    def test_unrelated_concurrent_pointer_is_never_overwritten(self):
        def verify(manifest):
            if manifest == self.manifest:
                self.pointer.unlink()
                self.pointer.symlink_to('releases/other')
                raise RuntimeError('concurrent publisher')
        with patch.object(deploy,'verify',side_effect=verify), self.assertRaisesRegex(RuntimeError,'rollback needs attention'):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases/other'))

    def test_corrupt_archive_never_switches_live_pointer(self):
        self.args.manifest.write_text(json.dumps({'index.html':'0'*64}))
        with patch.object(deploy,'verify'), self.assertRaisesRegex(ValueError,'hash mismatch'):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases')/self.old)

    def test_private_state_change_fails_and_restores_old_pointer(self):
        with patch.object(deploy,'verify'), patch.object(deploy,'protected',side_effect=[{'/':(200,'unchanged')},{'/':(200,'changed')},{'/':(200,'unchanged')}]), self.assertRaisesRegex(RuntimeError,'Private downloads'):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases')/self.old)

    def test_config_drift_still_restores_owned_pointer_without_overwriting_config(self):
        def verify(manifest):
            if manifest == self.manifest:
                self.config.write_bytes(b'concurrent configuration')
                raise RuntimeError('candidate verification failed')
        with patch.object(deploy,'verify',side_effect=verify), self.assertRaisesRegex(RuntimeError,'rollback needs attention'):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases')/self.old)
        self.assertEqual(self.config.read_bytes(),b'concurrent configuration')

    def test_interrupt_just_after_atomic_replace_restores_actual_pointer(self):
        real_replace = os.replace
        calls = 0
        def replace_then_interrupt(source, target):
            nonlocal calls
            real_replace(source,target)
            calls += 1
            if calls == 1: raise KeyboardInterrupt('after atomic replace')
        with patch.object(deploy,'verify'), patch.object(os,'replace',side_effect=replace_then_interrupt), self.assertRaises(KeyboardInterrupt):
            update.main(self.args)
        self.assertEqual(self.pointer.readlink(),Path('releases')/self.old)


if __name__ == '__main__': unittest.main()
