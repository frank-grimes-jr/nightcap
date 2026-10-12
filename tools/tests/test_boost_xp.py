"""Cross-check GM XP against extracted server C++ and exercise real SetEXP.

Run: python tools/tests/test_boost_xp.py --compiler g++
No database or game access. World/packet/quest boundaries are fakes; XP arithmetic
and level reconciliation are complete, unchanged production function bodies.
Reload here means decimal profile serialization, not a real client reconnect.
"""
import argparse
import os
import pathlib
import subprocess
import tempfile

from test_passive_aa import function

ROOT = pathlib.Path(__file__).resolve().parents[2]

PRELUDE = r'''
#include <cstdint>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t;
using uint64=uint64_t; using int8=int8_t;
std::map<std::string,int> rules;
#define RuleI(c,n) (rules[#c ":" #n])
#define RuleB(c,n) (bool(rules[#c ":" #n]))
#define LogDebug(...) ((void)0)
enum ExpSource { Kill, GM };
namespace Race { enum { Human=1,Barbarian=2,Troll=9,Ogre=10,Halfling=11,Iksar=128 }; }
namespace Class { enum { Warrior=1,Paladin=3,Ranger=4,ShadowKnight=5,Monk=7,Bard=8,Rogue=9,Necromancer=11,Wizard=12,Magician=13,Enchanter=14 }; }
namespace Chat { enum { Red,Yellow,Experience }; }
namespace AccountStatus { enum { GMAdmin=80 }; }
namespace EQ { namespace versions { enum { maskUFAndEarlier=1 }; } }
namespace PlayerEvent { enum { AA_GAIN }; struct AAGainedEvent { uint32 gained; }; }
namespace fmt { template<class... T> std::string format(std::string s,T...) { return s; } }
template<class... T> std::string StringFormat(const char*,T...) { return ""; }
template<class T> char* ConvertArray(T,char* out) { return out; }
enum { MAX_GROUP_MEMBERS=6,REZ_REGAIN,GAIN_GROUPXP,GAIN_RAIDEXP,GAIN_XP,
GAIN_SINGLE_AA_SINGLE_AA,GAIN_SINGLE_AA_MULTI_AA,GAIN_MULTI_AA_MULTI_AA,
EVENT_AA_GAIN,GAIN_LEVEL,CORPSE_ITEM_LOST,CORPSE_EXP_LOST,EVENT_EXP_GAIN,
EVENT_AA_EXP_GAIN,OP_ExpUpdate,GM_GAINXP };
struct NPC {};
struct Group { void* members[MAX_GROUP_MEMBERS]{}; };
struct Zone { bool IsHotzone() { return false; } } world,*zone=&world;
struct Parser {
    bool PlayerHasQuestSub(int) { return false; }
    template<class... T> void EventPlayer(T...) {}
} parser,*parse=&parser;
struct QueryServ { void SendQuery(const char*) {} } query_serv,*QServ=&query_serv;
struct Bot { template<class... T> static void LevelBotWithClient(T...) {} };
struct ExpUpdate_Struct { uint32 exp; };
struct EQApplicationPacket {
    void* pBuffer;
    EQApplicationPacket(int,size_t size):pBuffer(new char[size]) {}
    ~EQApplicationPacket() { delete[] static_cast<char*>(pBuffer); }
};
struct Client {
    struct { uint64 exp=0; uint32 expAA=17,aapoints=23; } m_pp;
    struct { uint32 perAA=0; } m_epp;
    int level=50,race=1,cls=1,admin=0,m_ClientVersionBit=0,client_max=0;
    uint8 GetLevel() { return level; }
    int GetBaseRace() { return race; }
    int GetClass() { return cls; }
    uint64 GetEXP() { return m_pp.exp; }
    uint32 GetAAXP() { return m_pp.expAA; }
    uint32 GetRequiredAAExperience() { return 50000; }
    Group* GetGroup() { return nullptr; }
    bool IsRaidGrouped() { return false; }
    int GetMercenaryID() { return 0; }
    void UpdateMercLevel() {}
    int GetClientMaxLevel() { return client_max; }
    int CharacterID() { return 1; }
    bool GetGM() { return false; }
    template<class... T> void Message(T...) {}
    template<class... T> void MessageString(T...) {}
    template<class... T> void ProcessEvolvingItem(T...) {}
    template<class... T> void RecordPlayerEventLog(T...) {}
    void SendSound() {}
    void SendAlternateAdvancementStats() {}
    void FastQueuePacket(EQApplicationPacket** p) { delete *p; *p=nullptr; }
    void SetLevel(uint8 value) { level=value; }
    uint32 GetEXPForLevel(uint16);
    uint32 CheckedEXPForLevel(uint16);
    void SetEXP(ExpSource,uint64,uint64,bool=false,NPC* =nullptr);
};
// Only the range probe uses this guard. The functions under test are unchanged.
uint32 checked(float value) {
    if (!(value >= 0 && double(value) < 4294967295.0)) throw std::overflow_error("XP overflow");
    return static_cast<uint32>(value);
}
int checks=0,failures=0;
void check(bool result,const char* label) {
    ++checks;
    if(!result) { if(failures<20)std::cerr<<"FAIL "<<label<<"\n"; ++failures; }
}
'''

