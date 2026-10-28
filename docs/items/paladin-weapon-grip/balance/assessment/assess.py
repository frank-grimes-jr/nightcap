"""Reproducible design assessment, not a gameplay patch or encounter simulator."""
import hashlib, json, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'server-mods').is_dir())
sys.path.insert(0, str(ROOT/'tools/tests'))
from test_free_trade import FreeTradeTests, body

# Explicit proposed values; existing items are not edited by this program.
PROFILES = [
    dict(id=605504, name='Ascended SoulFire', one=26, delay=30, two=46, two_delay=45, accuracy=10, block=0),
    dict(id=611050, name='Ascended Fiery Avenger', one=30, delay=30, two=66, two_delay=44, accuracy=15, block=1),
    dict(id=10099, name='Fiery Defender', one=32, delay=30, two=64, two_delay=40, accuracy=20, block=2),
    dict(id=810099, name='Ascended Fiery Defender', one=36, delay=30, two=72, two_delay=40, accuracy=25, block=3),
    dict(id=605403, name='Ascended Ghoulbane', one=30, delay=34, two=0, two_delay=0, accuracy=0, block=0),
    dict(id=605158, name='Ascended Sword of the Morning', one=32, delay=27, two=0, two_delay=0, accuracy=5, block=0),
    dict(id=605057, name='Ascended Wurmslayer', one=50, delay=40, two=0, two_delay=0, accuracy=0, block=0),
    dict(id=5504, name='SoulFire', one=13, delay=30, two=23, two_delay=45, accuracy=4, block=0),
    dict(id=205504, name='Polished SoulFire', one=18, delay=30, two=31, two_delay=45, accuracy=6, block=0),
    dict(id=405504, name='Exalted SoulFire', one=22, delay=30, two=38, two_delay=45, accuracy=8, block=0),
    dict(id=11050, name='Fiery Avenger', one=15, delay=30, two=33, two_delay=44, accuracy=5, block=0),
    dict(id=211050, name='Polished Fiery Avenger', one=20, delay=30, two=44, two_delay=44, accuracy=8, block=0),
    dict(id=411050, name='Exalted Fiery Avenger', one=25, delay=30, two=55, two_delay=44, accuracy=12, block=1),
]

def hit(a, d):
    # Roll0 samples [0,N-1]; ties win 50%. Both inputs are positive integer ratings.
    assert a > 0 and d > 0
    return 1-d/(2*a) if a >= d else a/(2*d)

def native_rows():
    source=(ROOT/'server-mods/code/zone/attack.cpp').read_text(encoding='utf-8')
    bonus=body(source,'uint8 Mob::GetWeaponDamageBonus(')
    caps=body(source,'int64 Mob::DoDamageCaps(')
    records=[]
    for p in PROFILES:
        records.append('{%d,%d,%d,%d,%d}'%(p['id'],p['one'],p['delay'],p['two'],p['two_delay']))
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'native.json'
        cpp=r'''
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <initializer_list>
#include <cassert>
using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using int64=int64_t;
constexpr bool UseAltSinisterStrikeFormula=false;
constexpr int LevelToStopDamageCaps=0;
#define RuleB(c,r) r
#define RuleI(c,r) r
namespace Class {constexpr int Cleric=2,Druid=6,Shaman=10,Necromancer=11,Wizard=12,Magician=13,Enchanter=14;}
namespace EQ {namespace item {constexpr int ItemTypeMartial=45;}
struct ItemData {uint8 Delay;int ItemType;bool IsType1HWeapon()const{return ItemType==0;}};}
struct Mob {
 uint8 current_level=50;int cls=3;
 uint8 GetLevel()const{return current_level;} int GetClass()const{return cls;}
 uint8 GetWeaponDamageBonus(const EQ::ItemData*,bool=false);
 int64 DoDamageCaps(int64);
};
#ifdef _MSC_VER
#pragma warning(disable:4244)
#endif
''' + bonus + '\n' + caps + r'''
int main(){
 struct Profile {int id,one,delay,two,two_delay;};
 Profile profiles[]={PROFILES};
 std::ofstream out(R"PATH(OUTPUT)PATH");out<<"[";bool first=true;
 for(const auto &p:profiles)for(int level:{1,10,20,30,40,45,50,60})for(int cls:{3,1,2,12})for(int aug:{0,5,10}){
  Mob m;m.current_level=static_cast<uint8>(level);m.cls=cls;
  EQ::ItemData one{static_cast<uint8>(p.delay),0},two{static_cast<uint8>(p.two_delay),1};
  // Bonus column is the native function's return. Main comparison uses Paladin;
  // alternate class rows test caps only, not melee eligibility/multiclass ownership.
  int b1=level>=28?m.GetWeaponDamageBonus(&one):0;
  int b2=level>=28 && p.two?m.GetWeaponDamageBonus(&two):0;
  if(!first)out<<",";first=false;
  out<<"{\"id\":"<<p.id<<",\"level\":"<<level<<",\"primary_class\":"<<cls<<",\"augment\":"<<aug
   <<",\"one_capped\":"<<m.DoDamageCaps(p.one+aug)<<",\"two_capped\":"<<(p.two?m.DoDamageCaps(p.two+aug):0)
   <<",\"one_bonus\":"<<b1<<",\"two_bonus\":"<<b2<<"}";
 }
 Mob m;m.current_level=20;assert(m.DoDamageCaps(46)==30);m.current_level=1;assert(m.DoDamageCaps(46)==10);
 out<<"]";
}
'''
        FreeTradeTests().compile_run(cpp.replace('PROFILES',','.join(records)).replace('OUTPUT',out.as_posix()))
        rows=json.loads(out.read_text())
    return rows

