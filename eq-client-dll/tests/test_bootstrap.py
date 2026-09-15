"""Build the proxy and bootstrap fixtures first; never launches actual eqgame."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BootstrapTests(unittest.TestCase):
    def test_entry_gate(self):
        cases = {"success": "", "repeat": "", "fail": "initializer_failed", "hang": "bootstrap_timeout",
                 "crash": "startup_exception", "reject": "runtime_health",
                 "wrong_entry": "entry_range", "wrong_byte": "entry_breakpoint", "wrong_proxy": "entry_restore",
                 "owner_crash": "", "candidate": ("initializer_failed", "primary_exited", "process_exited")}
        for mode, reason in cases.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix="nightcap-entry-") as temp:
                directory = Path(temp) / "client é space"
                directory.mkdir()
                for name in ("bootstrap-probe.exe", "bootstrap-fixture.dll", "bootstrap-host.exe"):
                    shutil.copy2(ROOT / "build/tests" / name, directory / name)
                shutil.copy2(ROOT / "build/dinput8.dll", directory / "dinput8.dll")
                shutil.copy2(ROOT / "config/nightcap-patches.cfg", directory / "nightcap-patches.cfg")
                env = os.environ.copy()
                env["NIGHTCAP_BOOTSTRAP_TEST"] = mode
                env["NIGHTCAP_LAUNCH_NONCE"] = "0123456789abcdef0123456789abcdef"
                result = subprocess.run([directory / "bootstrap-probe.exe"], cwd=directory,
                                        env=env, capture_output=True, timeout=15)
                output = result.stdout.decode(errors="replace")
                if mode == "owner_crash":
                    self.assertEqual(result.returncode, 77, output + str(result.stderr))
                    self.assertFalse((directory / "main-entered").exists())
                    pid, created = map(int, (directory / "owner-child").read_text().split())
                    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                    kernel.OpenProcess.restype = wintypes.HANDLE
                    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
                    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
                    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
                    process = kernel.OpenProcess(0x100000 | 0x1000, False, pid)
                    if process:
                        try:
                            times = [wintypes.FILETIME() for _ in range(4)]
                            self.assertTrue(kernel.GetProcessTimes(process, *(ctypes.byref(t) for t in times)))
                            actual = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
                            if actual == created:
                                self.assertEqual(kernel.WaitForSingleObject(process, 1000), 0)
                        finally:
                            kernel.CloseHandle(process)
                    else:
                        self.assertEqual(ctypes.get_last_error(), 87) # PID no longer exists
                    continue
                self.assertEqual(result.returncode, 0 if mode in ("success", "repeat") else 1, output + str(result.stderr))
                self.assertEqual((directory / "main-entered").exists(), mode in ("success", "repeat"), output)
                self.assertTrue(any("reason=" + value in output for value in (reason if isinstance(reason, tuple) else (reason,))), output)
                if mode in ("success", "repeat"):
                    self.assertTrue((directory / "verified-before-main").is_file())
                    self.assertTrue((directory / "bootstrap-ready").is_file())
                if mode == "candidate":
                    files = list(directory.glob("nightcap_health_*.json"))
                    self.assertEqual(len(files), 1, output)
                    health = json.loads(files[0].read_bytes())
                    self.assertEqual(health["state"], "failed")
                    self.assertEqual(health["reason"], "unsupported_executable")
                    self.assertEqual(health["nonce"], env["NIGHTCAP_LAUNCH_NONCE"])
                    self.assertEqual(health["applied_mask"], 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
