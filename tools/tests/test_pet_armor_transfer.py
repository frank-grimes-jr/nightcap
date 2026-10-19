"""Compile production transfer methods and inject each database failure point."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_gameplay_policies import ROOT, ZONE, function


class PetArmorTransfers(unittest.TestCase):
    def test_actual_transfer_methods(self):
        source = (ZONE/'pet_armor.cpp').read_text()
        bodies = '\n'.join(function(source, signature) for signature in
                           ('bool CanEquip(', 'Row FromInstance(', 'std::string Predicate(', 'bool SchemaReady()', 'bool Transfer('))
        bodies = function((ZONE/'pet_armor.h').read_text(), 'inline constexpr unsigned Capacity(') + '\n' + bodies
        fixture = (Path(__file__).parent/'pet_armor_fixture.cpp').read_text()
        # Keep cursor ranges tied to the actual server constants, not a fixture guess.
        self.assertIn('EQ::invbag::CURSOR_BAG_BEGIN', bodies)
        with tempfile.TemporaryDirectory(prefix='nightcap-pet-transfer-') as tmp:
            out = Path(tmp)
            (out/'test.cpp').write_text(fixture.replace('// ACTUAL_METHODS', bodies))
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                                       'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            run = subprocess.run([str(out/'test.exe')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            traces = {side.lower():[line[len(side)+1:] for line in run.stdout.splitlines() if line.startswith(side+':')]
                      for side in ('EQUIP','REMOVE')}
            evidence = os.environ.get('NIGHTCAP_TEST_EVIDENCE')
            if evidence:
                target = Path(evidence); target.mkdir(parents=True,exist_ok=True)
                (target/'pet-transfer-sql.json').write_text(json.dumps(traces,indent=2)+'\n')
            self.assertEqual(len(traces['equip']),12)

    def test_quarantine_and_loot_guards(self):
        client = (ZONE/'client_pet_armor.cpp').read_text()
        self.assertIn('m_pet_armor_transfer_valid = false;',client)
        self.assertIn('client_data_loaded = false;',client)
        process = (ZONE/'client_process.cpp').read_text()
        self.assertIn('if (!m_pet_armor_transfer_valid) { break; }',process)
        disconnect = function(process, 'void Client::OnDisconnect(')
        self.assertIn('if (m_pet_armor_transfer_valid) {\n\t\tClearAllProximities();', disconnect)
        self.assertIn('if (IsNightcapPetArmorSlot(i)) { continue; }',(ZONE/'loot.cpp').read_text())
        load = function((ZONE/'pet_armor.cpp').read_text(),'bool Load(')
        self.assertNotIn('SetSerialNumber',load)
        self.assertNotIn('AddGUIDToMap',load)


if __name__ == '__main__': unittest.main()