CASES = r'''
int main() {
    rules={{"Character:MaxLevel",126},{"Character:AAExpMinLevel",1},{"AA:ExpPerPoint",50000}};
    // Demonstrate the original defect through the actual server reconciliation.
    Client broken; broken.m_pp.exp=0;
    broken.SetEXP(Kill,883418,17);
    check(broken.level==10,"zero XP boost reproduces level 50 to 10");
    // Darthy repair retains the XP earned after the malformed boost.
    Client repaired; repaired.level=50; repaired.race=12; repaired.cls=11;
    repaired.m_pp.exp=165592026;
    rules["Character:MaxLevel"]=50;
    check(repaired.GetEXPForLevel(50)==164708608,"Darthy native level 50 floor");
    repaired.SetEXP(GM,repaired.m_pp.exp,repaired.m_pp.expAA);
    check(repaired.level==50 && repaired.m_pp.exp==165592026,"Darthy repaired profile reconciles unchanged");
    repaired.SetEXP(Kill,repaired.m_pp.exp+1,repaired.m_pp.expAA);
    check(repaired.level==50 && repaired.m_pp.exp==165592027,"Darthy repaired profile survives next XP");
    std::stringstream repair_save;
    repair_save<<repaired.level<<" "<<repaired.m_pp.exp<<" "<<repaired.m_pp.expAA<<" "<<repaired.m_pp.aapoints;
    Client repair_load; repair_load.race=12; repair_load.cls=11;
    repair_save>>repair_load.level>>repair_load.m_pp.exp>>repair_load.m_pp.expAA>>repair_load.m_pp.aapoints;
    repair_load.SetEXP(Kill,repair_load.m_pp.exp+1,repair_load.m_pp.expAA);
    check(repair_load.level==50 && repair_load.m_pp.exp==165592028 &&
          repair_load.m_pp.expAA==17 && repair_load.m_pp.aapoints==23,
          "Darthy repaired profile survives serialization and another XP award");
    rules["Character:MaxLevel"]=126;
    int stable=0,overflow=0;
    for(int race : {1,2,3,4,5,6,7,8,9,10,11,12,128,130,330,522})
    for(int cls=1;cls<=16;++cls)
    for(int oldrace=0;oldrace<=1;++oldrace)
    for(int oldclass=0;oldclass<=1;++oldclass) {
        rules["Character:UseOldRaceExpPenalties"]=oldrace;
        rules["Character:UseOldClassExpPenalties"]=oldclass;
        for(int level=1;level<=126;++level) {
            Client c; c.level=level; c.race=race; c.cls=cls;
            std::cout<<level<<" "<<race<<" "<<cls<<" "<<oldrace<<" "<<oldclass<<" ";
            uint32 xp;
            try { xp=c.CheckedEXPForLevel(level); }
            catch(const std::overflow_error&) { ++overflow; std::cout<<"overflow\n"; continue; }
            check(c.GetEXPForLevel(level)==xp,"guard probe agrees with unchanged native threshold");
            std::cout<<xp<<"\n";
            // SetEXP consults level+1, so never execute it beyond its safe curve.
            try { c.CheckedEXPForLevel(level+1); }
            catch(const std::overflow_error&) { continue; }
            auto next=c.GetEXPForLevel(level+1);
            check(next>xp+2,"safe thresholds remain monotonic");
            c.m_pp.exp=xp;
            rules["Character:MaxLevel"]=126;
            c.SetEXP(Kill,c.m_pp.exp+1,c.m_pp.expAA);
            check(c.level==level && c.m_pp.exp==uint64(xp)+1,"boost survives first XP award");
            check(c.m_pp.expAA==17 && c.m_pp.aapoints==23,"boost preserves independent AA state");
            std::stringstream saved;
            saved<<c.level<<" "<<c.m_pp.exp<<" "<<c.m_pp.expAA<<" "<<c.m_pp.aapoints;
            Client loaded; loaded.race=race; loaded.cls=cls;
            saved>>loaded.level>>loaded.m_pp.exp>>loaded.m_pp.expAA>>loaded.m_pp.aapoints;
            loaded.SetEXP(Kill,loaded.m_pp.exp+1,loaded.m_pp.expAA);
            check(loaded.level==level && loaded.m_pp.exp==uint64(xp)+2,"serialized profile survives another award");
            // Era cap and per-character cap must retain level and bound XP.
            for(int cap=0;cap<3;++cap) {
                Client capped=c;
                rules["Character:MaxLevel"]=cap==0?level:126;
                rules["Character:MaxExpLevel"]=cap==1?level:0;
                capped.client_max=cap==2?level:0;
                // Exactly next threshold avoids probing a potentially overflowing level+2.
                // At the end of the safe curve only the ordinary +1 case is used.
                bool safe_cross=true;
                try { capped.CheckedEXPForLevel(level+2); }
                catch(const std::overflow_error&) { safe_cross=false; }
                auto award=safe_cross?uint64(next)+1:uint64(xp)+2;
                capped.SetEXP(Kill,award,capped.m_pp.expAA);
                check(capped.level==level,"configured cap retains boosted level");
                check(capped.m_pp.exp==(safe_cross?next:xp+2),"configured cap bounds XP");
                rules["Character:MaxExpLevel"]=0;
            }
            ++stable;
        }
    }
    std::cerr<<checks<<" native checks, "<<failures<<" failures; "<<stable
             <<" stable profiles, "<<overflow<<" overflow rejections\n";
    return failures?1:0;
}
'''

