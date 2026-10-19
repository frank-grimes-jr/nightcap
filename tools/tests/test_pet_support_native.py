"""Execute native stacking and haste with captured pet-buff definitions."""
import os
from pathlib import Path
import re
import unittest
import pet_support_spells as policy
from test_pet_equipment import ROOT, compile_run
from test_gameplay_policies import function


class PetBuffNative(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('NIGHTCAP_NATIVE_SOURCE'),'retained full native source required')
    def test_native_stacking_and_haste(self):
        native=Path(os.environ['NIGHTCAP_NATIVE_SOURCE'])
        common=(native/'common/spdat.cpp').read_text(encoding='utf-8')
        header=(native/'common/spdat.h').read_text(encoding='utf-8')
        source=(ROOT/'server-mods/code/zone/spells.cpp').read_text(encoding='utf-8')
        methods='\n'.join([function(common,'bool IsBlankSpellEffect('),function(common,'bool IsEffectIgnoredInStacking('),
                           function(source,'int Mob::CheckStackConflict(')])
        code=re.sub(r'/\*.*?\*/|//[^\n]*','',methods,flags=re.S)
        names=set(re.findall(r'SpellEffect::(\w+)',code))
        constants=[]
        for name in sorted(names):
            value=re.search(r'constexpr int\s+'+name+r'\s*=\s*(\d+);',header)
            self.assertIsNotNone(value,name)
            constants.append(f'constexpr int {name}={value[1]};')
        haste=function((ROOT/'server-mods/code/zone/bonuses.cpp').read_text(encoding='utf-8'),'case SpellEffect::AttackSpeed:')
        fixture=r'''
#include <cstdint>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint16=uint16_t;using int8=int8_t;
namespace SpellEffect { // CONSTANTS
}
namespace Chat{constexpr int Red=1,SpellFailure=2;}
namespace Class{constexpr int Bard=8;}
namespace SBIndex{constexpr int BUFFSTACKER_EXISTS=0,BUFFSTACKER_VALUE=1;}
constexpr int EFFECT_COUNT=12,SPELL_EYE_OF_ZOMM=67,SPELL_MANA_BURN=2751,SPELL_NO_HOLD=1,SCREECH_BUFF_BLOCK=2;
struct SPDat_Spell_Struct{int effect_id[12]{},base_value[12]{},formula[12]{},max_value[12]{},buff_duration=100;const char*name="captured buff";}spells[4000];
bool IsValidSpell(int id){return id>0&&id<4000;}
bool IsEffectInSpell(int id,int effect){for(int i=0;i<12;++i)if(spells[id].effect_id[i]==effect)return true;return false;}
bool IsResurrectionEffects(int){return false;}bool IsStackableDOT(int){return false;}
bool IsBardSong(int){return false;}bool IsDetrimentalSpell(int){return false;}
bool IsCastOnFadeDurationSpell(int){return false;}bool IsBardOnlyStackEffect(int){return false;}
bool IsGroupSpell(int){return false;}int GetSpellLevel(int,int){return 255;}
int CalcSpellEffectValue(int id,int slot,int){return spells[id].base_value[slot];}
int GetSpellResurrectionSicknessCheck(int,int){return 0;}
namespace Strings {std::vector<std::string> Split(std::string,std::string){return{};}bool Contains(const std::vector<std::string>&,std::string){return false;}}
#define RuleS(a,b) std::string{}
#define RuleB(a,b) false
#define LogSpells(...) ((void)0)
struct Mob{
 bool IsClient(){return true;}
 struct Bonus{int CompleteHealBuffBlocker=0,Screech=0,AStacker[2]{},BStacker[2]{},CStacker[2]{},DStacker[2]{};}spellbonuses;
 struct Buff{int ticsremaining=0;}buffs[1];
 const char*GetName(){return "pet";}bool IsNPC(){return true;}
 void Message(...){}void MessageString(...){}
 int CheckStackConflict(uint16,int,uint16,int,Mob*,Mob*,int);
};
// METHODS
int GetSlowMitigation(){return 0;}
struct Haste{int haste=0;};
void AddHaste(Haste*new_bonus,int effect_value){switch(11){
// HASTE
}}
void check(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 Mob pet;
// ORIGINALS
 check(pet.CheckStackConflict(3237,65,3305,65,&pet,&pet,0)!=0,"baseline conflict not reproduced");
// AFTERIMAGES
 for(int mage:{327,106,107,1472,2119,3237})for(int nec:{661,1414,3305})for(int bst:{1430,2619}){
  for(auto pair:std::vector<std::pair<int,int>>{{mage,nec},{nec,mage},{mage,bst},{bst,mage},{nec,bst},{bst,nec}})
   check(pet.CheckStackConflict(pair.first,65,pair.second,65,&pet,&pet,0)==0,"cross-class buff rejected/overwritten");
 }
 check(pet.CheckStackConflict(661,65,1414,65,&pet,&pet,0)!=0,"same-class ranks started stacking");
 Haste haste;AddHaste(&haste,150);AddHaste(&haste,175);AddHaste(&haste,160);
 check(haste.haste==75,"ordinary haste added instead of strongest winning");
 AddHaste(&haste,30);AddHaste(&haste,175);check(haste.haste==-70,"haste bypassed slow");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        def load(rows):
            lines=[]
            for row in rows:
                for field,prefix in [('effect_id','effectid'),('base_value','effect_base_value'),('formula','formula'),('max_value','max')]:
                    lines += [f"spells[{row['id']}].{field}[{i-1}]={row[f'{prefix}{i}']};" for i in range(1,13)]
            return '\n'.join(lines)
        rows=policy.fixture_rows()
        fixture=fixture.replace('// CONSTANTS','\n'.join(constants)).replace('// METHODS',methods).replace('// HASTE',haste)
        fixture=fixture.replace('// ORIGINALS',load(rows)).replace('// AFTERIMAGES',load([policy.afterimage(r) for r in rows if r['id'] in policy.IDS]))
        compile_run(fixture)


if __name__=='__main__': unittest.main()
