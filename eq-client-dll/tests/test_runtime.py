"""Disposable-process checks. Build build.bat and tests/build-runtime-tests.bat first.
Never loads the candidate into eqgame or changes the installed game client.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = (ROOT / "config/nightcap-patches.cfg").read_bytes()
STOP_CODE = 0x4E430001

class RuntimeTests(unittest.TestCase):
    def test_ui_state_and_hooks(self):
        for name in ("ui-state", "ui-hooks", "pet-state", "pet-management", "spell-access", "spell-inspection", "spell-menu", "model-policy", "model-hooks"):
            with self.subTest(name=name):
                result = subprocess.run([ROOT / f"build/tests/{name}.exe"], capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_patch_failure_injection(self):
        result = subprocess.run([ROOT / "build/tests/verified-patch.exe"], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unload_before_forwarding(self):
        with tempfile.TemporaryDirectory(prefix="nightcap-runtime-") as temp:
            directory = Path(temp)
            for source, target in [("build/tests/runtime-host.exe", "host.exe"), ("build/dinput8.dll", "dinput8.dll")]:
                shutil.copy2(ROOT / source, directory / target)
            result = subprocess.run([directory / "host.exe", directory / "dinput8.dll", "unload"], timeout=15)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(list(directory.glob("nightcap_*")))

    def test_required_failures_never_return_to_host(self):
        cases = [
            ("missing", None, None, "configuration_open"),
            ("disabled", CONFIG.replace(b"equipment=1", b"equipment=0"), None, "equipment"),
            ("bad_config", CONFIG + b"foreign=1\n", None, "invalid_configuration"),
            ("oversize", b"a" * 4097, None, "configuration_read"),
            ("host", CONFIG, None, "unsupported_executable"),
            ("nonce", CONFIG, "a" * 32, "unsupported_executable"),
            ("bad_nonce", CONFIG, "BAD", "launch_nonce"),
        ]
        for label, config, nonce, reason in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory(prefix="nightcap-runtime-") as temp:
                # Non-ASCII + spaces exercise module-relative Unicode paths.
                directory = Path(temp) / "client é space"
                directory.mkdir()
                shutil.copy2(ROOT / "build/tests/runtime-host.exe", directory / "host.exe")
                shutil.copy2(ROOT / "build/dinput8.dll", directory / "dinput8.dll")
                if config is not None:
                    (directory / "nightcap-patches.cfg").write_bytes(config)
                env = os.environ.copy()
                env.pop("NIGHTCAP_LAUNCH_NONCE", None)
                if nonce is not None:
                    env["NIGHTCAP_LAUNCH_NONCE"] = nonce
                # Deliberately different cwd: no config or logs should use cwd.
                child = subprocess.Popen([directory / "host.exe", directory / "dinput8.dll"], cwd=temp, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    out, err = child.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
                    self.fail("owned disposable host did not terminate")
                self.assertEqual(child.returncode & 0xffffffff, STOP_CODE, out + err)
                paths = list(directory.glob("nightcap_health_*.json"))
                self.assertEqual(len(paths), 1)
                record = json.loads(paths[0].read_bytes())
                self.assertEqual(record["pid"], child.pid)
                self.assertGreater(int(record["process_created"]), 0)
                self.assertEqual(record["state"], "failed")
                self.assertEqual(record["reason"], reason)
                self.assertEqual(record["applied_mask"], 0)
                self.assertEqual(record["nonce"], nonce if nonce == "a" * 32 else "")
                if reason in ("equipment", "invalid_configuration", "unsupported_executable"):
                    self.assertEqual(record["config_sha256"], hashlib.sha256(config).hexdigest())
                self.assertFalse(list(directory.glob("*.tmp")))
                self.assertFalse(list(Path(temp).glob("nightcap_*")))

    def test_health_atomic_replacement(self):
        with tempfile.TemporaryDirectory(prefix="nightcap-health-") as temp:
            result = subprocess.run([ROOT / "build/tests/runtime-health.exe", temp + os.sep], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            expected = result.stdout.strip()
            record = json.loads(expected)
            actual = Path(temp, f"nightcap_health_{record['pid']}.json").read_bytes()
            self.assertEqual(actual, expected)
            self.assertEqual(record["state"], "ready")
            self.assertEqual(record["config_sha256"], hashlib.sha256(b"fixture").hexdigest())
            self.assertFalse(list(Path(temp).glob("*.tmp")))

if __name__ == "__main__":
    unittest.main(verbosity=2)
