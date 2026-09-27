"""Compile the real cap resolver and skill advancement against controlled cap data."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_gameplay_policies import ZONE, function

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint8 = uint8_t;
using uint16 = uint16_t;
namespace EQ { namespace skills { enum SkillType { HandToHand, DualWield, Offense, Specialize, HIGHEST_SKILL=4 }; } }
struct Client {
 uint8 base=12, second=0, third=0, level=2;
 uint16 skills[5]={1,1,1,1,0};
 uint8 GetClass() const { return base; }
 uint8 GetLevel() const { return level; }
 std::vector<uint8> GetMulticlassList() const {
  std::vector<uint8> held{base}; if(second) held.push_back(second); if(third) held.push_back(third); return held;
 }
 uint16 MaxSkill(EQ::skills::SkillType skill, uint8 cls, uint8 lvl) const {
  if(skill==EQ::skills::Specialize) return cls==12 ? 200 : 0;
  if(cls==7 || cls==15) return lvl<2 ? 0 : lvl*5+5;
  return skill==EQ::skills::DualWield ? 0 : lvl*2;
 }
 CAP_DECL
 uint16 GetRawSkill(EQ::skills::SkillType s) const { return skills[s]; }
 uint16 GetMaxSkillAfterSpecializationRules(EQ::skills::SkillType s,uint16 cap) { return s==EQ::skills::Specialize ? std::min<uint16>(50,cap) : cap; }
 void SetSkill(EQ::skills::SkillType s,uint16 v) { skills[s]=v; }
 void AddSkill(EQ::skills::SkillType s,uint16 v);
};
void check(bool b,const char* m) { if(!b) throw std::runtime_error(m); }
'''
CONTROLS=r'''
int main() {
 try {
  for(int slot : {2,3}) for(int cls : {7,15}) {
   Client native, held, ordinary; native.base=cls; (slot==2?held.second:held.third)=cls;
   for(auto skill : {EQ::skills::HandToHand,EQ::skills::DualWield,EQ::skills::Offense}) {
    check(held.MaxSkill(skill)==native.MaxSkill(skill), "held combat skill cap differs from native");
    held.AddSkill(skill,1); check(held.GetRawSkill(skill)==2,"seeded skill cannot advance");
    held.AddSkill(skill,1000); check(held.GetRawSkill(skill)==native.MaxSkill(skill),"advancement must stop at held cap");
    check(held.MaxSkill(skill,12,2)==ordinary.MaxSkill(skill),"explicit primary-class cap changed");
   }
   held.AddSkill(EQ::skills::Specialize,1000); check(held.GetRawSkill(EQ::skills::Specialize)==50,"specialization cap bypassed");
   held.level=1; check(held.MaxSkill(EQ::skills::DualWield)==0,"skill unlocked before native level");
   held.level=50; native.level=50; check(held.MaxSkill(EQ::skills::HandToHand)==native.MaxSkill(EQ::skills::HandToHand),"level-up cap stale");
   held.second=held.third=0; check(held.MaxSkill(EQ::skills::DualWield)==0,"released class retains cap");
  }
  Client wizard; check(wizard.MaxSkill(EQ::skills::HandToHand)==4,"single-class cap changed");
  std::cout << "seeded skills advance to held native caps; specialization and release controls passed\n";
 } catch(const std::exception& e) { std::cerr<<e.what(); return 1; }
}
'''
class MulticlassSkillProgression(unittest.TestCase):
 def test_seeded_skill_progression(self):
  header=(ZONE/'client.h').read_text()
  source=(ZONE/'client.cpp').read_text()
  signature='uint16 Client::MaxSkill(EQ::skills::SkillType skill_id) const'
  if signature in source:
   declaration='uint16 MaxSkill(EQ::skills::SkillType skill_id) const;'
   body=function(source,signature)
  else:
   declaration=function(header,'inline uint16 MaxSkill(EQ::skills::SkillType skill_id) const')
   body=''
  body+=function(source,'void Client::AddSkill(')
  # Normal chance-based advancement and deterministic grants share this resolver.
  self.assertIn('GetMaxSkillAfterSpecializationRules(skillid, MaxSkill(skillid))',function(source,'bool Client::CheckIncreaseSkill('))
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)
   (out/'test.cpp').write_text(FIXTURE.replace('CAP_DECL',declaration)+body+CONTROLS)
   (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
   built=subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
   self.assertEqual(built.returncode,0,(out/'build.log').read_text())
   run=subprocess.run([str(out/'test.exe')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)

if __name__=='__main__': unittest.main()
