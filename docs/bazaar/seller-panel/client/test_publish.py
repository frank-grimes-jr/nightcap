import base64
import copy
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


def envelope(manifest):
    return json.dumps({'manifest': base64.b64encode(json.dumps(manifest).encode()).decode()}).encode()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.stage, self.public = Path(temp.name)/'stage', Path(temp.name)/'public'
        self.stage.mkdir(); self.public.mkdir()
        (self.public/'release/old').mkdir(parents=True)
        self.assets = {'dinput8.dll': b'new proxy', 'nightcap-patch-sites.json': b'new catalog', 'nightcap-patches.cfg': b'new config', 'uifiles/nightcap/equi_bazaarsearchwnd.xml': b'new XML'}
        files = []
        for name in ['global_chr.s3d', 'global4_chr.s3d', *[n for n in self.assets if n not in p.ADDED]]:
            data = ('old '+name).encode()
            (self.public/'release/old'/name).write_bytes(data)
            files.append({'path':name, 'url':'https://play.nightcapgame.org/release/old/'+name, 'size':len(data), 'sha256':p.sha(data), 'required':True})
        old = {'release':p.PREVIOUS, 'expires':'old', 'patch_notes':[{'release':p.PREVIOUS}], 'files':files, 'policy':'preserved'}
        new = copy.deepcopy(old)
        new.update(release=p.RELEASE, expires='new', patch_notes=[{'release':p.RELEASE}, *old['patch_notes']])
        for f in new['files']:
            if f['path'] in self.assets:
                data = self.assets[f['path']]
                f.update(sha256=p.sha(data), size=len(data), url=f"https://play.nightcapgame.org/release/{p.RELEASE}/"+f['path'])
        for name in sorted(p.ADDED):
            data=self.assets[name]
            new['files'].append({'path':name,'required':True,'size':len(data),'sha256':p.sha(data),'url':f'https://play.nightcapgame.org/release/{p.RELEASE}/'+name})
        self.old, self.new = envelope(old), envelope(new)
        for name, data in {'channel.json':self.new, 'previous-channel.json':self.old, **self.assets}.items():
            (self.stage/name).parent.mkdir(parents=True,exist_ok=True)
            (self.stage/name).write_bytes(data)
        (self.public/'channel.json').write_bytes(self.old)
        (self.public/'launcher-channel.json').write_bytes(b'keep desktop')
        self.release = self.public/'release'/str(p.RELEASE)
        patched = patch.multiple(p, OLD=p.sha(self.old), NEW=p.sha(self.new), PINS={k:p.sha(v) for k,v in self.assets.items()})
        patched.start(); self.addCleanup(patched.stop)
        if os.name == 'nt':
            sync = patch.object(p, 'sync_dir', lambda path: None)
            sync.start(); self.addCleanup(sync.stop)

    def run_publish(self, snapshot=lambda: {'game':'stable'}):
        return p.publish(self.stage, self.public, snapshot)

    def test_publish_repeat_and_preservation(self):
        self.run_publish(); self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(), self.new)
        for name, data in self.assets.items(): self.assertEqual((self.release/name).read_bytes(), data)
        self.assertEqual((self.public/'launcher-channel.json').read_bytes(), b'keep desktop')

    def test_candidate_and_baseline_drift_fail_before_writes(self):
        for target in [self.stage/'channel.json', self.stage/'previous-channel.json', self.public/'channel.json', *[self.stage/n for n in self.assets]]:
            original=target.read_bytes(); target.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): self.run_publish()
            self.assertFalse(self.release.exists())
            target.write_bytes(original)

    def test_retained_asset_drift_keeps_old_channel(self):
        (self.public/'release/old/global_chr.s3d').write_bytes(b'corrupt')
        with self.assertRaises(RuntimeError): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(), self.old)

    def test_service_drift_keeps_old_channel(self):
        states=iter([{'game':'old'}, {'game':'restarted'}])
        with self.assertRaisesRegex(RuntimeError, 'Service drift'): self.run_publish(lambda: next(states))
        self.assertFalse(self.release.exists())

    def test_interrupted_writes_recover_without_partial_channel(self):
        for target in [self.release/'nightcap-patch-sites.json', self.release/'uifiles/nightcap/equi_bazaarsearchwnd.xml', self.public/'channel.json']:
            if target != self.public/'channel.json' and target.exists():target.unlink()
            original=p.os.replace
            def interrupt(source, destination):
                if destination == target: raise OSError('injected interruption')
                original(source, destination)
            with patch.object(p.os, 'replace', interrupt):
                with self.assertRaises(OSError): self.run_publish()
            self.assertEqual((self.public/'channel.json').read_bytes(), self.old)
            self.run_publish()
            self.assertEqual((self.public/'channel.json').read_bytes(), self.new)
            (self.public/'channel.json').write_bytes(self.old)

    def test_immutable_drift_rejected_before_other_archive_write(self):
        self.release.mkdir()
        (self.release/'nightcap-patch-sites.json').write_bytes(b'foreign')
        with self.assertRaisesRegex(RuntimeError, 'Immutable release drift'): self.run_publish()
        self.assertFalse((self.release/'dinput8.dll').exists())

    def test_interrupted_channel_write_recovers_valid_prefix_only(self):
        partial = self.public/('channel.json'+p.PARTIAL)
        for data in [b'', self.new[:len(self.new)//3]]:
            partial.write_bytes(data)
            self.run_publish()
            self.assertEqual((self.public/'channel.json').read_bytes(), self.new)
            (self.public/'channel.json').write_bytes(self.old)
        partial.write_bytes(b'foreign content')
        with self.assertRaisesRegex(RuntimeError, 'Partial channel drift'): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(), self.old)

    def test_interrupted_archive_write_recovers_valid_prefix_only(self):
        self.release.mkdir()
        partial = self.release/('dinput8.dll'+p.PARTIAL)
        partial.write_bytes(b'foreign content')
        with self.assertRaisesRegex(RuntimeError, 'Partial archive drift'): self.run_publish()
        partial.write_bytes(self.assets['dinput8.dll'][:3])
        self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(), self.new)

    def test_missing_new_asset_and_foreign_inventory_are_rejected(self):
        original=json.loads(base64.b64decode(json.loads(self.new)['manifest']))
        mutations=[]
        missing=copy.deepcopy(original);missing['files']=[f for f in missing['files'] if f['path']!='nightcap-patch-sites.json'];mutations.append(missing)
        extra=copy.deepcopy(original);extra['files'].append({**extra['files'][0],'path':'foreign.eqg'});mutations.append(extra)
        duplicate=copy.deepcopy(original);duplicate['files'].append(duplicate['files'][0]);mutations.append(duplicate)
        history=copy.deepcopy(original);history['patch_notes']=history['patch_notes'][:1];mutations.append(history)
        for manifest in mutations:
            altered=envelope(manifest);(self.stage/'channel.json').write_bytes(altered)
            with patch.object(p,'NEW',p.sha(altered)):
                with self.assertRaises(RuntimeError):self.run_publish()
            self.assertEqual((self.public/'channel.json').read_bytes(),self.old)
            self.assertFalse(self.release.exists())

    def test_public_control_drift_keeps_old_channel(self):
        calls=0
        def snapshot():
            nonlocal calls
            calls+=1
            if calls == 2: (self.public/'launcher-channel.json').write_bytes(b'concurrent update')
            return {'game':'stable'}
        with self.assertRaisesRegex(RuntimeError, 'Public control drift'): self.run_publish(snapshot)
        self.assertEqual((self.public/'channel.json').read_bytes(), self.old)

    @unittest.skipUnless(os.name == 'posix', 'POSIX mode bits and umask')
    def test_private_umask_creates_publicly_traversable_release_and_readable_files(self):
        previous=os.umask(0o077)
        try:
            self.run_publish()
        finally:
            os.umask(previous)
        self.assertEqual(self.release.stat().st_mode & 0o777,0o755)
        for name,data in self.assets.items():
            path=self.release/name
            self.assertEqual(path.stat().st_mode & 0o777,0o644)
            self.assertEqual(path.read_bytes(),data)
        self.assertEqual((self.release/'uifiles').stat().st_mode & 0o777,0o755)
        self.assertEqual((self.release/'uifiles/nightcap').stat().st_mode & 0o777,0o755)
        self.assertEqual((self.public/'channel.json').stat().st_mode & 0o777,0o644)
        self.assertEqual((self.public/'channel.json').read_bytes(),self.new)

    @unittest.skipUnless(os.name == 'posix', 'POSIX mode bits and umask')
    def test_verified_existing_release_directory_permissions_are_repaired(self):
        self.release.mkdir(mode=0o700)
        for name,data in self.assets.items():
            (self.release/name).parent.mkdir(parents=True,exist_ok=True)
            (self.release/name).write_bytes(data)
            (self.release/name).chmod(0o600)
        previous=os.umask(0o077)
        try:
            self.run_publish()
        finally:
            os.umask(previous)
        self.assertEqual(self.release.stat().st_mode & 0o777,0o755)
        for name in self.assets:self.assertEqual((self.release/name).stat().st_mode & 0o777,0o644)

    @unittest.skipUnless(os.name == 'posix', 'POSIX mode bits and umask')
    def test_invalid_baseline_does_not_change_existing_release_bytes_or_permissions(self):
        self.release.mkdir(mode=0o700)
        for name,data in self.assets.items():
            (self.release/name).parent.mkdir(parents=True,exist_ok=True)
            (self.release/name).write_bytes(data)
            (self.release/name).chmod(0o644)
        (self.public/'channel.json').write_bytes(b'unexpected baseline')
        def snapshot():
            return {q.relative_to(self.public).as_posix():
                    (q.stat().st_mode & 0o777,q.read_bytes() if q.is_file() else None)
                    for q in self.public.rglob('*')}
        before=snapshot();previous=os.umask(0o077)
        try:
            with self.assertRaisesRegex(RuntimeError,'Public channel drift'):self.run_publish()
        finally:
            os.umask(previous)
        self.assertEqual(snapshot(),before)
        self.assertEqual(self.release.stat().st_mode & 0o777,0o700)

    @unittest.skipIf(os.name == 'nt', 'POSIX symlink permissions')
    def test_symlink_release_rejected(self):
        self.release.symlink_to(self.stage, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'Release symlink'): self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(), self.old)

    @unittest.skipIf(os.name == 'nt', 'POSIX symlink permissions')
    def test_nested_symlink_rejected_without_channel_change(self):
        self.release.mkdir()
        (self.release/'uifiles').symlink_to(self.stage,target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError,'symlink'):self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)
        self.assertFalse((self.release/'dinput8.dll').exists())

    def test_foreign_nested_file_rejected(self):
        nested=self.release/'uifiles/nightcap';nested.mkdir(parents=True)
        (nested/'foreign.xml').write_bytes(b'foreign')
        with self.assertRaisesRegex(RuntimeError,'Unexpected release files'):self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.old)

    def test_nested_partial_rejects_corruption_then_recovers(self):
        nested=self.release/'uifiles/nightcap';nested.mkdir(parents=True)
        partial=nested/('equi_bazaarsearchwnd.xml'+p.PARTIAL)
        partial.write_bytes(b'foreign')
        with self.assertRaisesRegex(RuntimeError,'Partial archive drift'):self.run_publish()
        partial.write_bytes(b'new ')
        self.run_publish()
        self.assertEqual((self.public/'channel.json').read_bytes(),self.new)


if __name__ == '__main__': unittest.main()
