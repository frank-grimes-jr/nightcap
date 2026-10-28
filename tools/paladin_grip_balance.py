"""Native damage-bonus/proc diagnostic, not a full combat or encounter simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/tests'))
from test_free_trade import FreeTradeTests, body
from paladin_grip_preflight import profiles


def measure():
    source=(ROOT/'server-mods/code/zone/attack.cpp').read_text(encoding='utf-8')
    bonus=body(source,'uint8 Mob::GetWeaponDamageBonus(')
    proc=body(source,'float Mob::GetProcChances(')
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/'results.json'
        fixture=r'''
#include "common/paladin_weapon_grip.h"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using int64=int64_t;
constexpr bool UseAltSinisterStrikeFormula=false;
static bool AdjustProcPerMinute=true;
constexpr float AvgProcsPerMinute=2.0f,ProcPerMinDexContrib=0.075f,BaseProcChance=0.035f,ProcDexDivideBy=11000.0f;
#define RuleB(c,r) r
#define RuleR(c,r) r
#define LogCombat(...) ((void)0)
namespace EQ {namespace item {constexpr int ItemTypeMartial=45;}
struct ItemData {uint8 Delay;int ItemType;bool IsType1HWeapon()const{return ItemType==0;}};}
struct Mob {
 uint8 current_level=50;uint32 speed=3000;
 uint8 GetLevel()const{return current_level;} int GetDEX()const{return 255;}
 uint32 GetWeaponSpeedbyHand(uint16)const{return speed;}
 uint8 GetWeaponDamageBonus(const EQ::ItemData*,bool=false);
 float GetProcChances(float,uint16);
};
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4244)
#endif
''' + bonus + '\n' + proc + r'''
#ifdef _MSC_VER
#pragma warning(pop)
#endif
int main(){
 std::ofstream out(R"PATH(OUTPUT)PATH");out<<"[";bool first=true;
 for(const auto &p:NightcapPaladinGrip::Profiles) {
  Mob m;EQ::ItemData one{p.one_hand_delay,0},two{p.two_hand_delay,1};
  m.speed=uint32(p.one_hand_delay)*100;float ppm_one=m.GetProcChances(0,13)*60000/m.speed;
  m.speed=uint32(p.two_hand_delay)*100;float ppm_two=m.GetProcChances(0,13)*60000/m.speed;
  assert(std::abs(ppm_one-ppm_two)<0.00001f);
  for(int level:{1,20,28,40,50})for(int augment:{0,5,10})for(int shield:{0,100}) {
   m.current_level=static_cast<uint8>(level);
   int b1=level>=28?m.GetWeaponDamageBonus(&one):0,b2=level>=28?m.GetWeaponDamageBonus(&two):0;
   // Normalized landed-damage index at a fixed 2x weapon term; excludes hit,
   // mitigation/crit/Slay distributions, multi-attacks and stance spells.
   double i1=(2.0*(p.one_hand_damage+augment)*(100+shield)/100+b1)*10/p.one_hand_delay;
   double i2=(2.0*(p.two_hand_damage+augment)+b2)*10/p.two_hand_delay;
   if(!augment && !(i1<i2)) {std::cerr<<p.id<<" level "<<level<<" shield "<<shield<<" indices "<<i1<<"/"<<i2<<" bonuses "<<b1<<"/"<<b2<<"\n";}
   if(!augment)assert(i1<i2);
   if(!first)out<<",";first=false;
   out<<"{\"id\":"<<p.id<<",\"level\":"<<level<<",\"augment_damage\":"<<augment
      <<",\"shield_percent\":"<<shield<<",\"one_hand_bonus\":"<<b1<<",\"two_hand_bonus\":"<<b2
      <<",\"one_hand_index\":"<<i1<<",\"two_hand_index\":"<<i2<<",\"normalized_ppm\":"<<ppm_one<<"}";
  }
 }
 out<<"]";
}
'''
        FreeTradeTests().compile_run(fixture.replace('OUTPUT',output.as_posix()))
        rows=json.loads(output.read_text())
    return {'scope':'Actual native damage bonus and normalized proc functions; diagnostic index, not measured combat DPS',
            'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'profile_sha256':hashlib.sha256((ROOT/'server-mods/code/common/paladin_weapon_grip.h').read_bytes()).hexdigest(),
            'profiles':profiles(),'rows':rows,
            'limitations':['No full native encounter build while Docker is unavailable',
                           'Augment +5/+10 are sensitivity cases, not proven currently obtainable loadouts',
                           'Normalized PPM uses October23 captured rules; confirm current rules at deployment',
                           'Shield Specialist 100% and Knights Advantage24% verified against captured AA policy',
                           'Martial multiclass retains double-attack bonuses in both grips; no knight penalty assumed here',
                           'Augmented or specialized builds can reverse ordering; no universal 2H DPS superiority claim']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=measure()
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS:',len(result['rows']),'native-function diagnostic cases; normalized proc cadence preserved')
