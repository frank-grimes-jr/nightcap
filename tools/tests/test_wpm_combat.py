"""Run actual combat-policy methods with deterministic class and RNG boundaries."""
import unittest
from test_gameplay_policies import function
from test_pet_equipment import ROOT, compile_run

ZONE = ROOT / 'server-mods/code/zone'


class WPMCombat(unittest.TestCase):
    def test_all_class_orders_and_single_class_mitigation(self):
        source = (ZONE / 'attack.cpp').read_text()
        methods = '\n'.join(function(source, signature) for signature in (
            'bool Mob::HasCombatClass(', 'uint8 Mob::GetMitigationClass(',
            'bool Mob::UsesKnightDoubleAttack(', 'int Mob::GetACSoftcap(',
            'double Mob::GetSoftcapReturns(', 'bool Client::CheckDoubleAttack(', 'bool Client::CheckTripleAttack('))
        fixture = r'''
#include <algorithm>
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <iostream>
#include <cmath>
using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using int32=int32_t;
namespace Class {enum {Warrior=1,Cleric,Paladin,Ranger,ShadowKnight,Druid,Monk,Bard,Rogue,Shaman,Necromancer,Wizard,Magician,Enchanter,Beastlord,Berserker};}
namespace EQ {namespace skills {constexpr int SkillDoubleAttack=22,SkillTripleAttack=46;}}
#define LogCombatDetail(...) ((void)0)
bool classic=true;
#define RuleB(category,name) classic
#define RuleI(category,name) 200
struct Zone {struct Random {double chance=0;int Int(int,int){return 1;}bool Roll(double c){chance=c;return c>=0.5;}}random;} z,*zone=&z;
struct Mob {
 bool client=true;uint8 cls=1,level=65;std::vector<uint8>held{1};bool twohand=false;
 int skill=200;
 struct Bonuses{int GiveDoubleAttack=0,DoubleAttackChance=0,TripleAttackChance=0;}aabonuses,spellbonuses,itembonuses;
 bool IsClient()const{return client;}const Mob*CastToClient()const{return this;}
 bool IsMulticlassMember(uint8 c)const{return std::find(held.begin(),held.end(),c)!=held.end();}
 uint8 GetClass()const{return cls;}uint8 GetLevel()const{return level;}
 bool HasCombatClass(uint8)const;uint8 GetMitigationClass()const;bool UsesKnightDoubleAttack()const;
 bool HasTwoHanderEquipped()const{return twohand;}bool HasSkill(int)const{return skill>0;}int GetSkill(int)const{return skill;}
 int GetACSoftcap();double GetSoftcapReturns();
};
struct Client:Mob {bool CheckDoubleAttack();bool CheckTripleAttack();};
// METHODS
void check(bool ok,const char*msg){if(!ok)throw std::runtime_error(msg);}
int main(){try{
 std::vector<uint8> order{1,3,7};int n=0;
 do {Client c;c.held=order;c.cls=order[0];c.aabonuses.DoubleAttackChance=50;
  check(c.GetMitigationClass()==1,"primary-dependent mitigation class");
  check(c.GetACSoftcap()==440 && c.GetSoftcapReturns()==0.35,"WPM mitigation mismatch");
  check(c.HasCombatClass(7) && c.HasCombatClass(1),"held combat capability missing");
  c.CheckDoubleAttack();check(std::abs(z.random.chance-0.795)<0.0001,"knight primary suppressed WPM double attack");++n;
  check(c.CheckTripleAttack(),"held Warrior/Monk classic triple attack missing");
  c.level=59;check(!c.CheckTripleAttack(),"classic triple attack below level60");
 }while(std::next_permutation(order.begin(),order.end()));check(n==6,"class permutation coverage");
 Client knight;knight.cls=3;knight.held={3};knight.aabonuses.DoubleAttackChance=50;
 check(!knight.CheckTripleAttack(),"single knight gained classic triple attack");
 knight.CheckDoubleAttack();check(std::abs(z.random.chance-0.53)<0.0001,"single knight 1H changed");
 knight.twohand=true;knight.CheckDoubleAttack();check(std::abs(z.random.chance-0.795)<0.0001,"single knight 2H changed");
 knight.twohand=false;knight.cls=12;knight.held={12,3};
 knight.CheckDoubleAttack();check(std::abs(z.random.chance-0.53)<0.0001,"caster/knight order changed restriction");
 Client npc;npc.client=false;npc.cls=12;npc.held={1,7};
 check(!npc.HasCombatClass(1) && npc.GetMitigationClass()==12,"NPC borrowed player capabilities");
 check(npc.GetSoftcapReturns()==0.25,"NPC softcap changed");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHODS', methods))

    def test_heroic_curve_is_bounded_to_player_weapon_hits(self):
        header = (ROOT / 'server-mods/code/common/nightcap_melee.h').as_posix()
        compile_run(f'#include "{header}"\n' + r'''
#include <stdexcept>
#include <iostream>
#include <cmath>
int main(){try{
 using namespace NightcapMelee;
 if(HeroicDamagePercent(-1)!=0 || HeroicDamagePercent(0)!=0 || HeroicDamagePercent(100)!=100)
  throw std::runtime_error("heroic boundaries");
 if(std::abs(HeroicDamagePercent(200)-172.5)>0.00001)throw std::runtime_error("declining marginal gain");
 if(std::abs(HeroicDamagePercent(1000)-HeroicDamagePercent(999)-1.0/3.0)>0.00001)
  throw std::runtime_error("marginal floor");
 for(int skill=0;skill<80;++skill){bool expected=skill==0||skill==1||skill==2||skill==3||skill==28||skill==36||skill==77;
  if(IsWeaponSkill(skill)!=expected)throw std::runtime_error("special or ranged received autoattack multiplier");}
 if(ScaleHeroicHit(100,100)!=200 || ScaleHeroicHit(-5,100)!=-5)throw std::runtime_error("damage/sentinel scaling");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
''')
        outgoing=function((ZONE/'attack.cpp').read_text(),'void Mob::CommonOutgoingHitSuccess(')
        self.assertIn('IsClient() && RuleB(Combat, NightcapHeroicMeleeScaling)', outgoing)
        self.assertEqual(outgoing.count('NightcapMelee::ScaleHeroicHit('),1)


if __name__ == '__main__': unittest.main()
