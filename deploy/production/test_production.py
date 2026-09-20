import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
configure=module('configure')
start=module('start')
accounts=module('accounts')

class ProductionTests(unittest.TestCase):
    def test_old_native_pair_is_rejected_before_startup(self):
        world=b'\x7fELF\x00CALL nightcap_market_rotate({},{},{})\x00'
        markers=[b'LivingEconomy\x00',b'MarketAnnouncement\x00',b'_Z9Perl__oocPKc',
                 b'Your selected classes cannot cast this spell at your current level.']
        with tempfile.TemporaryDirectory() as tmp, patch.object(start,'BIN',Path(tmp)):
            root=Path(tmp)
            (root/'world').write_bytes(world)
            (root/'zone').write_bytes(b'\x7fELF'+b'\x00'.join(markers))
            start.validate_native()
            for marker in markers:
                (root/'zone').write_bytes(b'\x7fELF'+b'\x00'.join(m for m in markers if m!=marker))
                with self.assertRaises(ValueError):start.validate_native()
            (root/'zone').write_bytes(b'\x7fELF'+b'\x00'.join(markers))
            (root/'world').write_bytes(b'\x7fELF\x00CALL nightcap_market_rotate({})\x00')
            with self.assertRaises(ValueError):start.validate_native()

    def test_sql_inputs_are_bound_and_invalid_names_rejected(self):
        sql=accounts.sql_for('create','friend-one','$7$fixture')
        self.assertIn('EXECUTE p USING @name,@hash',sql)
        self.assertNotIn('friend-one',sql)
        for name in ["x' OR 1=1",'bad;name','a','x'*25]:
            with self.assertRaises(ValueError):accounts.sql_for('create',name,'hash')
        world=accounts.sql_for('world','nightcap-world','hash')
        self.assertIn('SET autocommit=0',world)
        self.assertIn('WHERE @created=1',world)
        self.assertIn('COMMIT',world)

    @unittest.skipUnless(os.name=='posix','Linux private permissions and runtime')
    def test_config_generation_and_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'base.json'
            base.write_text(json.dumps({'server':{'world':{'loginserver2':{'host':'public'},'telnet':{'enabled':'true'}},'zones':{'defaultstatus':'250'}}}))
            configure.configure(base,root/'private')
            for name in ('eqemu_config.json','login.json','db_password'):
                self.assertEqual((root/'private'/name).stat().st_mode&0o777,0o600)
            previous=os.getcwd()
            try:
                os.chdir(root/'private')
                with patch.dict(os.environ,{},clear=True):start.validate()
                with patch.dict(os.environ,{'LSPX':'0'}):
                    with self.assertRaises(ValueError):start.validate()
                cfg=json.loads(Path('eqemu_config.json').read_text())
                cfg['server']['zones']['defaultstatus']='250'
                Path('eqemu_config.json').write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):start.validate()
            finally:os.chdir(previous)
            with self.assertRaises(FileExistsError):configure.configure(base,root/'private')

    @unittest.skipUnless(os.name=='posix' and shutil.which('bash'),'Linux backup script')
    def test_failed_dump_never_creates_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fakebin=root/'bin';fakebin.mkdir()
            envfile=root/'backup.env';envfile.write_text('')
            (fakebin/'docker').write_text('#!/bin/sh\nprintf partial-dump\nexit 42\n')
            marker=root/'restic-called'
            (fakebin/'restic').write_text(f'#!/bin/sh\ntouch "{marker}"\n')
            for path in fakebin.iterdir():path.chmod(0o700)
            script=(HERE/'backup.sh').read_text().replace('/opt/nightcap/deploy/production',str(root)).replace('/etc/nightcap-backup.env',str(envfile))
            candidate=root/'backup.sh';candidate.write_text(script)
            result=subprocess.run(['bash',str(candidate)],env={**os.environ,'PATH':str(fakebin)+':'+os.environ['PATH']},capture_output=True)
            self.assertEqual(result.returncode,42)
            self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name=='posix','native sodium library')
    def test_native_compatible_password_hash(self):
        self.assertTrue(accounts.password_hash('fixture-password-123').startswith('$7$'))
        for invalid in ['short','a'*29,'contains a space']:
            with self.assertRaises(ValueError):accounts.password_hash(invalid)

if __name__=='__main__':unittest.main()
