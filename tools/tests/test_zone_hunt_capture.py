"""The capture CLI must retain its requested output after constructing SSH args."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class CaptureCliTests(unittest.TestCase):
    def test_successful_remote_capture_is_saved_to_requested_path(self):
        captured = {'spawns': [{'id': '12'}], 'quest_files': [], 'quest_hashes': {}}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'new-directory' / 'capture.json'
            with patch('sys.argv', ['zone_hunt_capture.py', '--output', str(output)]), \
                 patch('subprocess.run', return_value=SimpleNamespace(
                     returncode=0, stdout=json.dumps(captured), stderr='')) as remote, \
                 contextlib.redirect_stdout(io.StringIO()) as printed:
                runpy.run_path(str(ROOT / 'tools/zone_hunt_capture.py'), run_name='__main__')
            self.assertEqual(json.loads(output.read_text()), captured)
            self.assertEqual(json.loads(printed.getvalue()), {'spawns': 1, 'quest_files': 0, 'quest_hashes': 0})
            command = remote.call_args.args[0]
            self.assertIsInstance(command, list)
            self.assertEqual(command[-1], 'sudo -n python3 -')
            self.assertIn('START TRANSACTION READ ONLY;', remote.call_args.kwargs['input'])


if __name__ == '__main__':
    unittest.main()
