import json
import gzip
from datetime import datetime, timezone
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

if os.name=='posix':import loot_install as operator


@unittest.skipUnless(os.name=='posix','Linux systemd/config operator')
class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.base=self.root/'production';self.base.mkdir()
        (self.base/'website-history').mkdir();self.units=self.root/'units';self.units.mkdir()
        self.config=self.base/'nginx.conf'
        self.before=b'server { server_name wiki.nightcapgame.org; root /srv/public/wiki/current; }\n'
        self.config.write_bytes(self.before)
        self.manifest=self.root/'manifest.json';self.manifest.write_text('{}')
        self.args=SimpleNamespace(expected_config_sha=operator.deploy.sha(self.before),wiki_manifest=self.manifest,receipt='check')
        self.after=operator.candidate_config(self.before,(operator.SOURCE/'loot-nginx.conf').read_bytes())
        def service(*args):
            if args==('start',operator.NAMES[0]):
                path=self.base/'data/public/wiki-data/current';path.mkdir(parents=True)
                (path/'index.json.gz').write_bytes(gzip.compress(json.dumps({'snapshot':'a'*16,'captured_at':datetime.now(timezone.utc).isoformat()}).encode()))
        patches=[patch.object(operator.deploy,'BASE',self.base),patch.object(operator,'INSTALL',self.root/'reader'),
            patch.object(operator,'UNITS',self.units),patch.object(operator,'systemctl',side_effect=service),
            patch.object(operator.deploy,'services',return_value=[('service',str(i),'start') for i in range(5)]),
            patch.object(operator.deploy,'protected',return_value={'/':(200,'hash')}),
            patch.object(operator.deploy,'verify'),patch.object(operator.deploy,'reload_web'),patch.object(operator,'verify_data'),patch.object(operator,'require_absent_units'),
            patch.object(operator.deploy,'command',return_value='FragmentPath=\nDropInPaths=')]
        self.mocks=[p.start() for p in patches]
        for p in patches:self.addCleanup(p.stop)

    def test_success_rehearses_inverse_and_starts_timer_last(self):
        result=operator.install(self.args)
        self.assertTrue(result['rollback_rehearsed']);self.assertEqual(self.config.read_bytes(),self.after)
        self.assertEqual(operator.deploy.reload_web.call_count,3)
        self.assertEqual(operator.systemctl.call_args_list[-2].args,('enable','--now',operator.NAMES[1]))
        receipt=self.base/'website-history/check'
        self.assertEqual(operator.rollback(receipt)['result'],'ROLLED BACK')
        self.assertEqual(self.config.read_bytes(),self.before)
        self.assertFalse(operator.INSTALL.exists())

    def test_stale_preimage_or_existing_reader_refuses_before_mutation(self):
        self.args.expected_config_sha='wrong'
        with self.assertRaises(ValueError):operator.install(self.args)
        self.assertFalse(operator.INSTALL.exists())
        self.args.expected_config_sha=operator.deploy.sha(self.before);operator.INSTALL.mkdir()
        with self.assertRaises(ValueError):operator.install(self.args)
        self.assertEqual(self.config.read_bytes(),self.before)

    def test_route_failure_restores_config_and_removes_owned_units(self):
        operator.verify_data.side_effect=[RuntimeError('bad response'),None]
        with self.assertRaisesRegex(RuntimeError,'bad response'):operator.install(self.args)
        self.assertEqual(self.config.read_bytes(),self.before)
        self.assertFalse(operator.INSTALL.exists());self.assertEqual(list(self.units.iterdir()),[])

    def test_failed_capture_keeps_existing_web_config(self):
        operator.systemctl.side_effect=lambda *args:(_ for _ in ()).throw(RuntimeError('capture failed')) if args[0]=='start' else None
        with self.assertRaisesRegex(RuntimeError,'capture failed'):operator.install(self.args)
        self.assertEqual(self.config.read_bytes(),self.before);operator.deploy.reload_web.assert_not_called()

    def test_concurrent_config_is_preserved(self):
        def changed(*args):
            self.config.write_bytes(b'new operator config')
            raise RuntimeError('concurrent change')
        operator.verify_data.side_effect=changed
        with self.assertRaisesRegex(RuntimeError,'manual inverse'):operator.install(self.args)
        self.assertEqual(self.config.read_bytes(),b'new operator config')

    def test_manual_rollback_refuses_changed_reader_or_config(self):
        operator.install(self.args);receipt=self.base/'website-history/check'
        (operator.INSTALL/'loot_model.py').write_text('a later version')
        with self.assertRaisesRegex(RuntimeError,'later installation'):operator.rollback(receipt)
        self.assertEqual(self.config.read_bytes(),self.after)

    def test_injection_scope_is_exact(self):
        for content in [b'',self.before+self.before,self.after]:
            with self.assertRaises(ValueError):operator.candidate_config(content,b'alias /srv/public/wiki-data/$1;')

    def test_preexisting_effective_unit_rejected(self):
        operator.require_absent_units.side_effect=ValueError('preexisting override')
        with self.assertRaisesRegex(ValueError,'override'):operator.install(self.args)
        self.assertFalse(operator.INSTALL.exists())

    def test_failure_does_not_stop_a_replaced_unit(self):
        def replaced(*args):
            (self.units/operator.NAMES[0]).write_text('a later unit')
            raise RuntimeError('replacement')
        operator.verify_data.side_effect=replaced
        with self.assertRaisesRegex(RuntimeError,'later installation'):operator.install(self.args)
        self.assertNotIn(('stop',operator.NAMES[0]),[c.args for c in operator.systemctl.call_args_list])

    def test_rollback_does_not_stop_unit_with_new_dropin(self):
        operator.install(self.args)
        operator.deploy.command.return_value='FragmentPath=\nDropInPaths=/run/systemd/system/nightcap-wiki-loot.service.d/override.conf'
        operator.systemctl.reset_mock()
        with self.assertRaisesRegex(RuntimeError,'Effective unit changed'):
            operator.rollback(self.base/'website-history/check')
        operator.systemctl.assert_not_called()


if __name__=='__main__':unittest.main()
