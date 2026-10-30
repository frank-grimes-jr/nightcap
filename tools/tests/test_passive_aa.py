"""Compile actual XP methods with small world/client boundary fakes; no DB writes.

Run: python3 tools/tests/test_passive_aa.py --compiler clang++
The test extracts production bodies, rather than reimplementing XP arithmetic.
Full server compilation and RoF2 QA are separate checks.
"""
import argparse
import os
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


PRELUDE = r'''
#include "common/aa_progression.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <string>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using uint64=uint64_t;
std::map<std::string,double> rules;
#define RuleI(c,n) (int(rules[#c ":" #n]))
#define RuleR(c,n) (float(rules[#c ":" #n]))
#define RuleB(c,n) (bool(rules[#c ":" #n]))
#define LogDebug(...) ((void)0)
#define Log(...) ((void)0)
#define LogAA(...) ((void)0)
enum ExpSource { Quest, GM, Kill, Death, Resurrection, LDoNChest, Task, Sacrifice };
namespace ConsiderColor { enum { Gray=1,Green,LightBlue,DarkBlue,White,Yellow,Red }; }
namespace Class { enum { Warrior=1,Rogue,Paladin,ShadowKnight,Ranger,Bard,Monk,Wizard,Enchanter,Magician,Necromancer }; }
namespace Race { enum { Human=1,Halfling,Troll,Iksar,Ogre,Barbarian }; }
namespace Chat { enum { White,Red,Yellow }; }
namespace EQ { template<class T> T Clamp(T x,T a,T b) { return std::clamp(x,a,b); } }
namespace fmt { std::string format_int(int i) { return std::to_string(i); }
template<class... T> std::string format(std::string s,T...) { return s; } }
namespace Strings {
bool EqualFold(std::string a,std::string b) { for(auto& c:a)c=tolower(c); for(auto& c:b)c=tolower(c); return a==b; }
uint32 ToUnsignedInt(const std::string& s) { return std::stoul(s); }
}
// Boundary service; the default test world is a public zone with its native ZEM.
namespace NightcapDungeon { float ExperienceModifier(float value) { return value; } }
struct Seperator { int argnum=1; std::string arg[2]; };
enum { aaActionActivate,aaActionBuy,aaActionDisableEXP,aaActionSetEXP };
struct AA_Action { uint32 action,ability,target_id,exp_value; };
struct EQApplicationPacket { uint32 size; void* pBuffer; };
enum { AA_CAP,OVER_AA_CAP,AA_OFF,AA_ON };
struct NPC {
    bool owned=false, merc=false, swarm=false;
    bool HasOwner() { return owned; }
    bool IsMerc() { return merc; }
    bool GetSwarmInfo() { return swarm; }
    bool GetSwarmOwner() { return swarm; }
};
namespace NightcapLoot {
enum class TransferResult { Declined, Delivered, Uncertain };
uint64 awarded_item_exp=0; unsigned item_awards=0;
TransferResult item_result=TransferResult::Delivered;
TransferResult AwardItemExperience(void*, uint64 xp) {
    awarded_item_exp=xp; ++item_awards; return item_result;
}
}
struct Zone {
    struct { float zone_exp_multiplier=1; } newzone_data;
    struct Mods { float ExpMod=0, AAExpMod=0; } level_exp_mod[256];
    bool hot=false;
    bool IsHotzone() { return hot; }
    float expmod=1, aamod=1;
    float GetEXPModifier(void*) { return expmod; }
    float GetAAEXPModifier(void*) { return aamod; }
} world, *zone=&world;
struct Client {
    struct { uint32 perAA=0; } m_epp;
    struct { uint64 exp=0; uint32 expAA=0,aapoints=0; } m_pp;
    int level=30, race=Race::Human, cls=Class::Magician, XPRate=0;
    bool enabled=true;
    uint64 last_exp=0,last_aa=0;
    int calls=0;
    uint8 GetLevel() { return level; }
    uint8 GetClientMaxLevel() { return 0; }
    int GetBaseRace() { return race; }
    int GetClass() { return cls; }
    uint64 GetEXP() { return m_pp.exp; }
    uint32 GetAAXP() { return m_pp.expAA; }
    int GetSpentAA() { return 0; }
    uint32 GetAAPoints() { return m_pp.aapoints; }
    uint32 GetAAPercent() { return m_epp.perAA; }
    uint64 GetRequiredAAExperience() { return RuleI(AA,ExpPerPoint); }
    bool IsEXPEnabled() { return enabled; }
    template<class... T> void Message(T...) {}
    template<class... T> void MessageString(T...) {}
    void SendAlternateAdvancementStats() {}
    void SendAlternateAdvancementTable() {}
    void CalculateLeadershipExp(uint64&,uint8) {}
    void SetEXP(ExpSource,uint64 xp,uint64 aa,bool=false,NPC*=nullptr);
    uint32 GetEXPForLevel(uint16);
    void CalculateExp(uint64,uint64&,uint64&,uint8,bool,uint64* = nullptr);
    void CalculateStandardAAExp(uint64&,uint8,bool);
    void CalculateNormalizedAAExp(uint64&,uint8,bool);
    void AddEXP(ExpSource,uint64,uint8=0xff,bool=false,NPC*=nullptr);
    void AddLevelBasedExp(ExpSource,uint8,uint8=0,bool=false);
    void SetAAExperiencePercent(uint32);
    void SetAAEXPPercentage(uint8);
    void Handle_OP_AAAction(const EQApplicationPacket*);
    void ActivateAlternateAdvancementAbility(uint32,uint32) {}
    void PurchaseAlternateAdvancementRank(uint32) {}
    void NormalizeAAAllocation();
    uint64 FinalizeAAExperience(uint64,bool);
    uint64 CalculateLevelBasedAAExp(uint64,uint64);
};
void Client::SetEXP(ExpSource,uint64 xp,uint64 aa,bool,NPC*) {
    ++calls; last_exp=xp; last_aa=aa;
    m_pp.exp=xp; m_pp.aapoints+=aa/GetRequiredAAExperience();
    m_pp.expAA=aa%GetRequiredAAExperience();
}
void reset() {
    rules={{"Character:AAExpMinLevel",1},{"AA:PassiveExpPercent",1},
        {"Character:ExpMultiplier",0.65},{"Character:AAExpMultiplier",0.65},
        {"Character:FinalExpMultiplier",1},{"Character:ExperiencePercentCapPerKill",-1},
        {"AA:MaxAAEXPPerKill",-1},{"AA:UnusedAAPointCap",-1},{"AA:ExpPerPoint",50000},
        {"AA:NormalizedAANumberOfWhiteConPerAA",25}, {"Character:WhiteModifier",100},
        {"Character:BlueModifier",100},{"Character:GreenModifier",0},
        {"Character:UseXPConScaling",1}};
    world=Zone{};
}
int failures=0,checks=0;
void check(bool result,const char* label) { ++checks; if(!result) { ++failures; std::cerr<<"FAIL "<<label<<"\n"; } }
'''.replace('NPC*=', 'NPC* =')

