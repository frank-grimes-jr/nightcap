"""Compile the actual combat entry points against controlled engine boundaries.

The timers use a deterministic clock; damage and skill-cap lookup are fixtures.
The native entry points and Monk authorization policy are extracted unchanged.
No database, installed client, running server, or player state is touched.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_gameplay_policies import ROOT, function


SOURCE = ROOT / "server-mods/code"

FIXTURE = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t;
using int16=int16_t; using int64=int64_t; using uint64=uint64_t; using pTimerType=uint16;
/* NATIVE_TIMER_ENUM */
namespace Class { enum { Warrior=1,Paladin=3,Ranger=4,ShadowKnight=5,Monk=7,Bard=8,Rogue=9,Wizard=12,Beastlord=15,Berserker=16 }; }
namespace Race { enum { Ogre=10,Troll=9,Barbarian=2 }; }
namespace Chat { enum { Red=13 }; }
namespace EQ {
namespace skills {
enum SkillType { SkillArchery=7,SkillBackstab=8,SkillBash=10,SkillDragonPunch=21,
 SkillEagleStrike=23,SkillFlyingKick=26,SkillKick=30,SkillRoundKick=38,
 SkillThrowing=51,SkillTigerClaw=52,SkillFrenzy=74 };
bool CanUseMonkCombatAbility(const std::vector<uint8>&,SkillType,uint16);
}
namespace versions { enum class ClientVersion { UF,RoF2 }; }
namespace invslot { enum { slotPrimary,slotSecondary,slotFeet,slotShoulders,slotRange }; }
struct ItemInstance {};
template<class T> T Clamp(T value,T low,T high) {return std::max(low,std::min(high,value));}
}
namespace fmt {template<class... T> std::string format(const char* s,T...) {return s;}}
template<class... T> std::string StringFormat(const char* s,T...) {return s;}
enum { BashReuseTime=5,
 FrenzyReuseTime=10,KickReuseTime=10,BackstabReuseTime=10,
 animTailRake,anim1HWeapon,animKick,DMG_INVULNERABLE=-5 };
#define RuleI(category,name) 0
#define RuleB(category,name) false
uint32 GetPlayerClassBit(uint8 cls) {return 1u<<(cls-1);}
int database;
struct PersistentTimers {
 uint64 now=1000;
 std::map<pTimerType,uint64> deadlines;
 std::map<pTimerType,uint32> durations;
 bool Expired(int*,pTimerType timer,bool) const {
  auto it=deadlines.find(timer);return it==deadlines.end() || it->second<=now;
 }
 // Match PTimerList::Start's unsigned API, which exposes signed underflow at
 // the caller. A wide deterministic clock preserves the native elapsed-time
 // expiry semantics without wrapping the fixture's absolute deadline.
 void Start(pTimerType timer,uint32 duration) {
  durations[timer]=duration;deadlines[timer]=now+duration;
 }
};
struct Zone {struct Random {bool Roll(int) {return false;} int Roll0(int) {return 450;} int Int(int,int) {return 0;}} random;} zone_value;
auto* zone=&zone_value;
struct CombatAbility_Struct {uint32 m_target=44,m_atk=100,m_skill=0;};
struct Mob {uint32 id=44;uint32 GetID() const {return id;}};
struct Inventory {const EQ::ItemInstance* GetItem(int) const {return nullptr;}};
struct Client:Mob {
 Mob enemy;Mob* target=&enemy;Inventory inventory;PersistentTimers p_timers;
 struct Timer {bool enabled=false;bool Enabled() const {return enabled;}} spellend_timer;
 struct Bonuses {int DoubleSpecialAttack=0;} itembonuses,spellbonuses,aabonuses;
 uint8 class_id=Class::Monk,level=50;std::vector<uint8> held{Class::Monk};
 bool dead=false,feared=false,stunned=false,mezzed=false,aura=false,allowed=true,in_range=true;
 EQ::versions::ClientVersion version=EQ::versions::ClientVersion::RoF2;
 int haste=0,reduction=0,rejections=0;
 std::vector<int> attacks;
 Mob* GetTarget() const {return target;}
 uint8 GetClass() const {return class_id;} uint8 GetLevel() const {return level;}
 auto ClientVersion() const {return version;} auto GetMulticlassList() const {return held;}
 bool IsMulticlassMember(uint8 cls) const {return std::find(held.begin(),held.end(),cls)!=held.end();}
 bool IsFeared() const {return feared;} bool IsStunned() const {return stunned;}
 bool IsMezzed() const {return mezzed;} bool DivineAura() const {return aura;}
 int GetRace() const {return 1;}
 uint16 MaxSkill(EQ::skills::SkillType skill,uint8 cls,uint8 at_level) const {
  using namespace EQ::skills;
  int unlock=skill==SkillKick?1:skill==SkillRoundKick?5:skill==SkillTigerClaw?10:
   skill==SkillEagleStrike?20:skill==SkillDragonPunch?25:skill==SkillFlyingKick?30:0;
  if(cls==Class::Monk && unlock && at_level>=unlock)return 200;
  if(cls==Class::Warrior && skill==SkillKick)return 200;
  if(cls==Class::Paladin && skill==SkillBash)return 200;
  if(cls==Class::Berserker && skill==SkillFrenzy)return 200;
  return 0;
 }
 bool IsAttackAllowed(Mob*) const {return allowed;} bool CombatRange(Mob*) const {return in_range;}
 int GetHaste() const {return haste;} int16 GetSkillReuseTime(int) const {return reduction;}
 const Inventory& GetInv() const {return inventory;}
 int GetWeaponDamage(Mob*,const EQ::ItemInstance*) const {return 1;}
 int GetBaseSkillDamage(EQ::skills::SkillType,Mob*) const {return 10;}
 int GetSkill(EQ::skills::SkillType) const {return 100;}
 void SetAttackTimer() {} void ThrowingAttack(Mob*,bool=false) {}
 bool RangedAttack(Mob*,bool=false) {return true;} bool CheckDoubleRangedAttack() const {return false;}
 template<class... T> void DoAnim(T...) {} template<class... T> void CheckIncreaseSkill(T...) {}
 template<class... T> void SendColoredText(T...) {}
 template<class... T> void Message(T...) {++rejections;}
 void DoSpecialAttackDamage(Mob*,EQ::skills::SkillType skill,int64,int,int,int) {attacks.push_back(skill);}
 int MonkSpecialAttack(Mob*,uint8 skill) {attacks.push_back(skill);return 10;}
 void TryBackstab(Mob*,int) {attacks.push_back(EQ::skills::SkillBackstab);}
 void OPCombatAbility(const CombatAbility_Struct*);
 void DoClassAttacks(Mob*,uint16,bool);
 void Packet(int skill) {CombatAbility_Struct ca{44,100,uint32(skill)};OPCombatAbility(&ca);}
};
void check(bool ok,const std::string& why) {if(!ok)throw std::runtime_error(why);}
const std::array<int,6> monk_skills={EQ::skills::SkillKick,EQ::skills::SkillRoundKick,
 EQ::skills::SkillTigerClaw,EQ::skills::SkillEagleStrike,EQ::skills::SkillDragonPunch,EQ::skills::SkillFlyingKick};
'''

CONTROLS = r'''
void pairwise(const std::string& path) {
 int failures=0,cases=0;
 for(int first:monk_skills)for(int second:monk_skills) {
  if(first==second)continue;
  for(auto held:{std::vector<uint8>{7},std::vector<uint8>{12,7},std::vector<uint8>{12,1,7}}) {
   Client c;c.held=held;c.class_id=held[0];c.haste=100;
   if(path=="packet")c.Packet(first);else c.DoClassAttacks(c.GetTarget(),first,false);
   check(!c.attacks.empty(),"first valid attack was not executed");
   auto before=c.attacks.size();
   if(path=="packet")c.Packet(second);else c.DoClassAttacks(c.GetTarget(),second,false);
   ++cases;
   if(c.attacks.size()==before || c.attacks.back()!=second) {
    ++failures;std::cerr<<path<<" skill "<<first<<" incorrectly blocks "<<second<<" with primary class "<<int(held[0])<<'\n';
   }
  }
 }
 check(failures==0,std::to_string(failures)+" of "+std::to_string(cases)+" ordered independent cooldown cases failed");
}
void same_skill(const std::string& path) {
 for(int skill:monk_skills) {
  Client c;c.haste=100;
  auto attack=[&](){if(path=="packet")c.Packet(skill);else c.DoClassAttacks(c.GetTarget(),skill,false);};
  attack();auto first=c.attacks.size();check(first>0,"valid attack missing");
  attack();check(c.attacks.size()==first,"same skill bypassed active cooldown");
  c.p_timers.now+=path=="packet"?3:8;attack();
  check(c.attacks.size()==first,"same skill became ready before its deadline");
  ++c.p_timers.now;attack();check(c.attacks.size()>first,"same skill failed at exact recovery deadline");
 }
}
void packet_guards() {
 for(int skill:monk_skills) {
  for(auto held:{std::vector<uint8>{7},std::vector<uint8>{12,7},std::vector<uint8>{12,1,7}}) {
   Client valid;valid.held=held;valid.class_id=held[0];valid.Packet(skill);
   check(valid.attacks.size()==1,"current-level held Monk authorization rejected");
  }
  for(int guard=0;guard<11;++guard) {
   Client c;
   if(guard==0)c.target=nullptr;
   if(guard==1)c.enemy.id=45;
   if(guard==2)c.allowed=false;
   if(guard==3)c.in_range=false;
   if(guard==4)c.spellend_timer.enabled=true;
   if(guard==5)c.feared=true;
   if(guard==6)c.stunned=true;
   if(guard==7)c.mezzed=true;
   if(guard==8)c.aura=true;
   if(guard==9)c.dead=true;
   if(guard==10){c.held={Class::Wizard};c.class_id=Class::Wizard;}
   c.Packet(skill);
   check(c.attacks.empty() && c.p_timers.deadlines.empty(),"invalid attack executed or consumed cooldown (guard "+std::to_string(guard)+")");
  }
  Client low;low.level=0;low.Packet(skill);
  check(low.attacks.empty() && low.p_timers.deadlines.empty(),"future native cap authorized skill or consumed cooldown");
  Client released;released.Packet(skill);released.p_timers.now+=100;
  released.held={Class::Wizard};released.class_id=Class::Wizard;released.Packet(skill);
  check(released.attacks.size()==1,"released Monk retained attack access");
 }
}
void haste_reduction() {
 struct Row {int haste,reduction,delay;};
 for(auto row:{Row{-50,0,13},Row{0,0,9},Row{100,0,4},Row{-50,2,10},Row{0,2,7},Row{100,2,3},Row{0,50,0}}) {
  for(int skill:monk_skills) {
   Client c;c.haste=row.haste;c.reduction=row.reduction;c.Packet(skill);
   check(c.attacks.size()==1,"haste/reduction suppressed first attack");
   if(row.delay==0) {
    check(c.p_timers.deadlines.empty(),"negative reduced reuse must clamp to zero");
    c.Packet(skill);check(c.attacks.size()==2,"zero reuse unnecessarily blocks same skill");
   } else {
    check(c.p_timers.deadlines.size()==1,"one attack must start one cooldown");
    check(c.p_timers.deadlines.begin()->second==1000+row.delay,"haste/AA skill reuse reduction changed");
    c.p_timers.now+=row.delay-1;c.Packet(skill);check(c.attacks.size()==1,"reduced cooldown ended early");
    ++c.p_timers.now;c.Packet(skill);check(c.attacks.size()==2,"reduced cooldown failed to expire");
   }
  }
 }
}
void early_return_zero_reuse(int skill) {
 using namespace EQ::skills;
 const int base=skill==SkillBash?BashReuseTime:FrenzyReuseTime;
 const uint8 native_class=skill==SkillBash?Class::Paladin:Class::Berserker;
 int failures=0,cases=0;
 for(int haste:{-50,0,100})for(int reduction:{base-1,base,base+40}) {
  for(bool secondary:{false,true}) {
   Client c;c.class_id=secondary?Class::Wizard:native_class;
   c.held=secondary?std::vector<uint8>{Class::Wizard,native_class}:std::vector<uint8>{native_class};
   c.haste=haste;c.reduction=reduction;c.Packet(skill);++cases;
   check(c.attacks.size()==1,"valid Bash/Frenzy first activation missing");
   if(!c.p_timers.durations.empty()) {
    ++failures;
    std::cerr<<"skill "<<skill<<" haste "<<haste<<" reduction "<<reduction
     <<" starts unsigned duration "<<c.p_timers.durations.begin()->second
     <<" with primary class "<<int(c.class_id)<<'\n';
   }
   c.Packet(skill);
   if(c.attacks.size()!=2) {
    ++failures;std::cerr<<"fully reduced skill "<<skill<<" blocks its next activation\n";
   }
  }
 }
 check(failures==0,std::to_string(failures)+" failures across "+std::to_string(cases)+
  " Bash/Frenzy equal-or-excess reduction cases");
}
void early_return_positive_reuse(int skill) {
 using namespace EQ::skills;
 const uint8 native_class=skill==SkillBash?Class::Paladin:Class::Berserker;
 struct Row {int haste,reduction,bash_delay,frenzy_delay;};
 for(auto row:{Row{-50,0,6,13},Row{0,0,4,9},Row{100,0,2,4},
  Row{-50,2,3,10},Row{0,2,2,7},Row{100,2,1,3},
  Row{-50,-2,9,16},Row{0,-2,6,11},Row{100,-2,3,5}}) {
  for(bool secondary:{false,true}) {
   Client c;c.class_id=secondary?Class::Wizard:native_class;
   c.held=secondary?std::vector<uint8>{Class::Wizard,native_class}:std::vector<uint8>{native_class};
   c.haste=row.haste;c.reduction=row.reduction;c.Packet(skill);
   const uint32 expected=skill==SkillBash?row.bash_delay:row.frenzy_delay;
   check(c.attacks.size()==1,"valid positive-reuse Bash/Frenzy activation missing");
   check(c.p_timers.durations.size()==1 && c.p_timers.durations.count(pTimerCombatAbility)==1,
    "Bash/Frenzy non-Monk shared timer identity changed");
   check(c.p_timers.durations.at(pTimerCombatAbility)==expected,
    "Bash/Frenzy native haste or signed reduction changed");
   c.p_timers.now+=expected-1;c.Packet(skill);
   check(c.attacks.size()==1,"Bash/Frenzy became usable before its deadline");
   ++c.p_timers.now;c.Packet(skill);
   check(c.attacks.size()==2,"Bash/Frenzy failed exactly at its deadline");
  }
 }
}
void restored_timers() {
 for(int first:monk_skills)for(int second:monk_skills) {
  if(first==second)continue;
  Client previous;previous.Packet(first);
  Client restored;restored.p_timers=previous.p_timers;
  restored.Packet(first);check(restored.attacks.empty(),"restored active skill cooldown was bypassed");
  restored.Packet(second);check(restored.attacks.size()==1,"restored skill timer blocked different skill");
 }
}
void cross_entry_points() {
 for(int first:monk_skills)for(int second:monk_skills) {
  for(bool packet_first:{false,true}) {
   Client c;c.haste=100;
   if(packet_first)c.Packet(first);else c.DoClassAttacks(c.GetTarget(),first,false);
   auto before=c.attacks.size();
   if(packet_first)c.DoClassAttacks(c.GetTarget(),second,false);else c.Packet(second);
   check((c.attacks.size()>before)==(first!=second),"packet/AI entry points disagree on per-skill cooldown identity");
  }
 }
}
void riposte() {
 for(int skill:monk_skills) {
  Client c;c.haste=100;c.DoClassAttacks(c.GetTarget(),skill,false);
  auto timers=c.p_timers.deadlines;auto count=c.attacks.size();
  c.DoClassAttacks(c.GetTarget(),skill,true);
  check(c.attacks.size()>count,"riposte was incorrectly blocked by active cooldown");
  check(c.p_timers.deadlines==timers,"riposte created or extended a persistent cooldown");
 }
}
void legacy_monk() {
 for(int first:monk_skills)for(int second:monk_skills) {
  for(bool packet:{false,true}) {
   Client c;c.version=EQ::versions::ClientVersion::UF;c.haste=100;
   if(packet)c.Packet(first);else c.DoClassAttacks(c.GetTarget(),first,false);
   auto before=c.attacks.size();check(before>0,"legacy valid attack missing");
   if(packet)c.Packet(second);else c.DoClassAttacks(c.GetTarget(),second,false);
   check(c.attacks.size()==before,"older clients must preserve shared Monk cooldown");
   check(c.p_timers.deadlines.size()==1 && c.p_timers.deadlines.count(pTimerCombatAbility)==1,
    "older-client persistent timer identity changed");
  }
 }
}
void non_monk() {
 using namespace EQ::skills;
 for(bool packet:{false,true})for(bool kick_first:{false,true}) {
  Client c;c.class_id=Class::Warrior;c.held={Class::Warrior,Class::Paladin};c.haste=100;
  int first=kick_first?SkillKick:SkillBash,second=kick_first?SkillBash:SkillKick;
  if(packet)c.Packet(first);else c.DoClassAttacks(c.GetTarget(),first,false);
  auto before=c.attacks.size();check(before>0,"ordinary class first attack missing");
  if(packet)c.Packet(second);else c.DoClassAttacks(c.GetTarget(),second,false);
  check(c.attacks.size()==before,"non-Monk Kick and Bash must retain stock shared cooldown");
  check(c.p_timers.deadlines.size()==1 && c.p_timers.deadlines.count(pTimerCombatAbility)==1,
   "non-Monk persistent timer identity changed");
 }
}
int main(int argc,char** argv) {
 try {
  check(argc==2,"scenario required");std::string scenario=argv[1];
  if(scenario=="dragon-round") {
   Client c;c.Packet(EQ::skills::SkillDragonPunch);c.Packet(EQ::skills::SkillRoundKick);
   check(c.attacks==std::vector<int>{EQ::skills::SkillDragonPunch,EQ::skills::SkillRoundKick},"Dragon Punch incorrectly blocks Round Kick");
  } else if(scenario=="packet-pairs")pairwise("packet");
  else if(scenario=="class-pairs")pairwise("class");
  else if(scenario=="packet-same")same_skill("packet");
  else if(scenario=="class-same")same_skill("class");
  else if(scenario=="guards")packet_guards();
  else if(scenario=="haste")haste_reduction();
  else if(scenario=="bash-zero")early_return_zero_reuse(EQ::skills::SkillBash);
  else if(scenario=="frenzy-zero")early_return_zero_reuse(EQ::skills::SkillFrenzy);
  else if(scenario=="bash-positive")early_return_positive_reuse(EQ::skills::SkillBash);
  else if(scenario=="frenzy-positive")early_return_positive_reuse(EQ::skills::SkillFrenzy);
  else if(scenario=="restored")restored_timers();
  else if(scenario=="cross-entry")cross_entry_points();
  else if(scenario=="riposte")riposte();
  else if(scenario=="legacy")legacy_monk();
  else if(scenario=="non-monk")non_monk();
  else throw std::runtime_error("unknown scenario");
  std::cout<<"PASS: "<<scenario<<'\n';
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''


class MonkCombatReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        combat = (SOURCE / "zone/special_attacks.cpp").read_text(encoding="utf-8")
        skills = (SOURCE / "common/skills.cpp").read_text(encoding="utf-8")
        timers = (SOURCE / "common/ptimer.h").read_text(encoding="utf-8")
        timer_enum = function(timers, "enum : int") + ";"
        helper = (SOURCE / "common/combat_ability_timer.h").read_text(encoding="utf-8")
        # The surrounding server headers pull in the complete engine; use its
        # exact timer enum and helper with only those boundary includes removed.
        methods = "\n".join(line for line in helper.splitlines()
                            if not line.startswith(("#include", "#pragma")))
        methods += function(skills, "bool EQ::skills::CanUseMonkCombatAbility(")
        for signature in ("void Client::OPCombatAbility(", "void Client::DoClassAttacks("):
            methods += function(combat, signature)
        cls.temp = tempfile.TemporaryDirectory(prefix="monk-combat-reuse-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        fixture = FIXTURE.replace("/* NATIVE_TIMER_ENUM */", timer_enum)
        (path / "test.cpp").write_text(fixture + methods + CONTROLS, encoding="utf-8")
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /I"{SOURCE}" test.cpp /Fe:test.exe\n'
            )
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["g++", "-std=c++17", "-Wall", "-Wextra", "-I", str(SOURCE), "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_scenario(self, scenario):
        result = subprocess.run([self.binary, scenario], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_dragon_punch_does_not_block_round_kick(self):
        self.run_scenario("dragon-round")

    def test_all_six_packet_attacks_have_independent_cooldowns(self):
        self.run_scenario("packet-pairs")

    def test_all_six_class_attacks_have_independent_cooldowns(self):
        self.run_scenario("class-pairs")

    def test_repeating_same_packet_skill_obeys_expiry(self):
        self.run_scenario("packet-same")

    def test_repeating_same_class_skill_obeys_expiry(self):
        self.run_scenario("class-same")

    def test_packet_authorization_and_target_controls(self):
        self.run_scenario("guards")

    def test_haste_and_aa_skill_reuse_reduction(self):
        self.run_scenario("haste")

    def test_bash_equal_or_excess_reduction_has_no_unsigned_long_lock(self):
        self.run_scenario("bash-zero")

    def test_frenzy_equal_or_excess_reduction_has_no_unsigned_long_lock(self):
        self.run_scenario("frenzy-zero")

    def test_bash_haste_negative_reduction_and_native_deadline_controls(self):
        self.run_scenario("bash-positive")

    def test_frenzy_haste_negative_reduction_and_native_deadline_controls(self):
        self.run_scenario("frenzy-positive")

    def test_restored_timers_preserve_independent_cooldowns(self):
        self.run_scenario("restored")

    def test_packet_and_class_attacks_share_each_skill_cooldown(self):
        self.run_scenario("cross-entry")

    def test_riposte_bypasses_but_does_not_extend_cooldown(self):
        self.run_scenario("riposte")

    def test_older_clients_keep_shared_monk_cooldown(self):
        self.run_scenario("legacy")

    def test_non_monk_kick_and_bash_keep_stock_shared_cooldown(self):
        self.run_scenario("non-monk")


if __name__ == "__main__":
    unittest.main(verbosity=2)
