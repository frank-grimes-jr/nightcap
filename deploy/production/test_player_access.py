import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import player_access as access


class PlayerAccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = self.root / 'registry' / 'credentials.json'
        access.initialize(self.registry, os.getgid() if os.name != 'nt' else 0)

    def test_issue_hash_only_then_revoke_preserves_other_player(self):
        first = access.issue(self.registry, 'joe', self.root / 'joe.txt')
        second = access.issue(self.registry, 'owner', self.root / 'owner.txt')
        code = (self.root / 'joe.txt').read_text().strip()
        rows = access.read_registry(self.registry)['credentials']
        self.assertEqual(len(code), 80)
        self.assertEqual(rows[0]['secret_hash'], hashlib.sha256(code.encode()).hexdigest())
        self.assertNotIn(code, self.registry.read_text())
        self.assertNotIn(code, json.dumps(first))
        self.assertEqual(access.revoke(self.registry, first['id'])['player'], 'joe')
        self.assertEqual(access.read_registry(self.registry)['credentials'][0]['id'], second['id'])
        self.assertEqual(len(list((self.registry.parent / '.backups').iterdir())), 3)
        if os.name != 'nt':
            self.assertEqual((self.root / 'joe.txt').stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.registry.stat().st_mode & 0o777, 0o640)

    def test_no_overwrite_or_unsafe_labels_and_failed_write_is_recoverable(self):
        access.issue(self.registry, 'joe', self.root / 'joe.txt')
        before = self.registry.read_bytes()
        with self.assertRaises(FileExistsError):
            access.issue(self.registry, 'joe', self.root / 'joe.txt')
        with self.assertRaises(ValueError):
            access.issue(self.registry, 'joe\ninjected', self.root / 'bad.txt')
        with self.assertRaises(ValueError):
            access.issue(self.registry, 'joe', self.registry.parent / 'delivery.txt')
        with patch.object(access.os, 'replace', side_effect=OSError('test crash')):
            with self.assertRaises(OSError):
                access.issue(self.registry, 'joe', self.root / 'interrupted.txt')
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertTrue((self.root / 'interrupted.txt').exists())
        self.assertFalse(list(self.registry.parent.glob('.registry-*')))

    def test_concurrent_issuers_do_not_lose_credentials(self):
        processes = [subprocess.Popen([sys.executable, str(Path(access.__file__)), '--registry', str(self.registry), 'issue', 'joe', '--out', str(self.root / f'code-{i}.txt')], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(4)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertNotIn('nc1.', stdout)
        self.assertEqual(len(access.read_registry(self.registry)['credentials']), 4)

    def test_corrupt_registry_never_overwritten(self):
        self.registry.write_text('{bad')
        with self.assertRaises(ValueError):
            access.issue(self.registry, 'joe', self.root / 'bad.txt')
        self.assertEqual(self.registry.read_text(), '{bad')
        self.assertFalse((self.root / 'bad.txt').exists())


if __name__ == '__main__':
    unittest.main()