CASES = r'''
int main() {
    reset(); Client c;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==6500 && c.last_aa==65,"off: full level XP plus passive AA");
    reset(); c=Client{}; c.SetAAExperiencePercent(25);
    check(c.GetAAPercent()==25,"command setter preserves percentage");
    c.SetAAExperiencePercent(100);
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==0 && c.last_aa==6500,"on: full AA, no extra passive bonus");
    c.SetAAEXPPercentage(1); check(c.GetAAPercent()==1,"quest setter preserves percentage");
    c.SetAAEXPPercentage(0); check(c.GetAAPercent()==0,"quest setter turns off");
    for(auto source : {Quest,Task}) {
        reset(); c=Client{}; c.AddEXP(source,10000);
        check(c.last_exp==6500 && c.last_aa==65,"raw quest/task passive");
        rules["AA:NormalizedAAEnabled"]=1; c=Client{}; c.AddEXP(source,10000);
        check(c.last_exp==6500 && c.last_aa==65,"normalized mode raw quest/task uses amount");
        c=Client{}; c.AddLevelBasedExp(source,10);
        auto award=(c.GetEXPForLevel(31)-c.GetEXPForLevel(30))/10;
        check(c.last_exp==award && c.last_aa==uint64(award*0.65)/100,"percentage quest/task passive");
        c=Client{}; c.SetAAExperiencePercent(100); c.AddLevelBasedExp(source,10);
        check(c.last_exp==0 && c.last_aa==uint64(award*0.65),"percentage quest/task full allocation");
    }
    reset(); rules["AA:NormalizedAAEnabled"]=1; c=Client{};
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==6500 && c.last_aa==20,"normalized kill passive");
    c=Client{}; c.AddEXP(Kill,0,ConsiderColor::White);
    check(c.last_aa==0,"zero XP never creates normalized AA");
    c=Client{}; c.AddEXP(Kill,10000,ConsiderColor::Gray);
    check(c.last_exp==0 && c.last_aa==0,"gray kill no XP");
    reset(); c=Client{}; c.m_pp.expAA=19; c.SetAAExperiencePercent(100);
    c.AddEXP(Resurrection,10000,0xff,true);
    check(c.last_exp==10000 && c.last_aa==19,"rez restores only level XP");
    for(auto source : {GM,Death,Resurrection,Sacrifice,LDoNChest}) {
        reset(); c=Client{}; c.AddEXP(source,10000);
        check(c.last_aa==0,"non-progression sources no passive award");
    }
    reset(); rules["Character:AAExpMinLevel"]=51; c=Client{}; c.m_pp.expAA=19; c.m_epp.perAA=100;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==6500 && c.last_aa==19 && c.GetAAPercent()==0,"below minimum keeps XP and prior AA");
    reset(); c=Client{}; c.enabled=false; c.AddEXP(Quest,10000); c.AddLevelBasedExp(Task,10);
    check(c.calls==0,"XP disabled covers both reward APIs");
    reset(); rules["AA:UnusedAAPointCap"]=10; c=Client{}; c.m_pp.aapoints=10; c.m_pp.expAA=19; c.m_epp.perAA=100;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==0 && c.last_aa==19 && c.m_pp.aapoints==10 && c.GetAAPercent()==100,"bank cap preserves earned state and level hold");
    c=Client{}; c.m_pp.aapoints=9; c.m_pp.expAA=49990;
    c.AddEXP(Kill,10000000,ConsiderColor::White);
    check(c.m_pp.aapoints==10 && c.m_pp.expAA==0,"large award cannot cross bank cap");
    reset(); rules["AA:MaxAAEXPPerKill"]=1000; c=Client{}; c.AddEXP(Kill,100000,ConsiderColor::White);
    check(c.last_aa==10,"passive percentage follows full-AA award cap");
    reset(); rules["AA:PassiveExpPercent"]=0; c=Client{}; c.AddEXP(Quest,10000);
    check(c.last_exp==6500 && c.last_aa==0,"zero rate disables passive only");
    reset(); c=Client{}; c.AddEXP(Kill,75,ConsiderColor::White);
    check(c.last_aa==0,"tiny rewards round down, no minimum farming bonus");
    reset(); c=Client{}; c.m_epp.perAA=55; c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==2925 && c.last_aa==3604 && c.GetAAPercent()==55,"legacy partial allocation and passive fraction retained");
    reset(); c=Client{}; c.m_epp.perAA=256; c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==6500 && c.GetAAPercent()==0,"invalid allocation fails off before narrowing");
    reset(); rules["Zone:LevelBasedEXPMods"]=1; rules["Character:FinalExpMultiplier"]=2;
    world.level_exp_mod[30].ExpMod=2; world.level_exp_mod[30].AAExpMod=1; c=Client{}; c.AddLevelBasedExp(Task,10);
    auto reward=(c.GetEXPForLevel(31)-c.GetEXPForLevel(30))/10*4;
    check(c.last_exp==reward && c.last_aa==uint64(reward/2*0.65)/100,"percentage reward independent level/AA mods applied once");
    world.level_exp_mod[30].AAExpMod=0; c=Client{}; c.AddLevelBasedExp(Task,10);
    check(c.last_exp==reward && c.last_aa==0,"percentage reward respects disabled AA level modifier");
    world.level_exp_mod[30].ExpMod=0; c=Client{}; c.AddLevelBasedExp(Task,10);
    check(c.last_exp==reward/2 && c.last_aa==uint64(reward/2*0.65)/100,"missing level modifier row preserves AA reward");
    for(auto value : {0u,1u,25u,99u,100u,101u,256u,0xffffffffu}) {
        reset(); c=Client{}; AA_Action action{aaActionSetEXP,0,0,value};
        EQApplicationPacket packet{sizeof(action),&action}; c.Handle_OP_AAAction(&packet);
        check(c.GetAAPercent()==(value<=100?value:0u),"packet validation precedes any narrowing");
        check(load_allocation(value,30)==(value<=100?value:0u),"saved allocation normalized on load");
    }
    reset(); rules["Character:AAExpMinLevel"]=51;
    check(load_allocation(100,30)==0,"loaded allocation below minimum turns off");
    for(const auto& value : {"on","off","0","1","50","100","101","256","-1","1.5","4294967296","garbage"}) {
        reset(); c=Client{}; Seperator sep; sep.arg[1]=value; command_aa_exp(&c,&sep);
        uint32 expected=std::string(value)=="on" || std::string(value)=="100" ? 100 : std::string(value)=="50" ? 50 : std::string(value)=="1" ? 1 : 0;
        check(c.GetAAPercent()==expected,"command accepts on/off and validates numeric tokens");
    }
    reset(); rules["AA:ModernAAScalingEnabled"]=1; rules["AA:ModernAAScalingStartPercent"]=1000;
    rules["AA:ModernAAScalingAALimit"]=4000; c=Client{}; c.AddEXP(Quest,10000);
    check(c.last_aa==650,"modern AA scaling applies before passive fraction");
    reset(); rules["AA:UnusedAAPointCap"]=10; c=Client{}; c.m_pp.aapoints=12; c.m_pp.expAA=123;
    c.AddLevelBasedExp(Task,10);
    check(c.m_pp.aapoints==12 && c.m_pp.expAA==123 && c.last_exp>0,"over-cap owned AA remains intact");
    reset(); rules["AA:PassiveExpPercent"]=-1; c=Client{}; c.AddEXP(Quest,10000);
    check(c.last_aa==0,"negative passive configuration clamps off");
    rules["AA:PassiveExpPercent"]=200; c=Client{}; c.AddEXP(Quest,10000);
    check(c.last_aa==6500 && c.last_exp==6500,"excess passive configuration clamps to 100");
    reset(); rules["Character:EnableCharacterEXPMods"]=1; world.expmod=2; world.aamod=3;
    c=Client{}; c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==13000 && c.last_aa==195,"independent character AA/level modifiers");
    reset(); c=Client{}; c.m_pp.expAA=49000; c.AddEXP(Quest,1000000);
    check(c.m_pp.aapoints==1 && c.m_pp.expAA==5500,"passive progress crosses point boundary and retains remainder");
    reset(); rules["AA:NormalizedAAEnabled"]=1; c=Client{}; c.SetAAExperiencePercent(100);
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.last_exp==0 && c.last_aa==2000,"normalized focus gets full AA award");
    reset(); rules["Zone:LevelBasedEXPMods"]=1; world.level_exp_mod[30]={2,3};
    c=Client{}; c.AddLevelBasedExp(Task,10,20,true);
    auto limited=(c.GetEXPForLevel(21)-c.GetEXPForLevel(20))/10;
    check(c.last_exp==limited && c.last_aa==uint64(limited*0.65f)/100,"max reward level and ignore-mods remain effective");

    // October 9 live tuning: rule reload applies to the next reward, without
    // rewriting existing AA progress or reducing the normal leveling award.
    reset(); c=Client{}; c.level=5; c.m_pp.expAA=1049;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.m_pp.expAA==1114 && c.GetEXP()==6500,"one-percent preimage at level five");
    rules["AA:PassiveExpPercent"]=20;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.m_pp.expAA==2414 && c.GetEXP()==13000,"twenty-percent reload keeps prior progress and level XP");
    for(auto level : {5,10,30,50}) {
        for(auto source : {Kill,Quest,Task}) {
            reset(); rules["AA:PassiveExpPercent"]=20; c=Client{}; c.level=level;
            c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==6500 && c.last_aa==1300,"twenty-percent kill/quest/task at progression levels");
            c=Client{}; c.level=level; c.SetAAExperiencePercent(100);
            c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==0 && c.last_aa==6500,"twenty-percent tuning does not boost full focus");
        }
    }
    for(auto source : {Quest,Task}) {
        reset(); rules["AA:PassiveExpPercent"]=20; c=Client{}; c.AddLevelBasedExp(source,10);
        auto award=(c.GetEXPForLevel(31)-c.GetEXPForLevel(30))/10;
        check(c.last_exp==award && c.last_aa==uint64(award*0.65f)*20/100,"twenty-percent percentage quest/task rewards");
    }
    reset(); rules["AA:PassiveExpPercent"]=20; c=Client{};
    c.AddEXP(Kill,1,ConsiderColor::White);
    check(c.last_aa==0,"twenty-percent tiny rewards retain no minimum stipend");

    // Owner-requested second tuning: 20 -> 40, retaining accumulated XP.
    reset(); rules["AA:PassiveExpPercent"]=20; c=Client{}; c.level=5; c.m_pp.expAA=1049;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    rules["AA:PassiveExpPercent"]=40;
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.m_pp.expAA==4949 && c.GetEXP()==13000,"forty-percent reload retains prior progress and normal XP");
    for(auto level : {5,10,30,50}) {
        for(auto source : {Kill,Quest,Task}) {
            reset(); rules["AA:PassiveExpPercent"]=40; c=Client{}; c.level=level;
            c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==6500 && c.last_aa==2600,"forty-percent kill/quest/task at progression levels");
            c=Client{}; c.level=level; c.SetAAExperiencePercent(100);
            c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==0 && c.last_aa==6500,"forty-percent tuning retains full focus award");
        }
    }
    for(auto source : {Quest,Task}) {
        reset(); rules["AA:PassiveExpPercent"]=40; c=Client{}; c.AddLevelBasedExp(source,10);
        auto award=(c.GetEXPForLevel(31)-c.GetEXPForLevel(30))/10;
        check(c.last_exp==award && c.last_aa==uint64(award*0.65f)*40/100,"forty-percent percentage quest/task rewards");
    }
    reset(); rules["AA:PassiveExpPercent"]=40; c=Client{}; c.AddEXP(Kill,1,ConsiderColor::White);
    check(c.last_aa==0,"forty-percent tiny awards retain no minimum stipend");
    c=Client{}; c.m_pp.expAA=49000; c.AddEXP(Quest,10000);
    check(c.m_pp.aapoints==1 && c.m_pp.expAA==1600 && c.last_exp==6500,"forty-percent AA boundary keeps remainder and level XP");

    std::cout<<checks<<" checks, "<<failures<<" failures\n";
    return failures?1:0;
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', default='clang++')
    args = parser.parse_args()
    source = (ROOT / 'server-mods/code/zone/exp.cpp').read_text(encoding='utf-8')
    client = (ROOT / 'server-mods/code/zone/client.cpp').read_text(encoding='utf-8')
    packet = (ROOT / 'server-mods/code/zone/client_packet.cpp').read_text(encoding='utf-8')
    command = (ROOT / 'server-mods/code/zone/gm_commands/aa_exp.cpp').read_text(encoding='utf-8')
    db = (ROOT / 'server-mods/code/zone/zonedb.cpp').read_text(encoding='utf-8')
    bodies = []
    for name in ['static uint64 ScaleAAXPBasedOnCurrentAATotal', 'float static GetConLevelModifierPercent',
                 'void Client::CalculateNormalizedAAExp', 'void Client::CalculateStandardAAExp',
                 'void Client::CalculateExp', 'uint64 Client::CalculateLevelBasedAAExp', 'void Client::NormalizeAAAllocation',
                 'uint64 Client::FinalizeAAExperience', 'void Client::AddEXP',
                 'void Client::AddLevelBasedExp', 'uint32 Client::GetEXPForLevel']:
        if name in source:
            bodies.append(function(source, name))
    for name in ['void Client::SetAAExperiencePercent', 'void Client::SetAAEXPPercentage']:
        bodies.append(function(client, name))
    bodies.append(function(packet, 'void Client::Handle_OP_AAAction'))
    bodies.append(function(command, 'void command_aa_exp'))
    assignment = re.search(r'm_epp->perAA\s*=.*?;', db, re.S).group(0)
    bodies.append('uint32 load_allocation(uint32 percent, uint32 level) {'
                  'struct { uint32 e_percent_to_aa; } e{percent};'
                  'struct Profile { uint32 level; } profile{level}, *pp=&profile;'
                  'struct Epp { uint32 perAA=0; } ext, *m_epp=&ext;'
                  + assignment + 'return m_epp->perAA;}')
    with tempfile.TemporaryDirectory(prefix='passive-aa-') as tmp:
        path = pathlib.Path(tmp)
        test = path / 'test.cpp'
        test.write_text(PRELUDE + '\n'.join(bodies) + CASES, encoding='utf-8')
        if os.name == 'nt' and args.compiler == 'clang++':
            script = path / 'build.cmd'
            script.write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                              'cl /nologo /EHsc /std:c++20 /I"' + str(ROOT/'server-mods/code') + '" test.cpp /Fe:test.exe\n'
                              'exit /b %errorlevel%\n')
            subprocess.run(['cmd', '/d', '/c', str(script)], cwd=path, check=True)
            binary = path/'test.exe'
        else:
            subprocess.run([args.compiler, '-std=c++20', '-Wall', '-Wextra',
                            '-Wno-unused-parameter', '-I', str(ROOT/'server-mods/code'),
                            str(test), '-o', str(path/'test')], check=True)
            binary = path/'test'
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
