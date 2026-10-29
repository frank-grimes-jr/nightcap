"""The release-specific adapter requires finished receipts before remote work."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import capture_activation_guard as guard
import publish_wiki as publish


class ActivationGuardTests(unittest.TestCase):
    def test_missing_client_receipt_cannot_start_capture(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(guard, 'HERE', Path(tmp) / 'wiki'), patch.object(guard, 'remote') as remote:
            with self.assertRaises(FileNotFoundError):
                guard.main()
            remote.assert_not_called()

    def test_remote_program_pins_receipts_and_verified_game_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'wiki').mkdir()
            (root / 'client').mkdir()
            (root / 'client/published.json').write_text(json.dumps(dict(release=2026102901, channel_sha256='abc')))
            def capture(code):
                ast.parse(code)
                for requirement in ["runtime['gateway_open'] is True", "runtime['database_restored'] is False",
                                    "row['Image']==runtime['runtime']['image_id']", "row['State']['StartedAt']==runtime['runtime']['started_at']",
                                    "fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)", 'runtime_receipt_sha256', 'client_receipt_sha256']:
                    self.assertIn(requirement, code)
                return dict(verified=True, services_after={'game': {'Image': 'sha256:test'}}, channel_sha256='abc')
            with patch.object(guard, 'HERE', root / 'wiki'), patch.object(guard, 'remote', side_effect=capture):
                guard.main()
            self.assertTrue((root / 'wiki/activation-guard.json').exists())

    def test_publisher_requires_activation_guard_before_any_remote_call(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(publish, 'HERE', Path(tmp)), patch.object(publish, 'remote') as remote:
            with self.assertRaises(FileNotFoundError):
                publish.main()
            remote.assert_not_called()


if __name__ == '__main__':
    unittest.main()
