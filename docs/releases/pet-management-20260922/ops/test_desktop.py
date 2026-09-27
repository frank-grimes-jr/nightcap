"""Desktop publication fault tests use isolated temporary directories only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('desktop_publish', Path(__file__).with_name('publish-desktop.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class DesktopPublisherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='desktop-publication-test-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.stage, self.public = root / 'stage', root / 'public'
        self.stage.mkdir()
        self.public.mkdir()
        self.old = {}
        for name in release.OLD:
            file = self.public / name
            file.write_bytes(('old-' + name).encode())
            self.old[name] = release.sha(file)
        self.exe_name = release.REL + '/nightcap-desktop.exe'
        self.files = {}
        for name, content in [('launcher-channel.json', b'new-signed-launcher-channel'),
                              (self.exe_name, b'exact-new-desktop-executable')]:
            file = self.stage / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
            self.files[name] = {'size': file.stat().st_size, 'sha256': release.sha(file)}
        (self.stage / 'publication-files.json').write_text(json.dumps(self.files))
        for name, value in [('STAGE', self.stage), ('PUBLIC', self.public), ('OLD', self.old)]:
            guard = patch.object(release, name, value)
            guard.start()
            self.addCleanup(guard.stop)
        # Any future accidental external operation must abort in this suite.
        for name in ('run', 'Popen', 'check_output'):
            guard = patch.object(subprocess, name, side_effect=AssertionError('real subprocess forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def assert_old_channel(self):
        self.assertEqual(release.sha(self.public / 'launcher-channel.json'), self.old['launcher-channel.json'])

    def assert_backup(self):
        self.assertEqual(release.sha(self.stage / 'previous-launcher-channel.json'), self.old['launcher-channel.json'])

    def assert_published(self):
        for name, entry in self.files.items():
            self.assertEqual(release.sha(self.public / name), entry['sha256'])
        self.assert_backup()
        for name, digest in self.old.items():
            if name != 'launcher-channel.json':
                self.assertEqual(release.sha(self.public / name), digest)

    def test_success_and_replay_preserve_pet_channel_starter_guide_and_original_backup(self):
        release.publish()
        self.assert_published()
        release.publish()
        self.assert_published()

    def test_staged_corruption_is_rejected_before_public_changes(self):
        (self.stage / self.exe_name).write_bytes(b'corrupt')
        with self.assertRaises(AssertionError):
            release.publish()
        self.assert_old_channel()
        self.assertFalse((self.public / release.REL).exists())
        self.assertFalse((self.stage / 'previous-launcher-channel.json').exists())

    def test_inventory_requires_exact_paths_and_sizes(self):
        variants = []
        missing = dict(self.files)
        missing.pop(self.exe_name)
        variants.append(missing)
        extra = dict(self.files)
        extra['../outside.exe'] = self.files[self.exe_name]
        variants.append(extra)
        wrong_size = json.loads(json.dumps(self.files))
        wrong_size[self.exe_name]['size'] += 1
        variants.append(wrong_size)
        for files in variants:
            with self.subTest(files=files):
                (self.stage / 'publication-files.json').write_text(json.dumps(files))
                with self.assertRaises(AssertionError):
                    release.publish()
                self.assert_old_channel()
                self.assertFalse((self.public / release.REL).exists())

    def test_any_pinned_public_drift_is_rejected_without_overwriting_it(self):
        for name in self.old:
            with self.subTest(name=name):
                original = (self.public / name).read_bytes()
                (self.public / name).write_bytes(b'external-drift')
                before = {str(p.relative_to(self.public)): p.read_bytes() for p in self.public.rglob('*') if p.is_file()}
                with self.assertRaises(AssertionError):
                    release.publish()
                after = {str(p.relative_to(self.public)): p.read_bytes() for p in self.public.rglob('*') if p.is_file()}
                self.assertEqual(after, before)
                (self.public / name).write_bytes(original)

    def test_existing_immutable_mismatch_is_rejected_without_overwrite(self):
        target = self.public / self.exe_name
        target.parent.mkdir(parents=True)
        target.write_bytes(b'wrong-existing-executable')
        with self.assertRaises(AssertionError):
            release.publish()
        self.assert_old_channel()
        self.assertEqual(target.read_bytes(), b'wrong-existing-executable')
        self.assert_backup()

    def test_existing_immutable_extra_file_is_rejected(self):
        target = self.public / self.exe_name
        target.parent.mkdir(parents=True)
        target.write_bytes((self.stage / self.exe_name).read_bytes())
        (target.parent / 'unexpected.exe').write_bytes(b'unexpected')
        with self.assertRaises(AssertionError):
            release.publish()
        self.assert_old_channel()

    def test_changed_private_backup_is_never_replaced(self):
        backup = self.stage / 'previous-launcher-channel.json'
        backup.write_bytes(b'wrong-backup')
        with self.assertRaises(AssertionError):
            release.publish()
        self.assert_old_channel()
        self.assertEqual(backup.read_bytes(), b'wrong-backup')

    def test_partial_executable_copy_keeps_old_pointer_and_resumes(self):
        original = release.shutil.copyfile
        def interrupted(source, target):
            if Path(source) == self.stage / self.exe_name:
                Path(target).write_bytes(b'partial')
                raise OSError('injected interrupted executable copy')
            return original(source, target)
        with patch.object(release.shutil, 'copyfile', side_effect=interrupted):
            with self.assertRaises(OSError):
                release.publish()
        self.assert_old_channel()
        self.assert_backup()
        self.assertFalse((self.public / release.REL).exists())
        release.publish()
        self.assert_published()

    def test_immutable_directory_rename_failure_keeps_old_pointer_and_resumes(self):
        original = release.os.replace
        def interrupted(source, target):
            if Path(target) == self.public / release.REL:
                raise OSError('injected immutable directory rename failure')
            return original(source, target)
        with patch.object(release.os, 'replace', side_effect=interrupted):
            with self.assertRaises(OSError):
                release.publish()
        self.assert_old_channel()
        self.assert_backup()
        self.assertFalse((self.public / release.REL).exists())
        release.publish()
        self.assert_published()

    def test_metadata_rename_failure_retains_complete_executable_and_old_pointer(self):
        original = release.os.replace
        def interrupted(source, target):
            if Path(target) == self.public / 'launcher-channel.json':
                raise OSError('injected pointer rename failure')
            return original(source, target)
        with patch.object(release.os, 'replace', side_effect=interrupted):
            with self.assertRaises(OSError):
                release.publish()
        self.assert_old_channel()
        self.assert_backup()
        self.assertEqual(release.sha(self.public / self.exe_name), self.files[self.exe_name]['sha256'])
        release.publish()
        self.assert_published()

    def test_lost_response_after_pointer_commit_replays_without_losing_backup(self):
        original = release.os.replace
        def interrupted(source, target):
            result = original(source, target)
            if Path(target) == self.public / 'launcher-channel.json':
                raise OSError('injected lost response after commit')
            return result
        with patch.object(release.os, 'replace', side_effect=interrupted):
            with self.assertRaises(OSError):
                release.publish()
        self.assert_published()
        release.publish()
        self.assert_published()

    def test_metadata_is_never_exposed_before_exact_executable(self):
        original = release.os.replace
        flips = []
        def ordered(source, target):
            if Path(target) == self.public / 'launcher-channel.json':
                flips.append(True)
                executable = self.public / self.exe_name
                self.assertEqual(release.sha(executable), self.files[self.exe_name]['sha256'])
                self.assertEqual(executable.stat().st_size, self.files[self.exe_name]['size'])
                self.assert_old_channel()
                self.assert_backup()
            return original(source, target)
        with patch.object(release.os, 'replace', side_effect=ordered):
            release.publish()
        self.assertEqual(flips, [True])
        self.assert_published()

    def test_public_drift_during_asset_copy_prevents_pointer_flip(self):
        original = release.copy_verified
        def drift(source, target, digest):
            result = original(source, target, digest)
            if Path(source) == self.stage / self.exe_name:
                (self.public / 'channel.json').write_bytes(b'concurrent-pet-channel-change')
            return result
        with patch.object(release, 'copy_verified', side_effect=drift):
            with self.assertRaises(AssertionError):
                release.publish()
        self.assert_old_channel()
        self.assert_backup()
        self.assertEqual((self.public / 'channel.json').read_bytes(), b'concurrent-pet-channel-change')


if __name__ == '__main__':
    unittest.main(verbosity=2)
