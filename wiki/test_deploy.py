import argparse
import hashlib
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


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def archive(self, name='index.html', data=b'wiki', link=False):
        path = self.base/'payload.tar.gz'
        with tarfile.open(path,'w:gz') as tar:
            info = tarfile.TarInfo(name)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = '/etc/passwd'
            else:
                info.size = len(data)
            tar.addfile(info,io.BytesIO(data))
        return path,{name:hashlib.sha256(data).hexdigest()}

    def test_valid_payload_and_hash_mismatch(self):
        archive,manifest = self.archive()
        deploy.unpack(archive,manifest,self.base/'release')
        self.assertEqual((self.base/'release/index.html').read_bytes(),b'wiki')
        with self.assertRaises(ValueError):
            deploy.unpack(archive,{'index.html':'0'*64},self.base/'bad')
        self.assertFalse((self.base/'bad').exists())

    def test_traversal_and_symlink_rejected(self):
        archive,manifest = self.archive('../index.html')
        with self.assertRaises(ValueError):
            deploy.unpack(archive,manifest,self.base/'release')
        archive,manifest = self.archive(link=True)
        with self.assertRaises(ValueError):
            deploy.unpack(archive,manifest,self.base/'release')

    def test_extra_file_rejected(self):
        archive,manifest = self.archive('channel.json')
        with self.assertRaises(ValueError):
            deploy.unpack(archive,manifest,self.base/'release')

    def test_aggregate_size_rejected_before_read(self):
        archive,manifest = self.archive()
        members = []
        for n in range(4):
            member = tarfile.TarInfo(f'page-{n}.html')
            member.size = 9_000_000
            members.append(member)
        from unittest.mock import MagicMock
        tar = MagicMock()
        tar.__enter__.return_value = tar
        tar.getmembers.return_value = members
        with patch.object(deploy.tarfile,'open',return_value=tar),self.assertRaisesRegex(ValueError,'32 MB'):
            deploy.unpack(archive,{m.name:'0'*64 for m in members},self.base/'release')
        tar.extractfile.assert_not_called()

    def test_stale_config_aborts_before_receipt_or_unpack(self):
        (self.base/'nginx.conf').write_bytes(b'private host config')
        args = argparse.Namespace(release='20261009-wiki',expected_config_sha='0'*64)
        with patch.object(deploy,'BASE',self.base),self.assertRaises(ValueError):
            deploy.main(args)
        self.assertFalse((self.base/'website-history').exists())

    def test_new_host_has_separate_root_and_no_proxy(self):
        conf = (Path(__file__).parent/'nginx.conf').read_text()
        self.assertIn('server_name wiki.nightcapgame.org;',conf)
        self.assertIn('root /srv/public/wiki/current;',conf)
        self.assertNotIn('proxy_pass',conf)
        self.assertNotIn('root /srv/public;',conf)
        self.assertIn("form-action 'self'",conf)

    def test_malformed_path_can_be_400_but_private_routes_must_be_404(self):
        def response(host,path,method='GET'):
            if path=='/index.html' and method=='GET':
                return 200,'hash',{'X-Content-Type-Options':'nosniff','Content-Security-Policy':"script-src 'self'"}
            return (403 if method=='POST' else 400 if path.startswith('/../') else 404),'',{}
        with patch.object(deploy,'probe',side_effect=response):
            deploy.verify({'index.html':'hash'})
        def leak(host,path,method='GET'):
            return (200,'private',{}) if path=='/channel.json' else response(host,path,method)
        with patch.object(deploy,'probe',side_effect=leak),self.assertRaisesRegex(RuntimeError,'Unexpected exposed route'):
            deploy.verify({'index.html':'hash'})

    @unittest.skipIf(os.name=='nt','Real POSIX symlink/recovery test runs on the deployment host')
    def test_reload_failure_still_removes_pointer_and_preserves_original_error(self):
        original = b'private host config'
        (self.base/'nginx.conf').write_bytes(original)
        archive,manifest = self.archive()
        manifest_file = self.base/'manifest.json'
        manifest_file.write_text(json.dumps(manifest))
        vhost = self.base/'wiki.conf'
        vhost.write_bytes(b'new wiki host')
        args = argparse.Namespace(release='20261009-wiki',expected_config_sha=deploy.sha(original),archive=archive,manifest=manifest_file,vhost=vhost)
        with patch.object(deploy,'BASE',self.base), patch.object(deploy,'services',return_value=list(range(5))), patch.object(deploy,'protected',return_value={'/':(200,'hash')}), patch.object(deploy,'wait_for_host'), patch.object(deploy,'verify',side_effect=ValueError('original validation failure')), patch.object(deploy,'reload_web',side_effect=[None,RuntimeError('reload recovery failure')]):
            with self.assertRaisesRegex(RuntimeError,'recovery requires attention') as caught:
                deploy.main(args)
        self.assertEqual(str(caught.exception.__cause__),'original validation failure')
        self.assertEqual((self.base/'nginx.conf').read_bytes(),original)
        self.assertFalse((self.base/'data/public/wiki/current').is_symlink())


if __name__ == '__main__':
    unittest.main()
