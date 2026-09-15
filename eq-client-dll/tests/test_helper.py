"""Native helper IPC fixtures. Never starts the installed game executable."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import pefile

ROOT = Path(__file__).resolve().parents[1]
MAGIC = 0x4e434231
NONCE = "0123456789abcdef0123456789abcdef"
KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
KERNEL.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
KERNEL.CreateFileW.restype = wintypes.HANDLE
KERNEL.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
KERNEL.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
KERNEL.OpenProcess.restype = wintypes.HANDLE
KERNEL.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
KERNEL.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
KERNEL.CloseHandle.argtypes = [wintypes.HANDLE]


def creation(handle):
    times = [wintypes.FILETIME() for _ in range(4)]
    if not KERNEL.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
        raise ctypes.WinError(ctypes.get_last_error())
    return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime


def assert_exited(test, pid, created):
    handle = KERNEL.OpenProcess(0x100000 | 0x1000, False, pid)
    if not handle:
        test.assertEqual(ctypes.get_last_error(), 87)
        return
    try:
        if creation(handle) == created:
            test.assertEqual(KERNEL.WaitForSingleObject(handle, 5000), 0)
    finally:
        KERNEL.CloseHandle(handle)


def fixture(directory, candidate=False):
    directory.mkdir()
    shutil.copy2(ROOT / "build/tests/helper-fixture/eqgame.exe", directory / "eqgame.exe")
    proxy = ROOT / ("build/dinput8.dll" if candidate else "build/tests/helper-fixture/dinput8.dll")
    shutil.copy2(proxy, directory / "dinput8.dll")
    shutil.copy2(ROOT / "config/nightcap-patches.cfg", directory / "nightcap-patches.cfg")


class Launch:
    def __init__(self, directory, mode="success", nonce=NONCE, malformed=False, partial=False, fragmented=False, hold=False):
        exe = pefile.PE(str(directory / "eqgame.exe"))
        proxy = pefile.PE(str(directory / "dinput8.dll"))
        entry = exe.OPTIONAL_HEADER.AddressOfEntryPoint
        original = exe.get_data(entry, 1)[0]
        initializer = next(e.address for e in proxy.DIRECTORY_ENTRY_EXPORT.symbols if e.name == b"NightcapInitialize")
        handles = []
        try:
            for name in ("eqgame.exe", "dinput8.dll"):
                handle = KERNEL.CreateFileW(str(directory / name), 0x80000000, 1, None, 3, 0x00200000, None)
                if handle == ctypes.c_void_p(-1).value:
                    raise ctypes.WinError(ctypes.get_last_error())
                handles.append(handle)
                if not KERNEL.SetHandleInformation(handle, 1, 1):
                    raise ctypes.WinError(ctypes.get_last_error())
            parent = KERNEL.OpenProcess(0x100000 | 0x1000, True, os.getpid())
            if not parent:
                raise ctypes.WinError(ctypes.get_last_error())
            handles.append(parent)
            startup = subprocess.STARTUPINFO()
            startup.lpAttributeList = {"handle_list": handles}
            env = os.environ.copy()
            env["NIGHTCAP_BOOTSTRAP_TEST"] = mode
            env["NIGHTCAP_HELPER_HOLD"] = "1" if hold else "0"
            if nonce is None:
                env.pop("NIGHTCAP_LAUNCH_NONCE", None)
            else:
                env["NIGHTCAP_LAUNCH_NONCE"] = nonce
            self.process = subprocess.Popen([ROOT / "build/nightcap-bootstrap.exe"], cwd=directory, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                startupinfo=startup, close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.created = creation(int(self.process._handle))
            self.messages = queue.Queue()
            self.reader = threading.Thread(target=self._read, daemon=True)
            self.reader.start()
            encoded = str(directory).encode("utf-16-le")
            request = struct.pack("<IIQQQIIIIII", MAGIC, 99 if malformed else 1, *handles,
                entry, initializer, proxy.OPTIONAL_HEADER.SizeOfImage, 2000, original, len(encoded)//2) + encoded
            if partial:
                self.process.stdin.write(request[:7]); self.process.stdin.close()
            elif fragmented:
                for i in range(0, len(request), 7):
                    self.process.stdin.write(request[i:i+7]); self.process.stdin.flush()
            else:
                self.process.stdin.write(request); self.process.stdin.flush()
        finally:
            exe.close(); proxy.close()
            for handle in handles:
                KERNEL.CloseHandle(handle)

    def _read(self):
        data = b""
        while True:
            part = os.read(self.process.stdout.fileno(), 88 - len(data))
            if not part:
                self.messages.put(None)
                return
            data += part
            if len(data) == 88:
                magic, kind, pid, code, created, reason = struct.unpack("<IIIIQ64s", data)
                self.messages.put(dict(magic=magic, kind=kind, pid=pid, code=code, created=created,
                                       reason=reason.split(b"\x00", 1)[0].decode("ascii")))
                data = b""

    def message(self):
        message = self.messages.get(timeout=10)
        if message is None:
            raise AssertionError("helper closed output before expected response")
        if message["magic"] != MAGIC:
            raise AssertionError("invalid response magic")
        return message

    def approve(self, approved):
        self.process.stdin.write(struct.pack("<I", approved)); self.process.stdin.flush()

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=10)
        self.reader.join(timeout=2)
        for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
            pipe.close()


class HelperTests(unittest.TestCase):
    def test_protocol_and_entry_gate(self):
        cases = ("success", "fragmented", "reject", "invalid_ack", "missing_ack", "EOF", "fail", "hang", "crash", "candidate")
        for mode in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix="nightcap-helper-") as temp:
                directory = Path(temp) / "client é space"
                fixture(directory, candidate=mode == "candidate")
                launch = Launch(directory, mode=mode, fragmented=mode == "fragmented")
                try:
                    first = launch.message()
                    success = mode in ("success", "fragmented")
                    if mode in ("fail", "hang", "crash", "candidate"):
                        self.assertEqual(first["kind"], 0, first)
                    else:
                        self.assertEqual(first["kind"], 1, first)
                        self.assertFalse((directory / "main-entered").exists())
                        self.assertEqual((directory / "bootstrap-ready").read_text(encoding="utf-16-le"), NONCE)
                        child = KERNEL.OpenProcess(0x100000 | 0x1000, False, first["pid"])
                        self.assertTrue(child)
                        try:
                            self.assertEqual(creation(child), first["created"])
                            self.assertEqual(KERNEL.WaitForSingleObject(child, 0), 258)
                        finally:
                            KERNEL.CloseHandle(child)
                        if mode == "EOF":
                            launch.process.stdin.close()
                        elif mode != "missing_ack":
                            launch.approve(1 if success else 2 if mode == "invalid_ack" else 0)
                        second = launch.message()
                        self.assertEqual(second["kind"], 2 if success else 0, second)
                        self.assertEqual((second["pid"], second["created"]), (first["pid"], first["created"]))
                        if success:
                            last = launch.message()
                            self.assertEqual(last["kind"], 3, last)
                            self.assertEqual(last["code"], 0, last)
                            self.assertEqual((last["pid"], last["created"]), (first["pid"], first["created"]))
                    self.assertEqual(launch.process.wait(timeout=10), 0 if success else 3)
                    self.assertEqual((directory / "main-entered").exists(), success)
                    assert_exited(self, first["pid"], first["created"])
                    if mode == "candidate":
                        reports = list(directory.glob("nightcap_health_*.json"))
                        self.assertEqual(len(reports), 1)
                        health = json.loads(reports[0].read_bytes())
                        self.assertEqual(health["reason"], "unsupported_executable")
                        self.assertEqual(health["nonce"], NONCE)
                finally:
                    launch.close()

    def test_rejects_inputs_before_process_creation(self):
        for options in ({"malformed": True}, {"partial": True}, {"nonce": None}, {"nonce": "x" * 32}):
            with self.subTest(options=options), tempfile.TemporaryDirectory(prefix="nightcap-helper-") as temp:
                directory = Path(temp) / "client"
                fixture(directory)
                launch = Launch(directory, **options)
                try:
                    message = launch.message()
                    self.assertEqual(message["kind"], 0, message)
                    self.assertEqual(message["pid"], 0, message)
                    self.assertEqual(launch.process.wait(timeout=10), 1)
                    self.assertFalse((directory / "main-entered").exists())
                finally:
                    launch.close()

    def test_channel_close_terminates_running_session(self):
        with tempfile.TemporaryDirectory(prefix="nightcap-session-") as temp:
            directory = Path(temp) / "client"
            fixture(directory)
            launch = Launch(directory, hold=True)
            try:
                child = launch.message()
                self.assertEqual(child["kind"], 1)
                launch.approve(1)
                self.assertEqual(launch.message()["kind"], 2)
                launch.process.stdin.close()
                self.assertEqual(launch.process.wait(timeout=10), 0x4e430003)
                assert_exited(self, child["pid"], child["created"])
            finally:
                launch.close()

    def test_parent_crash_terminates_owned_session(self):
        for stage in ("before", "after"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix="nightcap-parent-") as temp:
                directory = Path(temp) / "client"
                fixture(directory)
                worker = subprocess.run([sys.executable, __file__, "--parent-crash", str(directory), stage],
                    capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                self.assertEqual(worker.returncode, 0, worker.stderr)
                info = json.loads(worker.stdout)
                assert_exited(self, info["helper_pid"], info["helper_created"])
                assert_exited(self, info["child"]["pid"], info["child"]["created"])
                self.assertEqual((directory / "main-entered").exists(), stage == "after")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--parent-crash":
        directory = Path(sys.argv[2])
        launch = Launch(directory, hold=True)
        child = launch.message()
        if child["kind"] != 1:
            raise AssertionError(child)
        if sys.argv[3] == "after":
            launch.approve(1)
            if launch.message()["kind"] != 2:
                raise AssertionError("helper did not start fixture")
            deadline = time.monotonic() + 3
            while not (directory / "main-entered").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            if not (directory / "main-entered").exists():
                raise AssertionError("fixture main not reached")
        print(json.dumps(dict(helper_pid=launch.process.pid, helper_created=launch.created, child=child)), flush=True)
        os._exit(0)  # Deliberately bypass cleanup before/after health approval.
    unittest.main(verbosity=2)
