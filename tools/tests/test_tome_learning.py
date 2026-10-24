"""Compile actual tome learning and packet dispatch against isolated IO fakes.

Run directly, or pass --source-root PATH containing zone/ and common/ to verify
a retained server tree. Canonical authorization uses the real checked-in catalog
and GetSpellMinLevel. This does not establish native-client or live DB acceptance.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "server-mods/code"


def function(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <functional>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>
#include "spell_class_catalog.h"
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t;
constexpr int MAX_PP_DISCIPLINES=8;
constexpr uint32 Tome=66390, Sneak=4659, High=8001;
namespace Chat { enum {Red,White}; }
namespace Class { enum {Wizard=12,Enchanter=14,Magician=13,Necromancer=11,PLAYER_CLASS_COUNT=16}; }
namespace EQ { namespace item { enum {ItemTypeSpell=20}; }
struct ItemData {
 uint32 ID=Tome,Classes=2304;int ItemType=20;bool common=true;
 std::string Name="Tome of Sneak Attack";struct {int Effect=Sneak;} Scroll;
 bool IsClassCommon()const{return common;}
}; }
namespace Strings { bool BeginsWith(const std::string&s,const std::string&p){return s.rfind(p,0)==0;} }
namespace fmt {template<class...T>std::string format(const char*,T...){return "formatted diagnostic";} }
template<class...T>void LogError(T...){}
struct Spell {uint8 classes[16];} spells[10000];
bool IsValidSpell(uint32 id){return id==Sneak || id==High;}
bool require_handin=false;
#define RuleB(category,name) require_handin
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct Database {
 EQ::ItemData item;bool found=true,save_ok=true;int attempts=0;
 uint32 saved[MAX_PP_DISCIPLINES]={};std::function<void()> before_save;
 const EQ::ItemData*GetItem(uint32 id){return found&&id==Tome?&item:nullptr;}
 bool SaveCharacterDiscipline(uint32,int slot,uint32 spell){
  ++attempts;if(before_save)before_save();if(!save_ok)return false;saved[slot]=spell;return true;
 }
} database;
struct Client {
 uint8 primary=9,m_class2=0,m_class3=0,level=30;
 int returned=0,updates=0,deletions=0,charges=3;bool original_instance=true;
 std::vector<std::string> messages;
 struct {struct {uint32 values[MAX_PP_DISCIPLINES]={};}disciplines;}m_pp;
 uint8 GetClass()const{return primary;}uint8 GetLevel()const{return level;}
 uint32 CharacterID()const{return 27;}
 std::vector<uint8>GetMulticlassList()const;
 uint8 GetSpellMinLevel(uint16)const;
 void Message(int,const char*s){messages.push_back(s);}
 void SummonItem(uint32){++returned;}
 void SendDisciplineUpdate(){++updates;}
 void DeleteItemInInventory(int slot,int count,bool update){
  check(slot==4215&&count==1&&update,"right-click must consume exactly one from its source slot");
  ++deletions;--charges;if(charges==0)original_instance=false;
 }
 bool TrainDiscipline(uint32);
 bool LearnDisciplineFromItem(uint32);
 void RightClick();
};
'''

SCENARIOS = r'''
void rejected(Client& p,bool click,const char* why){
 auto before=p.m_pp;
 if(click)p.RightClick();else check(!p.TrainDiscipline(Tome),why);
 check(std::equal(std::begin(p.m_pp.disciplines.values),std::end(p.m_pp.disciplines.values),std::begin(before.disciplines.values)),"rejection modified profile");
 check(p.updates==0,"rejection published a learned discipline");
 check(std::all_of(std::begin(database.saved),std::end(database.saved),[](uint32 spell){return spell==0;}),"rejection persisted a new discipline");
 check(p.deletions==0&&p.charges==3&&p.original_instance,"rejection consumed or replaced original tome instance");
 check(p.returned==(click?0:1),"right-click must preserve original; consumed caller must refund one");
 check(!p.messages.empty(),"rejection must explain failure");
}
void learned(Client& p,bool click,int slot=0){
 database.before_save=[&]{check(p.m_pp.disciplines.values[slot]==0,"profile was modified before persistence succeeded");};
 if(click)p.RightClick();else check(p.TrainDiscipline(Tome),"eligible held class could not learn");
 check(p.m_pp.disciplines.values[slot]==uint32(database.item.Scroll.Effect),"learned profile entry missing");
 check(database.saved[slot]==p.m_pp.disciplines.values[slot],"learned discipline not persisted");
 check(p.updates==1&&database.attempts==1,"learning must publish and persist once");
 check(p.returned==0,"successful learning returned another tome");
 check(p.deletions==(click?1:0)&&p.charges==(click?2:3),"wrong consumed/hand-in item count");
 Client relog;std::copy(std::begin(database.saved),std::end(database.saved),std::begin(relog.m_pp.disciplines.values));
 check(relog.m_pp.disciplines.values[slot]==p.m_pp.disciplines.values[slot],"saved discipline absent on simulated reload");
}
int main(int argc,char**argv){try{
 check(argc==2,"scenario required");std::string s=argv[1];Client p;
 for(auto id:{Sneak,High})std::fill(std::begin(spells[id].classes),std::end(spells[id].classes),255);
 spells[Sneak].classes[8]=20;spells[High].classes[8]=68;
 bool click=s.rfind("click_",0)==0;if(click)s=s.substr(6);
 if(s=="primary")learned(p,click);
 else if(s=="secondary"){p.primary=5;p.m_class2=9;learned(p,click);}
 else if(s=="tertiary"){p.primary=5;p.m_class2=10;p.m_class3=9;learned(p,click);}
 else if(s=="caster_primary"){p.primary=12;p.m_class2=9;learned(p,click);}
 else if(s=="level_boundary"){p.level=20;learned(p,click);}
 else if(s=="below_level"){p.level=19;rejected(p,click,"below-level discipline accepted");}
 else if(s=="high_level"){p.level=60;database.item.Scroll.Effect=High;rejected(p,click,"over-60 discipline level was erased");}
 else if(s=="high_boundary"){p.level=68;database.item.Scroll.Effect=High;learned(p,click);}
 else if(s=="unowned_widened"){
  p.primary=5;database.item.Classes=65535;std::fill(std::begin(spells[Sneak].classes),std::end(spells[Sneak].classes),1);
  rejected(p,click,"widened data authorized an unowned canonical class");
 }
 else if(s=="canonical_level"){
  p.level=19;std::fill(std::begin(spells[Sneak].classes),std::end(spells[Sneak].classes),1);
  rejected(p,click,"widened class levels bypassed canonical level");
 }
 else if(s=="canonical_owned"){
  p.primary=12;p.m_class3=9;database.item.Classes=1u<<(12-1);
  std::fill(std::begin(spells[Sneak].classes),std::end(spells[Sneak].classes),255);learned(p,click);
 }
 else if(s=="removed_class"){p.primary=5;p.m_class2=10;database.item.Classes=65535;rejected(p,click,"removed class still authorized learning");}
 else if(s=="duplicate"){p.m_pp.disciplines.values[0]=Sneak;rejected(p,click,"duplicate accepted");}
 else if(s=="duplicate_hole"){p.m_pp.disciplines.values[3]=Sneak;rejected(p,click,"duplicate after empty slot accepted");}
 else if(s=="full"){std::fill(std::begin(p.m_pp.disciplines.values),std::end(p.m_pp.disciplines.values),1);rejected(p,click,"full list accepted");}
 else if(s=="last_slot"){
  std::fill(std::begin(p.m_pp.disciplines.values),std::end(p.m_pp.disciplines.values)-1,1);learned(p,click,MAX_PP_DISCIPLINES-1);
 }
 else if(s=="save_failure"){
  database.save_ok=false;rejected(p,click,"failed persistence reported success");check(database.attempts==1,"save failure scenario never attempted save");
 }
 else if(s=="invalid_spell"){database.item.Scroll.Effect=9999;rejected(p,click,"invalid spell accepted");}
 else if(s=="invalid_type"){database.item.ItemType=1;rejected(p,click,"invalid item type accepted");}
 else if(s=="not_common"){database.item.common=false;rejected(p,click,"non-common item accepted");}
 else if(s=="not_tome"){database.item.Name="Scroll of Sneak Attack";rejected(p,click,"scroll accepted as tome");}
 else if(s=="skill_prefix"){database.item.Name="Skill: Sneak Attack";learned(p,click);}
 else if(s=="missing_item"){
  database.found=false;check(!p.TrainDiscipline(Tome),"missing item accepted");check(p.returned==0&&database.attempts==0,"unknown item refunded or persisted");
 }
 else if(s=="handin_rule"){
  require_handin=true;p.RightClick();check(p.deletions==0&&database.attempts==0&&p.returned==0,"right-click ignored hand-in rule");
 }
 else throw std::runtime_error("unknown scenario");
 std::cout<<"PASS "<<argv[1]<<"\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''

CASES = (
    "primary", "secondary", "tertiary", "caster_primary", "level_boundary",
    "below_level", "high_level", "high_boundary", "unowned_widened",
    "canonical_level", "canonical_owned", "removed_class", "duplicate",
    "duplicate_hole", "full", "last_slot", "save_failure", "invalid_spell",
    "invalid_type", "not_common", "not_tome", "skill_prefix", "missing_item",
    "click_primary", "click_secondary", "click_tertiary", "click_caster_primary",
    "click_level_boundary", "click_below_level", "click_high_level",
    "click_high_boundary", "click_unowned_widened", "click_canonical_level",
    "click_canonical_owned", "click_removed_class", "click_duplicate",
    "click_duplicate_hole", "click_full", "click_last_slot", "click_save_failure",
    "click_invalid_spell", "click_skill_prefix", "click_handin_rule",
)


class TomeLearning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        effects = (SOURCE_ROOT / "zone/effects.cpp").read_text()
        methods = effects[effects.index("bool Client::TrainDiscipline("):
                          effects.index("bool Client::MemorizeSpellFromItem(")]
        mods = (SOURCE_ROOT / "zone/client_mods.cpp").read_text()
        methods += function(mods, "std::vector<uint8> Client::GetMulticlassList()")
        methods += function(mods, "uint8 Client::GetSpellMinLevel(")
        packet = (SOURCE_ROOT / "zone/client_packet.cpp").read_text()
        marker = packet.index("!RuleB(Skills, RequireTomeHandin)")
        start = packet.rfind("if (", 0, marker)
        dispatch = function(packet[start:], "if (")
        methods += "\nvoid Client::RightClick(){const auto* item=&database.item;const int slot_id=4215;\n" + dispatch + "\n}\n"
        cls.temp = tempfile.TemporaryDirectory(prefix="tome-learning-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        shutil.copyfile(SOURCE_ROOT / "common/spell_class_catalog.h", path / "spell_class_catalog.h")
        (path / "test.cpp").write_text(FIXTURE + methods + SCENARIOS)
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe\n')
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = [os.environ.get("CXX", "g++"), "-std=c++17", "-Wall", "-Wextra", "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)


def scenario_test(scenario):
    def run(self):
        result = subprocess.run([self.binary, scenario], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    return run


for case in CASES:
    setattr(TomeLearning, "test_" + case, scenario_test(case))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.source_root:
        SOURCE_ROOT = args.source_root
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
