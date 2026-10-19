import unittest
from test_pet_equipment import compile_run,ROOT
from test_gameplay_policies import function
class Focus(unittest.TestCase):
    def test_actual_focus_projection_player_pet_bard_and_mage(self):
        native=function((ROOT/'server-mods/code/zone/spell_effects.cpp').read_text(),'int64 Mob::CalcFocusEffect(')
        start=native.index('\tconst bool thj =');end=native.index('\tint64  value',start)
        code=native[start:end]
        fixture=r'''
#include <cassert>
#include <cstdint>
#include <algorithm>
// HEADER
constexpr int EFFECT_COUNT=12;
namespace SpellEffect {enum {LimitMinDur=140};}
enum {focusImprovedDamage=1,focusImprovedDamage2,focusImprovedHeal,focusManaCost,focusReagentCost,focusSpellHateMod,focusOther};
struct Spell {int effect_id[12]={},base_value[12]={};};
struct Mob {
 bool enabled=true,client=true,permanent=false;int random_calls=0;
 bool IsClient(){return client;}bool GetNightcapPetOwner(){return permanent;}
 bool IsBardSong(int id){return id==4085||id==50000;}
 int GetFocusRandomEffectivenessValue(int base,int limit,bool best){++random_calls;return best?std::max(base,limit):base;}
 int run(int type,int focus_id,int spell_id,int base,int limit,bool dot=false){Spell focus_spell;if(dot){focus_spell.effect_id[0]=140;focus_spell.base_value[0]=3;}
#define RuleB(group,key) enabled
// ACTUAL
 return focus_value(base,limit,false);
 }
};
int main(){Mob m;assert(m.run(focusImprovedDamage,100,101,10,20)==200);assert(m.random_calls==0);
assert(m.run(focusImprovedHeal,100,101,10,20)==20);assert(m.run(focusSpellHateMod,100,101,-10,-20)==-20);
assert(m.run(focusImprovedDamage,5915,101,100,100)==100);assert(m.run(focusImprovedDamage,11064,101,150,150)==150);
assert(m.run(focusImprovedDamage,4085,101,10,20)==100);assert(m.run(focusImprovedDamage,4085,101,10,20,true)==10);
assert(m.run(focusImprovedDamage,100,50000,10,20)==0);
m.client=false;assert(m.run(focusImprovedDamage,100,101,10,20)==10);m.permanent=true;assert(m.run(focusImprovedDamage,100,101,10,20)==200);
m.enabled=false;assert(m.run(focusImprovedDamage,100,101,10,20)==10);
}
'''
        fixture=fixture.replace('// HEADER','#include "'+(ROOT/'server-mods/code/common/nightcap_thj_behaviors.h').as_posix()+'"').replace('// ACTUAL',code)
        compile_run(fixture)
if __name__=='__main__':unittest.main()
