"""Native recipient, focus-filter, and worn proc paths with controlled boundaries."""
import unittest
import wpm_content
from test_gameplay_policies import function
from test_pet_equipment import ROOT, compile_run

ZONE=ROOT/'server-mods/code/zone'
HEADER=(ROOT/'server-mods/code/common/nightcap_melee.h').as_posix()


class WPMEffects(unittest.TestCase):
    def test_recipient_and_worn_proc_eligibility(self):
        source=(ZONE/'attack.cpp').read_text()
        methods='\n'.join(function(source,s) for s in ('uint64 Mob::GetNightcapHealingReceived(', 'void Mob::TryWornWeaponProc('))
        fixture=r'''
#include <algorithm>
#include <cstdint>
#include <cassert>
#include <vector>
using uint64=uint64_t;
namespace EQ {namespace invslot {constexpr int slotSecondary=14;} namespace item {constexpr int ItemTypeShield=8;}
namespace skills {enum SkillType {Slash};}}
namespace SBIndex {enum {COMBAT_PROC_ORIGIN_ID,COMBAT_PROC_SPELL_ID,COMBAT_PROC_RATE_MOD,COMBAT_PROC_REUSE_TIMER};}
namespace ProcType {constexpr int MELEE_PROC=0;}
constexpr int MAX_AA_PROCS=16;
struct Item {int ItemType=8;struct {int Effect=42845;}Worn;};
struct Instance {Item item;int level=65;const Item*GetItem()const{return &item;}int GetItemRequiredLevel(bool)const{return level;}};
struct Inventory {Instance *equipped=nullptr;const Instance*GetItem(int)const{return equipped;}};
struct Zone {struct {int rolls=0;bool Roll(float chance){++rolls;return chance>=1.0;}}random;}z,*zone=&z;
bool IsValidSpell(int id){return id==42846;}
struct Mob {
 bool client=true,pet=false,limit=true;int level=65;Inventory inv;std::vector<int>procs;
 struct {int SpellProc[MAX_AA_PROCS]{};}itembonuses;
 bool IsClient()const{return client;}bool GetNightcapPetOwner()const{return pet;}auto&GetInv(){return inv;}int GetLevel()const{return level;}
 bool PassLimitToSkill(EQ::skills::SkillType,int,int){return limit;}
 void ExecWeaponProc(void*,int id,Mob*){procs.push_back(id);}
 uint64 GetNightcapHealingReceived(uint64);void TryWornWeaponProc(Mob*,EQ::skills::SkillType,float);
};
// METHODS
int main(){
 Mob m,target;Instance shield;m.inv.equipped=&shield;
 assert(m.GetNightcapHealingReceived(300)==330); // caster focus has already resolved
 assert(m.GetNightcapHealingReceived(0)==0);
 assert(m.GetNightcapHealingReceived(UINT64_MAX)==UINT64_MAX);
 m.inv.equipped=nullptr;assert(m.GetNightcapHealingReceived(300)==300);
 m.inv.equipped=&shield;m.level=64;assert(m.GetNightcapHealingReceived(300)==300);
 m.level=65;shield.item.ItemType=0;assert(m.GetNightcapHealingReceived(300)==300);
 shield.item.ItemType=8;m.client=false;assert(m.GetNightcapHealingReceived(300)==300);
 m.pet=true;assert(m.GetNightcapHealingReceived(300)==330);
 m.itembonuses.SpellProc[0]=42847;m.itembonuses.SpellProc[1]=42846;
 m.TryWornWeaponProc(&target,EQ::skills::Slash,1.0f);assert(m.procs.size()==1);
 m.pet=false;m.TryWornWeaponProc(&target,EQ::skills::Slash,1.0f);assert(m.procs.size()==1);
 m.client=true;m.limit=false;m.TryWornWeaponProc(&target,EQ::skills::Slash,1.0f);assert(m.procs.size()==1);
 m.limit=true;m.TryWornWeaponProc(nullptr,EQ::skills::Slash,1.0f);assert(m.procs.size()==1);
 m.itembonuses={};m.TryWornWeaponProc(&target,EQ::skills::Slash,1.0f);assert(m.procs.size()==1);
}
'''
        compile_run('#include "'+HEADER+'"\n'+fixture.replace('// METHODS',methods))

    def test_native_focus_filters_accept_only_paid_instant_heals_in_level_band(self):
        source=(ZONE/'spell_effects.cpp').read_text()
        native=function(source,'int64 Mob::CalcFocusEffect(')
        # Compile these unchanged switch arms, including the native return paths.
        names=['LimitInstant','LimitMinLevel','LimitSpellType','LimitManaMin']
        cases=[]
        for name in names:
            start=native.index('case SpellEffect::'+name+':')
            end=native.find('\n\t\t\tcase SpellEffect::',start+1)
            cases.append(native[start:end])
        fixture=r'''
#include <cassert>
#include <cstdint>
using uint8=uint8_t;
namespace SpellEffect {enum {LimitInstant=141,LimitMinLevel=142,LimitSpellType=138,LimitManaMin=348};}
#define LogInfo(...) ((void)0)
struct Spell {int buff_duration=0,mana=10;int effect_id[4],base_value[4];};
bool beneficial=true;
bool IsDetrimentalSpell(int){return !beneficial;}bool IsBeneficialSpell(int){return beneficial;}
struct Mob {int minimum=50;bool IsNPC()const{return false;}int GetFocusSpellLevel(int){return minimum;}
 int Check(const Spell&focus_spell,const Spell&spell){int spell_id=1;for(int i=0;i<4;++i){switch(focus_spell.effect_id[i]){
// CASES
 }}return 1;}};
int main(){Mob m;Spell f,s;int ids[]={141,142,138,348};int bases[]={1,50,1,10};
 for(int i=0;i<4;++i){f.effect_id[i]=ids[i];f.base_value[i]=bases[i];}
 assert(m.Check(f,s)==1);s.mana=0;assert(m.Check(f,s)==0);s.mana=10;
 beneficial=false;assert(m.Check(f,s)==0);beneficial=true;s.buff_duration=1;assert(m.Check(f,s)==0);
 s.buff_duration=0;m.minimum=49;assert(m.Check(f,s)==0);
}
'''
        compile_run(fixture.replace('// CASES','\n'.join(cases)))
        rows={r['id']:r for r in wpm_content.spell_rows()}
        for sid in (42843,42844):
            effects={rows[sid][f'effectid{i}']:rows[sid][f'effect_base_value{i}'] for i in range(1,13)}
            self.assertEqual(effects[141],1)
            self.assertEqual(effects[138],1)
            self.assertEqual(effects[348],10) # no recursive zero-mana proc healing


if __name__=='__main__':unittest.main()
