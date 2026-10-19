"""Execute the real client equipment parser and native transfer contract."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def compile_run(source):
    with tempfile.TemporaryDirectory(prefix='nightcap-equipment-', ignore_cleanup_errors=True) as tmp:
        out = Path(tmp)
        (out / 'test.cpp').write_text(source)
        (out / 'build.cmd').write_text(
            '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
            'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
        build = subprocess.run(['cmd', '/d', '/c', str(out / 'build.cmd')], cwd=out)
        if build.returncode:
            raise AssertionError((out / 'build.log').read_text())
        run = subprocess.run([str(out / 'test.exe')], capture_output=True, text=True)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)


class PetEquipment(unittest.TestCase):
    def test_complete_snapshot_and_paged_commands(self):
        header = (ROOT / 'eq-client-dll/src/pet_state.h').as_posix()
        compile_run(f'#include "{header}"\n' + r'''
#include <iostream>
#include <stdexcept>
void require(bool ok, const char *why) { if (!ok) throw std::runtime_error(why); }
int main() { try {
    nightcap::PetState state;
    require(!state.Consume("[NCPA1]B|1|22|202|0|7|54657374"), "accepted old partial protocol");
    require(state.Consume("[NCPA2]B|1|22|202|0|7|54657374"), "new snapshot rejected");
    require(state.Consume("[NCPA2]P|1|13|12|506574"), "pet rejected");
    for (int i = 0; i < 22; ++i) {
        if (i == 8) require(!state.Consume("[NCPA2]E|1"), "published first page only");
        auto frame = "[NCPA2]I|1|13|" + std::to_string(i) + "|0|456d707479";
        require(state.Consume(frame.c_str()), "equipment location rejected");
    }
    require(!state.Consume("[NCPA2]I|1|13|21|0|456d707479"), "duplicate accepted");
    require(!state.Consume("[NCPA2]I|1|13|22|0|456d707479"), "out of bounds accepted");
    require(state.Consume("[NCPA2]E|1"), "complete snapshot rejected");
    require(state.Command("equip", 0) == "#nightcappet equip 13 0 1", "first-page slot");
    state.NextPage(1);
    require(state.Command("equip", 0) == "#nightcappet equip 13 8 1", "second-page slot");
    state.NextPage(1);
    require(state.Command("equip", 5) == "#nightcappet equip 13 21 1", "last slot");
    require(state.Command("equip", 6).empty(), "unused row issued command");
    state.NextPage(1);
    require(state.Command("equip", 0) == "#nightcappet equip 13 0 1", "page wrap");
    state.Clear();
    require(state.Command("equip", 0).empty(), "stale identity issued command");
    return 0;
} catch (const std::exception &e) { std::cerr << e.what(); return 1; } }
''')


if __name__ == '__main__':
    unittest.main()
