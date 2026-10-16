"""Compile actual native duration policy, not a Python reimplementation."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_gameplay_policies import function
from test_aa_temporary_buffs import AA_FIXTURE, policy_helpers
from epic05 import load_catalog, spell_rows

ROOT = Path(__file__).resolve().parents[2]


class Epic05Native(unittest.TestCase):
    def test_real_duration_policy_bounds_only_epic_effects(self):
        source = (ROOT / 'server-mods/code/zone/spells.cpp').read_text()
        body = policy_helpers(source) + function(source, 'int32 Mob::GetBuffDurationForTarget(')
        body += '\n' + function(source, 'int CalcBuffDuration_formula(')
        header = (ROOT / 'server-mods/code/common/epic05.h').as_posix()
        fixture = AA_FIXTURE + r'''
#include "EPIC_HEADER"
struct Mob {
 bool player=true, pet=false;
 bool IsClient() const { return player; }
 bool IsPetOwnerClient() const { return pet; }
 int32 GetBuffDurationForTarget(uint16,int32) const;
};
void check(bool ok) { if (!ok) throw std::runtime_error("duration contract failed"); }
'''.replace('EPIC_HEADER', header)
        controls = r'''
int main() {
 try {
 rank(1, 60000); // Loaded catalog, unrelated to the ordinary blessing controls.
 spells[2].good_effect = 0;
 Mob player, pet, npc; pet.player=false; pet.pet=true; npc.player=false;
 for (auto target : {player, pet}) {
  for (uint16 spell=42801; spell<=42805; ++spell) {
   check(target.GetBuffDurationForTarget(spell, 3)==3);
   check(target.GetBuffDurationForTarget(spell, 600)==3);
   check(target.GetBuffDurationForTarget(spell, -1000)==3);
   check(target.GetBuffDurationForTarget(spell, 1)==1);
   check(target.GetBuffDurationForTarget(spell, 0)==0);
  }
  check(target.GetBuffDurationForTarget(1,20)==PERMANENT_BUFF_DURATION);
  check(target.GetBuffDurationForTarget(42799,20)==PERMANENT_BUFF_DURATION);
  check(target.GetBuffDurationForTarget(42806,20)==PERMANENT_BUFF_DURATION);
  check(target.GetBuffDurationForTarget(2,20)==20);
 }
 check(npc.GetBuffDurationForTarget(1,20)==20);
 std::cout << "Epic 0.5 native duration controls passed\n";
 } catch (const std::exception& error) { std::cerr << error.what(); return 1; }
}
'''
        checks = '\n'.join(f'check(CalcBuffDuration_formula(35,{r["buffdurationformula"]},{r["buffduration"]})=={r["buffduration"]});' for r in spell_rows(load_catalog()))
        controls = controls.replace('Mob player, pet, npc;', checks + '\n Mob player, pet, npc;')
        with tempfile.TemporaryDirectory(prefix='nightcap-epic05-') as folder:
            out = Path(folder)
            (out/'test.cpp').write_text(fixture + body + controls)
            if os.name == 'nt':
                (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
                build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
                self.assertEqual(build.returncode,0,(out/'build.log').read_text())
                command = [str(out/'test.exe')]
            else:
                subprocess.run(['c++','-std=c++17','test.cpp','-o','test'],cwd=out,check=True)
                command = [str(out/'test')]
            run = subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('passed',run.stdout)


if __name__ == '__main__': unittest.main()
