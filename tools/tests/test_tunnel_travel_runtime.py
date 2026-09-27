"""The hail smoke must resolve the installed paths, not repository helpers."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('perl'), 'Perl is required for the installed quest check')
class RuntimePaths(unittest.TestCase):
    def check_runtime(self, plugin_directory, directories):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            plugins = runtime / plugin_directory
            plugins.mkdir(parents=True)
            for name in ('tunnel_travel.pl', 'tunnel_travel_data.pl'):
                shutil.copyfile(ROOT / 'server-mods/plugins' / name, plugins / name)
            quests = runtime / 'quests/ecommons'
            quests.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'server-mods/quests/ecommons/999810.pl', quests / '999810.pl')
            (runtime / 'eqemu_config.json').write_text(json.dumps({'server': {'directories': directories}}))
            return subprocess.run(['perl', str(ROOT / 'tools/tests/tunnel_travel_quests.t'),
                                   str(ROOT), str(runtime)], capture_output=True, text=True)

    def test_misplaced_plugins_reproduce_the_production_failure(self):
        result = self.check_runtime('quests/plugins', {})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Expected one loaded tunnel_travel_data.pl', result.stderr)

    def test_default_plugin_directory_loads_and_exercises_installed_hail(self):
        result = self.check_runtime('plugins', {})
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn('ok 25 - numeric quest adapter exposes the menu', result.stdout)

    def test_configured_path_array_overrides_scalar(self):
        config = {'plugins': 'quests/plugins', 'plugin_paths': ['custom-plugins']}
        result = self.check_runtime('custom-plugins', config)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        result = self.check_runtime('quests/plugins', config)
        self.assertNotEqual(result.returncode, 0)

    def test_empty_array_uses_configured_scalar(self):
        result = self.check_runtime('quests/plugins', {'plugins': 'quests/plugins', 'plugin_paths': []})
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == '__main__':
    unittest.main()
