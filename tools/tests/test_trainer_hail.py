"""Compile the actual hail/open methods; transport and cap storage are fixtures."""
import subprocess
import os
import tempfile
import unittest
from pathlib import Path

from test_gameplay_policies import ROOT, ZONE, function

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
#ifdef _WIN32
#define strcasecmp _stricmp
#define strncasecmp _strnicmp
#else
#include <strings.h>
#endif
using uint8 = uint8_t; using uint16 = uint16_t; using uint32 = uint32_t;
using uchar = unsigned char;
namespace Class { enum { Warrior=1, WarriorGM=20, BerserkerGM=35, Berserker=16, PLAYER_CLASS_COUNT=16 }; }
bool IsPlayerClass(int cls) { return cls >= 1 && cls <= 16; }
namespace Race { enum { Gnome=12 }; }
namespace EQ { namespace skills { enum SkillType { Skill1HBlunt, SkillTinkering,
 Skill1HPiercing, Skill2HPiercing, HIGHEST_SKILL=4 }; }
namespace versions { enum class ClientVersion { RoF2=1 }; } }
bool cross_class=false;
#define RuleB(category,name) cross_class
constexpr int USE_NPC_RANGE2=10000, OP_GMTraining=1;
struct Pos { int x=0; };
int DistanceSquared(Pos a,Pos b) { return (a.x-b.x)*(a.x-b.x); }
struct GMTrainee_Struct { uint32 npcid,playerid,skills[100]; uint8 unknown408[40]; };
int alive_packets=0;
struct EQApplicationPacket {
 unsigned size; uchar* pBuffer;
 EQApplicationPacket(int,unsigned n):size(n),pBuffer(new uchar[n]{}) { ++alive_packets; }
 ~EQApplicationPacket() { delete[] pBuffer; --alive_packets; }
 EQApplicationPacket* Copy() const { auto p=new EQApplicationPacket(1,size); memcpy(p->pBuffer,pBuffer,size); return p; }
};
#define safe_delete(p) do { delete p; p=nullptr; } while(0)
struct NPC {
 int cls=26; bool npc=true,engaged=false; Pos position; unsigned id=99;
 bool IsNPC() const { return npc; } bool IsEngaged() const { return engaged; }
 int GetClass() const { return cls; } unsigned GetID() const { return id; }
 Pos GetPosition() const { return position; } NPC* CastToNPC() { return this; }
 void SayString(int,const char*) {}
};
using Mob=NPC;
struct { NPC* target=nullptr; NPC* GetMob(unsigned id) { return target && target->id==id ? target : nullptr; } } entity_list;
struct Random { int Int(int a,int) { return a; } };
struct Zone { Random random; } zone_value;
Zone* zone=&zone_value;
struct SkillCaps { static bool CanUseTrainer(uint8,const std::vector<uint8>&,bool); };
struct Client {
 Pos m_Position; std::vector<uint8> held{3,7,1}; bool invisible=false;
 unsigned opens=0; GMTrainee_Struct last{};
 unsigned GetID() const { return 42; } int GetClass() const { return 3; }
 int GetLevel() const { return 3; } int GetRace() const { return 1; }
 bool IsInvisible(NPC*) const { return invisible; }
 const char* GetCleanName() const { return "Palwar"; }
 std::vector<uint8> GetMulticlassList() const { return held; }
 EQ::versions::ClientVersion ClientVersion() const { return EQ::versions::ClientVersion::RoF2; }
 uint16 MaxSkill(EQ::skills::SkillType,int cls,int level) const { return cls==7 ? level*5 : level; }
 uint16 GetMaxSkillAfterSpecializationRules(EQ::skills::SkillType,uint16 cap) const { return cap; }
 void FastQueuePacket(EQApplicationPacket** p) { ++opens; memcpy(&last,(*p)->pBuffer,sizeof last); safe_delete(*p); }
 void CheckTrainerHail(NPC*,const char*);
 void OPGMTraining(const EQApplicationPacket*);
};
void check(bool ok,const char* why) { if(!ok) throw std::runtime_error(why); }
'''

CONTROLS = r'''
int main() {
 try {
  NPC joren; Client palwar; entity_list.target=&joren;
  for(const char* text : {"Hail, Joren", "hail", "HAIL, Joren"}) {
   unsigned before=palwar.opens; palwar.CheckTrainerHail(&joren,text);
   check(palwar.opens==before+1,"held Monk trainer hail must open");
   check(palwar.last.npcid==99 && palwar.last.playerid==42,"wrong trainer/player identity");
   check(palwar.last.skills[0]==15,"must show current held-class cap");
   check(palwar.last.skills[1]==0,"non-Gnome tinkering exposed");
  }
  for(int cls : {20,22,26}) { joren.cls=cls; auto n=palwar.opens; palwar.CheckTrainerHail(&joren,"hail"); check(palwar.opens==n+1,"held class denied"); }
  unsigned before=palwar.opens;
  for(const char* text : {"", "hello", "hailstorm", "training", "hailstone, Joren"}) palwar.CheckTrainerHail(&joren,text);
  palwar.CheckTrainerHail(nullptr,"hail"); palwar.CheckTrainerHail(&joren,nullptr);
  check(palwar.opens==before,"non-hail opened training");
  for(int cls : {1,19,21,35,36,41}) { joren.cls=cls; palwar.CheckTrainerHail(&joren,"hail"); }
  check(palwar.opens==before,"non-held or non-trainer opened");
  joren.cls=26; joren.position.x=101; palwar.CheckTrainerHail(&joren,"hail");
  check(palwar.opens==before,"remote trainer opened"); joren.position.x=0;
  joren.engaged=true; palwar.CheckTrainerHail(&joren,"hail"); joren.engaged=false;
  palwar.invisible=true; palwar.CheckTrainerHail(&joren,"hail"); palwar.invisible=false;
  check(palwar.opens==before,"engaged/invisible hail opened");
  palwar.held={3,1}; palwar.CheckTrainerHail(&joren,"hail");
  check(palwar.opens==before,"released Monk still authorized");
  cross_class=true; palwar.CheckTrainerHail(&joren,"hail");
  check(palwar.opens==before+1,"existing cross-class rule ignored"); cross_class=false;
  // Untrusted/stale ordinary open packets must not leak their copied packet.
  EQApplicationPacket request(OP_GMTraining,sizeof(GMTrainee_Struct));
  auto data=reinterpret_cast<GMTrainee_Struct*>(request.pBuffer); data->npcid=99;
  entity_list.target=nullptr; palwar.OPGMTraining(&request);
  check(alive_packets==1,"missing trainer leaks packet");
  entity_list.target=&joren; joren.cls=41; palwar.OPGMTraining(&request);
  check(alive_packets==1,"non-trainer leaks packet");
  std::cout << "Trainer hail, authorization, cap and packet lifetime controls passed\n";
 } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
'''


class TrainerHailTests(unittest.TestCase):
    def test_native_hail_and_open(self):
        source = (ZONE / "client_process.cpp").read_text()
        code = FIXTURE + function((ROOT / "server-mods/code/common/skill_caps.cpp").read_text(),
                                  "bool SkillCaps::CanUseTrainer(")
        code += function(source, "void Client::CheckTrainerHail(")
        code += function(source, "void Client::OPGMTraining(") + CONTROLS
        with tempfile.TemporaryDirectory(prefix="trainer-hail-") as directory:
            path = Path(directory)
            (path / "test.cpp").write_text(code)
            if os.name == "nt":
                (path / "build.cmd").write_text(
                    '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul\n'
                    'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe\n')
                build = subprocess.run(["cmd", "/d", "/c", str(path / "build.cmd")],
                                       cwd=path, capture_output=True, text=True)
            else:
                build = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", str(path / "test.cpp"),
                                        "-o", str(path / "test.exe")], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(path / "test.exe")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            print(result.stdout.strip())

    def test_say_dispatch_calls_hail_after_quest(self):
        source = (ZONE / "client.cpp").read_text()
        start = source.index("CheckEmoteHail(t->CastToNPC(), message);")
        self.assertIn("CheckTrainerHail(t->CastToNPC(), message);", source[start:start + 250])
        self.assertIn("void CheckTrainerHail(NPC* trainer, const char* message);", (ZONE / "client.h").read_text())


if __name__ == "__main__":
    unittest.main()
