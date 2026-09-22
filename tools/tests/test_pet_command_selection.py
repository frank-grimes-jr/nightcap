"""Compile actual server roster/selection methods with an in-memory entity list.

No zone, database, client, or network process is touched. Packet transport and
combat permission behavior remain the responsibility of native integration QA.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_gameplay_policies import ROOT, function


class PetCommandSelection(unittest.TestCase):
    def test_actual_selection_and_roster_lifecycle(self):
        source = (ROOT / "server-mods/code/zone/client_class_pets.cpp").read_text()
        signatures = (
            "void Client::UnregisterClassPet(",
            "std::vector<uint16> Client::GetExtraPetIds(",
            "void Client::RefreshClassPets(",
            "std::vector<NPC *> Client::GetCommandPets(",
            "std::vector<NPC *> Client::GetSelectedCommandPets(",
            "bool Client::SelectCommandPet(",
            "void Client::ObservePetTarget(",
        )
        for signature in signatures:
            if signature not in source:
                self.fail("Missing server command-selection behavior: " + signature)
        methods = "\n\n".join(function(source, signature) for signature in signatures)
        management = function((ROOT / "server-mods/code/zone/client_pet_armor.cpp").read_text(),
                              "void Client::HandlePetArmor(")
        # Execute the actual manage/select/order front end; the existing item
        # escrow branch below this boundary has its own transaction fixtures.
        boundary = '\tif (sep->argnum == 1 && !strcmp(sep->arg[1], "view"))'
        management = management[:management.index(boundary)] + "}\n"
        fixture = Path(__file__).with_name("pet_command_selection_fixture.cpp").read_text()
        with tempfile.TemporaryDirectory(prefix="nightcap-pet-selection-") as tmp:
            out = Path(tmp)
            (out / "test.cpp").write_text(fixture.replace("// ACTUAL_METHODS", methods)
                                         .replace("// ACTUAL_MANAGEMENT_HANDLER", management))
            (out / "build.cmd").write_text(
                '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /WX /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\n'
                'exit /b %errorlevel%\n'
            )
            build = subprocess.run(["cmd", "/d", "/c", str(out / "build.cmd")], cwd=out)
            self.assertEqual(build.returncode, 0, (out / "build.log").read_text())
            run = subprocess.run([str(out / "test.exe")], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("Pet command selection controls passed", run.stdout)


if __name__ == "__main__":
    unittest.main()
