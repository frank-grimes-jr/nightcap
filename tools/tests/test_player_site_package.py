import importlib.util
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('player_site_package', ROOT/'tools/player_site_package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PublicPayloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in package.FILES:
            target = self.root/name
            target.parent.mkdir(exist_ok=True)
            target.write_text('Nightcap')
        (self.root/'.env').write_text('PRIVATE_SENTINEL')
        (self.root/'database.sql').write_text('PRIVATE_SENTINEL')
        self.output = self.root/'public.tar.gz'
        self.root_patch = patch.object(package, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_private_files_are_never_published(self):
        package.package(self.output)
        with tarfile.open(self.output) as archive:
            self.assertEqual(set(archive.getnames()), set(package.FILES))
            for member in archive:
                self.assertNotIn(b'PRIVATE_SENTINEL', archive.extractfile(member).read())

    def test_branding_in_hidden_metadata_blocks_package(self):
        (self.root/'index.html').write_text('<meta content="E' + 'Q"><p>Nightcap</p>')
        with self.assertRaisesRegex(ValueError, 'Brand restriction'):
            package.package(self.output)
        self.assertFalse(self.output.exists())

    def test_existing_release_cannot_be_overwritten(self):
        package.package(self.output)
        original = self.output.read_bytes()
        (self.root/'index.html').write_text('A different page')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            package.package(self.output)
        self.assertEqual(original, self.output.read_bytes())

    def test_manifest_matches_every_uploaded_byte(self):
        import hashlib
        package.package(self.output)
        manifest = json.loads(self.output.with_suffix('.json').read_text())
        with tarfile.open(self.output) as archive:
            for member in archive:
                self.assertEqual(manifest[member.name], hashlib.sha256(archive.extractfile(member).read()).hexdigest())


class DeploymentPreconditionsTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'POSIX mode/umask regression')
    def test_restrictive_umask_keeps_public_payload_readable_and_receipts_private(self):
        spec = importlib.util.spec_from_file_location('site_deploy', ROOT/'deploy/production/player-site-deploy.py')
        deploy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(deploy)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            public = base/'data/public'
            public.mkdir(parents=True)
            for name in ('channel.json','launcher-channel.json','guide.html','nightcap-friends.zip'):
                (public/name).write_text('unchanged')
            config = base/'nginx.conf';config.write_text('private config')
            payload = base/'payload';payload.mkdir()
            for name in package.FILES:
                p = payload/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Nightcap')
            archive = base/'site.tar.gz'
            with patch.object(package,'ROOT',payload):package.package(archive)
            sites=public/'player-site';history=base/'history'
            argv=['publisher','stage',str(archive),str(archive.with_suffix('.json')),
                  '20261009-mode-test',deploy.sha(config.read_bytes()),str(config)]
            prior_umask=os.umask(0o077)
            try:
                with patch.object(deploy,'BASE',base),patch.object(deploy,'SITES',sites), \
                     patch.object(deploy,'HISTORY',history),patch.object(deploy.sys,'argv',argv), \
                     patch.object(deploy,'containers',return_value={}), \
                     patch.object(deploy,'current_pointer',return_value='previous'), \
                     patch.object(deploy,'activate'),patch.object(deploy,'restore'):
                    deploy.main()
            finally:os.umask(prior_umask)
            target=sites/'20261009-mode-test'
            self.assertEqual(sites.stat().st_mode & 0o777,0o755)
            self.assertEqual(target.stat().st_mode & 0o777,0o755)
            self.assertEqual((target/'site-assets').stat().st_mode & 0o777,0o755)
            self.assertTrue(all((target/n).stat().st_mode & 0o777 == 0o644 for n in package.FILES))
            self.assertEqual((history/'20261009-mode-test').stat().st_mode & 0o777,0o700)
            self.assertEqual((history/'20261009-mode-test/receipt.json').stat().st_mode & 0o777,0o600)

    def test_stale_pointer_fails_before_service_action(self):
        spec = importlib.util.spec_from_file_location('site_deploy', ROOT/'deploy/production/player-site-deploy.py')
        deploy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(deploy)
        with patch.object(deploy, 'current_pointer', return_value='20261001-newer'), \
             patch.object(deploy, 'compose', side_effect=AssertionError('Unexpected service action')):
            with self.assertRaisesRegex(AssertionError, 'pointer changed'):
                deploy.check_activation_preconditions({'previous':'20261001-older'}, ROOT)



class PrivateRouteTests(unittest.TestCase):
    def setUp(self):
        import io
        import urllib.error
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        spec = importlib.util.spec_from_file_location('site_deploy', ROOT/'deploy/production/player-site-deploy.py')
        self.deploy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.deploy)
        self.leaking_host = None
        self.leaking_alias = False
        self.cache = 'private, no-store, no-transform'

        def origin(request, timeout):
            host = request.get_header('Host')
            storage = '/player-site' in request.full_url
            if (host == 'play.nightcapgame.org' and (not storage or self.leaking_alias)) or host == self.leaking_host:
                response = MagicMock()
                response.__enter__.return_value = SimpleNamespace(
                    status=200, read=lambda: b'Nightcap', headers={
                        'Content-Security-Policy': "default-src 'none'",
                        'Cache-Control': self.cache})
                return response
            raise urllib.error.HTTPError(request.full_url, 404, 'Not Found', {}, io.BytesIO(b''))

        self.urlopen = patch.object(self.deploy.urllib.request, 'urlopen', side_effect=origin)
        self.urlopen.start()
        self.addCleanup(self.urlopen.stop)
        self.receipt = {'target': '20261001-private-test', 'files': {'index.html': self.deploy.sha(b'Nightcap')}}

    def test_restricted_player_host_with_closed_alternative_hosts_passes(self):
        self.deploy.verify_routes(self.receipt)

    def test_website_exposure_on_another_hostname_fails_verification(self):
        for host in ('nightcapgame.org', 'www.nightcapgame.org', 'unknown.invalid'):
            with self.subTest(host=host):
                self.leaking_host = host
                with self.assertRaises(AssertionError):
                    self.deploy.verify_routes(self.receipt)

    def test_storage_alias_exposure_fails_verification(self):
        self.leaking_alias = True
        with self.assertRaises(AssertionError):
            self.deploy.verify_routes(self.receipt)

    def test_cacheable_website_response_fails_verification(self):
        for cache in ('public, no-cache, no-transform', 'private, no-store',
                      'private, no-cache, no-transform', 'private, no-store, no-transform, public'):
            with self.subTest(cache=cache):
                self.cache = cache
                with self.assertRaises(AssertionError):
                    self.deploy.verify_routes(self.receipt)


if __name__ == '__main__':
    unittest.main()