def main():
    rows=native_rows()
    # Independent enumeration of opposed roll boundaries, not Monte Carlo.
    for a,d in [(1,1),(3,7),(7,3),(500,500),(510,500),(565,600)]:
        enumerated=sum(1 if x>y else .5 if x==y else 0 for x in range(a) for y in range(d))/(a*d)
        assert abs(hit(a,d)-enumerated)<1e-12
    marginal=[]
    for rating in [300,565,800]:
        for defense in [400,600,800]:
            for existing in [0,140,150]:
                for bonus in [0,5,10,15,20,25,30,50,100]:
                    before=hit(rating+min(existing,150),defense)
                    after=hit(rating+min(existing+bonus,150),defense)
                    marginal.append(dict(rating=rating,defense=defense,existing_accuracy=existing,bonus=bonus,
                                         before=before,after=after,relative_gain=after/before-1))
    matrix=[]
    for r in rows:
        if r['primary_class']!=3: continue
        p=next(p for p in PROFILES if p['id']==r['id'])
        for shield in [0,100]:
            for coefficient in [1,2,3]:
                for defense in [400,600,800]:
                    # Level50 comparison uses captured Paladin skill caps (Offense200+weapon250).
                    # Other-level rows isolate caps/bonus sensitivity using a fixed rating, not level-specific DPS.
                    chance=hit(565+p['accuracy'],defense)
                    one=(coefficient*(r['one_capped']*(100+shield)//100)+r['one_bonus'])*10/p['delay']*chance
                    two=(coefficient*r['two_capped']+r['two_bonus'])*10/p['two_delay']*chance if p['two'] else None
                    matrix.append(dict(**r,shield=shield,coefficient=coefficient,defense=defense,hit_chance=chance,
                                       one_index=one,two_index=two,one_over_two=one/two if two else None))
    blocking=[]
    for existing in [0,5,20]:
        for added in [0,1,2,3,5,10]:
            blocking.append(dict(existing=existing,added=added,new_roll=existing+added,
                                 conditional_damage_reduction=added/(100-existing),
                                 conditional_ehp_gain=(100-existing)/(100-existing-added)-1))
    double_attack=[]
    for p in PROFILES[:4]:
        r=next(r for r in matrix if r['id']==p['id'] and r['level']==50 and r['augment']==0 and r['shield']==100 and r['coefficient']==2 and r['defense']==600)
        # Isolate captured Knight's Advantage +24 with Paladin double-attack skill225.
        # Native CheckDoubleAttack formula; excludes triple/flurry/extra attack effects.
        one_attacks=1+(225+50)/500
        two_attacks=1+(225+50)*1.24/500
        double_attack.append(dict(id=p['id'],one_attacks=one_attacks,two_attacks=two_attacks,
                                  one_over_two=r['one_over_two']*one_attacks/two_attacks))
    sources=[ROOT/'server-mods/code/zone/attack.cpp',ROOT/'server-mods/code/zone/bonuses.cpp',
             Path('E:/EQ_Local_Dev/akk-stack/code/common/random.h'),HERE/'public-stats-reference.json',
             ROOT/'docs/quests/camil-chapterhouse/balance-public-content.json.gz',Path(__file__)]
    result=dict(status='ASSESSMENT ONLY: no gameplay patch, no release-ready balance claim',profiles=PROFILES,
                model='Native caps and damage bonus; analytical opposed-hit rolls; fixed weapon coefficient sensitivity, equal swing opportunities; excludes full damage interval/crit/slay/multiattack/stances/heroics/procs/encounters',
                sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                native=rows,accuracy=marginal,shield_block=blocking,comparisons=matrix,double_attack_sensitivity=double_attack)
    (HERE/'assessment-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'native_cases':len(rows),'comparison_cases':len(matrix),'accuracy_cases':len(marginal),'block_cases':len(blocking),'enumerated_hit_checks':6}))
    print('LEVEL50/noaug/coefficient2/defense600, comparative indices (NOT DPS):')
    for shield in [0,100]:
        print('shield',shield)
        for r in matrix:
            if r['level']==50 and r['augment']==0 and r['coefficient']==2 and r['defense']==600 and r['shield']==shield:
                print(r['id'],round(r['hit_chance']*100,3),round(r['one_index'],3),round(r['two_index'],3) if r['two_index'] else None)

if __name__=='__main__': main()