JS_COMPARE = r'''
const fs = require('node:fs');
const { experienceForLevel } = require(process.argv[1]);
let checks = 0;
for (const line of fs.readFileSync(process.argv[2], 'utf8').trim().split('\n')) {
  const [level, race, cls, oldRace, oldClass, expected] = line.trim().split(' ');
  let actual;
  try {
    actual = String(experienceForLevel(Number(level), {race: Number(race), class: Number(cls),
      useOldRaceExpPenalties: oldRace === '1', useOldClassExpPenalties: oldClass === '1'}));
  } catch (error) {
    if (expected !== 'overflow') throw error;
    actual = 'overflow';
  }
  if (actual !== expected) throw new Error(`Native/JS mismatch ${line}: got ${actual}`);
  ++checks;
}
console.log(`${checks} native/JavaScript threshold comparisons passed`);
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++')
    parser.add_argument('--node', default='node')
    parser.add_argument('--source', type=pathlib.Path, default=ROOT / 'server-mods/code/zone/exp.cpp')
    parser.add_argument('--emit-only', type=pathlib.Path, help='write extracted C++ harness without compiling')
    args = parser.parse_args()
    source = args.source.read_text()
    threshold = function(source, 'uint32 Client::GetEXPForLevel')
    reconcile = function(source, 'void Client::SetEXP')
    # A second instrumented copy detects undefined float-to-uint32 conversions and
    # modifier narrowing before calling the original. No arithmetic is replaced.
    for expression in ('uint32(base * mod)', 'uint64(finalxp * racemod)', 'uint64(finalxp * classmod)'):
        if threshold.count(expression) != 1:
            raise RuntimeError('Server XP expression changed; review range probe: ' + expression)
    probe = threshold.replace('Client::GetEXPForLevel', 'Client::CheckedEXPForLevel')
    probe = probe.replace('uint32(base * mod)', 'checked(base * mod)')
    probe = probe.replace('uint64(finalxp * racemod)', 'checked(finalxp * racemod)')
    probe = probe.replace('uint64(finalxp * classmod)', 'checked(finalxp * classmod)')
    harness = PRELUDE + threshold + '\n' + probe + '\n' + reconcile + CASES
    if args.emit_only:
        args.emit_only.write_text(harness)
        return
    with tempfile.TemporaryDirectory(prefix='boost-xp-') as tmp:
        path = pathlib.Path(tmp)
        test = path / 'test.cpp'
        exe = path / ('test.exe' if os.name == 'nt' else 'test')
        test.write_text(harness)
        subprocess.run([args.compiler, '-std=c++11', '-O2', '-Wall', '-Wextra',
                        '-Wno-unused-parameter', str(test), '-o', str(exe)], check=True)
        table = path / 'thresholds.txt'
        with table.open('w') as output:
            subprocess.run([str(exe)], stdout=output, check=True)
        subprocess.run([args.node, '-e', JS_COMPARE,
                        str(ROOT / 'eq-solo-gm/api/lib/character-level.cjs'), str(table)], check=True)


if __name__ == '__main__':
    main()
