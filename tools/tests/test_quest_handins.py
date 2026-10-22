"""Compile the actual NPC hand-in method, not a reimplementation of its allocator."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class QuestHandins(unittest.TestCase):
    def compile_run(self, fixture):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cpp, binary = folder / 'test.cpp', folder / ('test.exe' if os.name == 'nt' else 'test')
            cpp.write_text(fixture)
            if os.name == 'nt':
                script = folder / 'build.cmd'
                script.write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                                  'cl /nologo /EHsc /std:c++20 test.cpp /Fe:test.exe\nexit /b %errorlevel%\n')
                command = ['cmd', '/d', '/c', str(script)]
            else:
                command = [os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', str(cpp), '-o', str(binary)]
            build = subprocess.run(command, cwd=folder, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            print(result.stdout.strip())

    def test_actual_native_handins(self):
        source = (ROOT / 'server-mods/code/zone/npc.cpp').read_text()
        method = source[source.index('bool NPC::CheckHandin('):source.index('void NPC::ResetHandin(')]
        header = (ROOT / 'server-mods/code/zone/npc.h').read_text()
        structs = header[header.index('\tstruct HandinEntry {'):header.index('\t// NPC Hand-in')]
        fixture = (ROOT / 'tools/tests/fixtures/quest_handins.cpp').read_text()
        fixture = fixture.replace('// HANDIN_STRUCTS', structs).replace('// CHECK_HANDIN_METHOD', method)
        policy = ROOT / 'server-mods/code/common/quest_item_policy.h'
        if policy.exists():
            fixture = '#include "' + policy.as_posix() + '"\n' + fixture
        self.compile_run(fixture)

    def test_actual_task_delivery_filter(self):
        source = (ROOT / 'server-mods/code/zone/task_client_state.cpp').read_text()
        method = source[source.index('bool ClientTaskState::CanUpdate('):source.index('int ClientTaskState::UpdateTasks(')]
        fixture = (ROOT / 'tools/tests/fixtures/quest_delivery.cpp').read_text().replace('// CAN_UPDATE_METHOD', method)
        policy = ROOT / 'server-mods/code/common/quest_item_policy.h'
        self.compile_run('#include "' + policy.as_posix() + '"\n' + fixture)


if __name__ == '__main__':
    unittest.main()
