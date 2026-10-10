"""Validate the resolved Docker Compose contract without starting containers."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

HERE = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which('docker'), 'Docker Compose CLI required')
class ComposeTests(unittest.TestCase):
    def test_mount_options_and_private_network_contract(self):
        result = subprocess.run(
            ['docker', 'compose', '--env-file', str(HERE / '.env.example'),
             '-f', str(HERE / 'compose.yaml'), 'config', '--format', 'json'],
            check=True, capture_output=True, text=True,
        )
        config = json.loads(result.stdout)
        services = config['services']
        gateway = services['gateway']
        self.assertNotIn('ALLOW_CIDRS', gateway['environment'])
        self.assertEqual(gateway['environment']['PLAYER_ACCESS_FILE'], '/run/nightcap-access/credentials.json')
        credential_mount = next(m for m in gateway['volumes'] if m['target'] == '/run/nightcap-access')
        self.assertTrue(credential_mount['read_only'])
        self.assertTrue(credential_mount['source'].replace('\\', '/').endswith('/private/player-access'))
        self.assertEqual(services['game']['tmpfs'], ['/tmp:size=128m,mode=1777'])
        self.assertEqual(services['web']['tmpfs'], ['/tmp:size=16m,mode=1777'])
        for name, service in services.items():
            with self.subTest(service=name):
                self.assertFalse(service.get('ports'))
                if name != 'tunnel':
                    self.assertTrue(all(config['networks'][network].get('internal')
                                        for network in service['networks']))


if __name__ == '__main__':
    unittest.main()
