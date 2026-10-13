"""Compile actual skill methods from the repository or a retained source tree.

Use --source-root PATH containing zone/client.h, client.cpp and mob.cpp (and
attack.cpp when the dual-wield method calls GetHandToHandClass).
Cap rows are a small explicit fixture; no database, server or client is modified.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_gameplay_policies import ROOT, function

SOURCE_ROOT = ROOT / "server-mods/code"

FIXTURE = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using int16=int16_t;
namespace EQ {
namespace skills { enum SkillType { Skill1HPiercing=36, Skill2HPiercing=77, SkillDualWield=22, SkillKick=30, SkillHandtoHand=28, SkillOffense=33, SkillSpecialize=43, HIGHEST_SKILL=77 }; }
namespace versions { enum class ClientVersion { RoF2 }; }
namespace invslot { enum { slotPrimary,slotSecondary }; }
struct ItemData { bool two=false; bool IsType2HWeapon() const { return two; } };
struct ItemInstance { bool weapon=true; ItemData data; bool IsWeapon() const { return weapon; } const ItemData* GetItem() const { return &data; } };
}
namespace Class { enum { Warrior=1, Paladin=3, Monk=7, Beastlord=15, Berserker=16, MonkGM=26, BeastlordGM=34 }; }
namespace SpecialAbility { enum { AggroImmunity,ClientAggroImmunity }; }
namespace ConsiderColor { enum { Gray,White }; }
enum { EVENT_USE_SKILL,EVENT_SKILL_UP };
namespace fmt { template<class... T> std::string format(const char*,T...) { return "fixture"; } }
#define LogSkills(...) ((void)0)
enum Rule { SkillUpMaximumChancePercentage,SkillUpMinimumChancePercentage,SkillUpModifier,MaxLevel };
int rule(Rule r) { return r==MaxLevel ? 50 : 100; }
#define RuleI(category,name) rule(name)
struct SkillCaps {
 struct Row { uint16 cap; };
 static SkillCaps* Instance() { static SkillCaps value; return &value; }
 Row GetSkillCap(uint8 cls, EQ::skills::SkillType skill,uint8 level) {
  using namespace EQ::skills;
  if(skill==SkillSpecialize) return {uint16(cls==12 ? 200 : 0)};
  // Preserve the previous test's dated native Monk/Beastlord/Wizard cap matrix.
  const uint16 caps[3][3][3]={{{10,20,270},{12,19,252},{5,10,230}},{{10,20,250},{0,0,210},{5,10,200}},{{3,6,150},{0,0,0},{4,8,140}}};
  int c=cls==7?0:cls==15?1:cls==12?2:-1;
  int s=skill==SkillHandtoHand?0:skill==SkillDualWield?1:skill==SkillOffense?2:-1;
  int l=level==1?0:level==2?1:level==50?2:-1;
  if(c>=0 && s>=0 && l>=0)return {caps[c][s][l]};
  if(cls==Class::Monk && level>=1 && skill==EQ::skills::SkillDualWield) return {uint16(level==6 ? 47 : level>=7 ? 52 : 22)};
  if(cls==Class::Monk && level>=1 && skill==EQ::skills::SkillKick) return {uint16(level*5)};
  if(cls==Class::Warrior && skill==EQ::skills::SkillKick) return {uint16(level*4)};
  if(cls==Class::Warrior && level>=15 && skill==EQ::skills::SkillDualWield) return {uint16(level*5)};
  return {0};
 }
};
namespace PlayerEvent { enum { SKILL_UP }; struct SkillUpEvent { uint32 skill_id;int value;int16 max_skill;const char* against_who; }; }
struct PlayerEventLogs { static PlayerEventLogs* Instance() { static PlayerEventLogs p;return &p; } bool IsEventEnabled(int) {return false;} };
struct Parser { bool PlayerHasQuestSub(int) {return false;} template<class... T> void EventPlayer(T...) {} } parser;
auto* parse=&parser;
struct Zone { struct Random { double Real(int,int) {return 0;} } random; } zone_value;
auto* zone=&zone_value;
struct Client;
struct Mob {
 uint8 class_=Class::Paladin,level=6;bool player=true,corpse=false,immune=false;
 virtual ~Mob()=default;
 virtual uint16 GetSkill(EQ::skills::SkillType) const {return 0;}
 bool IsClient() const {return player;} bool IsCorpse() const {return corpse;}
 bool GetSpecialAbility(int) const {return immune;} uint8 GetLevel() const {return level;}
 uint8 GetClass() const {return class_;}
 const char* GetCleanName() const {return "fixture";}
 const Client* CastToClient() const;
 uint8 GetHandToHandClass() const;
 bool CanThisClassDualWield() const;
};
struct Inventory { const EQ::ItemInstance* primary=nullptr;const EQ::ItemInstance* secondary=nullptr;
 const EQ::ItemInstance* GetItem(int slot) const {return slot==EQ::invslot::slotPrimary?primary:secondary;} };
struct Client:Mob {
 std::vector<uint8> held{3,1,7};
 struct Profile { uint16 skills[100]={}; } m_pp;
 struct Bonuses { int skillmod[100]={},skillmodmax[100]={}; } itembonuses;
 Inventory inventory;bool dead=false,unconscious=false,ai=false;int saves=0;
 uint8 GetClass() const {return class_;}
 auto ClientVersion() const {return EQ::versions::ClientVersion::RoF2;}
 auto GetMulticlassList() const {return held;}
 bool IsMulticlassMember(uint8 cls) const {return std::find(held.begin(),held.end(),cls)!=held.end();}
 const Inventory& GetInv() const {return inventory;}
 uint16 GetRawSkill(EQ::skills::SkillType s) const {return m_pp.skills[s];}
 uint16 GetMaxSkillAfterSpecializationRules(EQ::skills::SkillType s,uint16 cap) const {return s==EQ::skills::SkillSpecialize?std::min<uint16>(50,cap):cap;}
 void SetSkill(EQ::skills::SkillType s,uint16 value) {m_pp.skills[s]=value;++saves;}
 bool IsDead() const {return dead;} bool IsUnconscious() const {return unconscious;} bool IsAIControlled() const {return ai;}
 int GetLevelCon(uint8 other) const {return other+5<level?ConsiderColor::Gray:ConsiderColor::White;}
 template<class... T> void RecordPlayerEventLog(T...) {}
 uint16 MaxSkill(EQ::skills::SkillType) const;
 uint16 MaxSkill(EQ::skills::SkillType,uint8,uint8) const;
 uint16 GetSkill(EQ::skills::SkillType) const override;
 bool CanHaveSkill(EQ::skills::SkillType) const;
 bool HasSkill(EQ::skills::SkillType) const;
 bool CheckIncreaseSkill(EQ::skills::SkillType,Mob*,int);
 void AddSkill(EQ::skills::SkillType,uint16);
};
const Client* Mob::CastToClient() const {return static_cast<const Client*>(this);}
void check(bool ok,const char* why) {if(!ok)throw std::runtime_error(why);}
'''

CONTROLS = r'''
int main(int argc,char** argv) {
 try {
  check(argc==2,"scenario required");std::string scenario=argv[1];Client p;
  using namespace EQ::skills;
  p.m_pp.skills[SkillDualWield]=1;p.m_pp.skills[SkillKick]=1;
  if(scenario=="caps") {
   check(p.MaxSkill(SkillDualWield)==47,"Palwar held Monk Dual Wield cap must be47 at6");
   check(p.MaxSkill(SkillKick)==30,"Palwar held Monk Kick cap must be30 at6");
   p.level=7;check(p.MaxSkill(SkillDualWield)==52,"current level selects cap");
  } else if(scenario=="advance") {
   for(auto skill:{SkillDualWield,SkillKick}) {
    check(p.CheckIncreaseSkill(skill,nullptr,0),"eligible held skill failed deterministic skill-up roll");
    check(p.GetRawSkill(skill)==2,"successful skill-up must add exactly one");
    p.m_pp.skills[skill]=p.MaxSkill(skill);
    check(!p.CheckIncreaseSkill(skill,nullptr,0),"skill advanced beyond current cap");
   }
  } else if(scenario=="add") {
   p.AddSkill(SkillKick,1);check(p.GetRawSkill(SkillKick)==2,"AddSkill must not clamp held Kick to primary zero");
   p.AddSkill(SkillDualWield,100);check(p.GetRawSkill(SkillDualWield)==47,"AddSkill must clamp to held current cap");
  } else if(scenario=="raw") {
   check(p.GetSkill(SkillDualWield)==1 && p.GetSkill(SkillKick)==1,"saved earned skill must remain visible");
   check(p.HasSkill(SkillDualWield),"held saved DW1 must satisfy native HasSkill");
   p.itembonuses.skillmod[SkillKick]=100;check(p.GetSkill(SkillKick)==2,"item skill bonus preserved");
   check(p.saves==0,"cap/access queries must never write earned skills");
  } else if(scenario=="fists") {
   check(p.CanThisClassDualWield(),"held Monk with earned DW1 can use empty fists");
  } else if(scenario=="weapons") {
   EQ::ItemInstance weapon,shield,two;shield.weapon=false;two.data.two=true;
   p.inventory.primary=&weapon;p.inventory.secondary=&weapon;
   check(p.CanThisClassDualWield(),"two one-handed weapons eligible");
   p.inventory.primary=&two;check(!p.CanThisClassDualWield(),"two-handed primary must deny offhand");
   p.inventory.primary=&weapon;p.inventory.secondary=&shield;check(!p.CanThisClassDualWield(),"shield must deny offhand");
   p.inventory.secondary=&weapon;p.m_pp.skills[SkillDualWield]=0;
   check(!p.CanThisClassDualWield(),"unearned DW must not grant offhand");
  } else if(scenario=="membership") {
   p.held={3};check(!p.HasSkill(SkillKick) && !p.CanThisClassDualWield(),"released classes cannot retain access");
   check(!p.CheckIncreaseSkill(SkillKick,nullptr,0),"unheld skill cannot advance");
   p.held={3,1};check(p.MaxSkill(SkillDualWield)==0,"Warrior DW is level locked at6");
   check(!p.CheckIncreaseSkill(SkillDualWield,nullptr,0),"future Warrior DW cannot advance");
   p.held={7};p.class_=7;check(p.MaxSkill(SkillDualWield)==47,"primary Monk control");
   check(p.CheckIncreaseSkill(SkillDualWield,nullptr,0),"primary Monk advancement control");
  } else if(scenario=="legacy_caps") {
   for(int slot:{2,3})for(uint8 cls:{7,15}) {
    Client native,held,ordinary;native.class_=cls;native.held={cls};
    held.class_=ordinary.class_=12;ordinary.held={12};held.held=slot==2?std::vector<uint8>{12,cls,0}:std::vector<uint8>{12,0,cls};
    native.level=held.level=ordinary.level=cls==7?2:50;
    for(auto skill:{SkillHandtoHand,SkillDualWield,SkillOffense}) {
     held.m_pp.skills[skill]=1;
     check(held.MaxSkill(skill)==native.MaxSkill(skill),"held combat cap differs from native");
     held.AddSkill(skill,1);check(held.GetRawSkill(skill)==2,"legacy seeded skill cannot advance");
     held.AddSkill(skill,1000);check(held.GetRawSkill(skill)==native.MaxSkill(skill),"legacy cap not enforced");
     check(held.MaxSkill(skill,12,held.level)==ordinary.MaxSkill(skill),"explicit primary cap changed");
    }
    held.AddSkill(SkillSpecialize,1000);check(held.GetRawSkill(SkillSpecialize)==50,"specialization bypassed");
    held.level=native.level=1;check(held.MaxSkill(SkillDualWield)==native.MaxSkill(SkillDualWield),"level1 unlock differs");
    if(cls==15){held.level=2;check(held.MaxSkill(SkillDualWield)==0,"early Beastlord DW");}
    held.level=native.level=50;check(held.MaxSkill(SkillHandtoHand)==native.MaxSkill(SkillHandtoHand),"level-up stale");
    held.held={12};check(held.MaxSkill(SkillDualWield)==0,"released class retains cap");
   }
   Client wizard;wizard.class_=12;wizard.held={12};wizard.level=2;
   check(wizard.MaxSkill(SkillHandtoHand)==6,"single-class cap changed");
  } else if(scenario=="guards") {
   p.held={7};p.class_=7;
   p.dead=true;check(!p.CheckIncreaseSkill(SkillKick,nullptr,0),"dead character gained");p.dead=false;
   p.ai=true;check(!p.CheckIncreaseSkill(SkillKick,nullptr,0),"charmed character gained");p.ai=false;
   Mob target;target.player=false;target.corpse=true;check(!p.CheckIncreaseSkill(SkillKick,&target,0),"corpse gained");target.corpse=false;
   target.immune=true;check(!p.CheckIncreaseSkill(SkillKick,&target,0),"immune target gained");target.immune=false;
   check(p.CheckIncreaseSkill(SkillKick,&target,0),"legal target control");
  } else throw std::runtime_error("unknown scenario");
  std::cout<<"PASS: "<<scenario<<'\n';
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''


class SkillProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = (SOURCE_ROOT / "zone/client.cpp").read_text()
        header = (SOURCE_ROOT / "zone/client.h").read_text()
        mob = (SOURCE_ROOT / "zone/mob.cpp").read_text()
        signature = "uint16 Client::MaxSkill(EQ::skills::SkillType skill_id) const"
        if signature in client:
            cap = function(client, signature)
        else:
            cap = function(header, "inline uint16 MaxSkill(EQ::skills::SkillType skill_id) const")
            cap = cap.replace("inline uint16 MaxSkill", "uint16 Client::MaxSkill", 1)
        code = FIXTURE + cap
        for signature in (
            "uint16 Client::MaxSkill(EQ::skills::SkillType skill_id,",
            "uint16 Client::GetSkill(", "bool Client::CanHaveSkill(",
            "bool Client::HasSkill(", "bool Client::CheckIncreaseSkill(", "void Client::AddSkill(",
        ):
            code += function(client, signature)
        dual_wield = function(mob, "bool Mob::CanThisClassDualWield(")
        if "GetHandToHandClass()" in dual_wield:
            attack = (SOURCE_ROOT / "zone/attack.cpp").read_text()
            code += function(attack, "uint8 Mob::GetHandToHandClass(")
        code += dual_wield + CONTROLS
        cls.temp = tempfile.TemporaryDirectory(prefix="multiclass-progression-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        (path / "test.cpp").write_text(code)
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul\n'
                'cl /nologo /EHsc /W4 /std:c++20 test.cpp /Fe:test.exe\n')
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["g++", "-std=c++20", "-Wall", "-Wextra", "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_native_skill_progression(self):
        for scenario in ("caps", "advance", "add", "raw", "fists", "weapons", "membership", "guards", "legacy_caps"):
            with self.subTest(scenario=scenario):
                result = subprocess.run([self.binary, scenario], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                print(result.stdout.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.source_root:
        SOURCE_ROOT = args.source_root
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
