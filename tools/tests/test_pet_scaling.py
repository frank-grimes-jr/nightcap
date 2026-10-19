"""Execute production pet getters and proc execution with deterministic entities."""
from pathlib import Path
import unittest
from test_pet_equipment import compile_run, ROOT
from test_gameplay_policies import function

ZONE = ROOT / 'server-mods/code/zone'


class PetScaling(unittest.TestCase):
    def test_earned_owner_focus_eligibility_and_twinheal_limits(self):
        method=function((ZONE/'spell_effects.cpp').read_text(encoding='utf-8'),'int64 Mob::GetNightcapInheritedFocus(')
        fixture=r'''
#include <cstdint>
#include <map>
#include <stdexcept>
#include <iostream>
using int64=int64_t;using uint16=uint16_t;
enum focusType{focusImprovedHeal,focusImprovedDamage,focusImprovedDamage2,focusTwincast,focusReagentCost,focusOther};
struct Rank{int value=0;bool legal=true;};struct Ability{};
struct Zone{Ability ability;std::map<int,Rank>ranks;
 std::pair<Ability*,Rank*>GetAlternateAdvancementAbilityAndRank(int id,int){return {&ability,&ranks[id]};}
}world,*zone=&world;
bool IsBeneficialSpell(int spell){return spell<3;}bool IsInstantHealSpell(int spell){return spell==1;}
struct Mob{
 bool npc=true,doppel=false;Mob*owner=nullptr;Mob*clone_owner=nullptr;
 struct Bonuses{bool FocusEffects[6]{};}aabonuses;
 std::map<int,std::pair<int,int>>aa_ranks;
 bool IsNPC(){return npc;}Mob*CastToNPC(){return this;}bool IsNightcapDoppelganger(){return doppel;}
 Mob*GetNightcapDoppelgangerOwner(){return clone_owner;}Mob*GetNightcapPetOwner(){return owner;}
 bool CanUseAlternateAdvancementRank(Rank*r){return r->legal;}
 int64 CalcAAFocus(focusType,Rank&r,int){return r.value;}
 int64 GetFocusEffect(focusType,int){return 99;}
 int64 GetNightcapInheritedFocus(focusType,uint16);
};
// METHOD
void check(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 Mob pet,owner;pet.owner=&owner;owner.aa_ranks={{1,{1,0}},{2,{1,0}}};
 zone->ranks[1]={20,true};zone->ranks[2]={50,false};
 owner.aabonuses.FocusEffects[focusImprovedHeal]=true;
 check(pet.GetNightcapInheritedFocus(focusImprovedHeal,1)==20,"ineligible AA inherited or wrong focus");
 zone->ranks[2].legal=true;
 check(pet.GetNightcapInheritedFocus(focusImprovedHeal,1)==50,"same-category focuses added instead of strongest");
 owner.aabonuses.FocusEffects[focusTwincast]=true;
 check(pet.GetNightcapInheritedFocus(focusTwincast,1)==50,"instant-heal twincast excluded");
 check(pet.GetNightcapInheritedFocus(focusTwincast,2)==0,"HoT inherited Twinheal");
 check(pet.GetNightcapInheritedFocus(focusTwincast,3)==0,"DD inherited healing twincast");
 check(pet.GetNightcapInheritedFocus(focusOther,1)==0,"unreviewed focus inherited");
 pet.owner=nullptr;check(pet.GetNightcapInheritedFocus(focusImprovedHeal,1)==0,"hostile NPC inherited focus");
 pet.doppel=true;pet.clone_owner=&owner;
 check(pet.GetNightcapInheritedFocus(focusReagentCost,1)==99,"clone reagent conservation missing");
 pet.clone_owner=nullptr;check(pet.GetNightcapInheritedFocus(focusReagentCost,1)==0,"departed clone owner used");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHOD',method))

    def test_rune_scaling_uses_shared_item_formula_once(self):
        source = (ZONE / 'effects.cpp').read_text()
        methods = function(source, 'int32 Mob::GetNightcapRuneAmount(') + '\n' + function(source, 'int64 Mob::GetExtraSpellAmt(')
        fixture = r'''
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
using uint16=uint16_t;using int32=int32_t;using int64=int64_t;
struct Spell{bool no_heal_damage_item_mod=false;int recast_time=0,recovery_time=0,cast_time=0;}spells[2];
bool IsValidSpell(int id){return id==1;}
bool IsBardSong(int){return false;}
bool FlatItemExtraSpellAmt=true,ItemExtraSpellAmtCalcAsPercent=true;
#define RuleB(a,b) b
struct Mob{
 bool client=true,pet=false;int heal=750;
 bool IsClient(){return client;}Mob* GetNightcapPetOwner(){return pet?this:nullptr;}
 int GetHealAmt(){return heal;}
 int32 GetNightcapRuneAmount(uint16,int32);int64 GetExtraSpellAmt(uint16,int64,int64);
};
// METHODS
int main(){try{
 Mob caster;
 if(caster.GetNightcapRuneAmount(1,100)!=850)throw std::runtime_error("player/WPM rune scaling");
 // Native instrument scaling has already transformed a base 100 rune to 200.
 if(caster.GetNightcapRuneAmount(1,200)!=1700)throw std::runtime_error("instrument applied more than once");
 caster.client=false;caster.pet=true;caster.heal=897;
 if(caster.GetNightcapRuneAmount(1,100)!=997)throw std::runtime_error("pet own plus inherited rune output");
 caster.pet=false;if(caster.GetNightcapRuneAmount(1,100)!=100)throw std::runtime_error("hostile NPC rune changed");
 caster.client=true;spells[1].no_heal_damage_item_mod=true;
 if(caster.GetNightcapRuneAmount(1,100)!=100)throw std::runtime_error("spell opt-out ignored");
 spells[1].no_heal_damage_item_mod=false;caster.heal=-10;
 if(caster.GetNightcapRuneAmount(1,100)!=100)throw std::runtime_error("negative stat shrank rune");
 caster.heal=750;ItemExtraSpellAmtCalcAsPercent=false;
 if(caster.GetNightcapRuneAmount(1,100)!=850)throw std::runtime_error("configured flat mode ignored");
 ItemExtraSpellAmtCalcAsPercent=true;
 if(caster.GetNightcapRuneAmount(1,INT32_MAX)!=INT32_MAX)throw std::runtime_error("rune overflow");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHODS', methods))

    def test_roster_delivery_respects_affinity_range_and_individual_stacking(self):
        source = (ZONE / 'spells.cpp').read_text()
        method = function(source, 'bool Mob::SpellOnOwnedPets(')
        fixture = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint16=uint16_t;using uint8=uint8_t;using int16=int16_t;
constexpr int ST_GroupNoPets=39;
struct Spell{int target_type=0;float range=100,min_range=0;}spells[2];
bool IsValidSpell(int s){return s==1;}bool IsBeneficialSpell(int){return true;}
float DistanceSquared(float a,float b){return (a-b)*(a-b);}
struct Mob{
 int id=0,owner=1;bool client=false,affinity=true,charm=false,dead=false,stacks=true;
 float pos=0;std::vector<Mob*>roster;std::vector<int>landed;
 bool IsClient(){return client;}Mob* CastToClient(){return this;}
 std::vector<Mob*> GetCommandPets(){return roster;}Mob* GetPet(){return roster.empty()?nullptr:roster[0];}
 bool IsCharmed(){return charm;}bool HasDied(){return dead;}bool HasPetAffinity(){return affinity;}
 int GetOwnerID(){return owner;}int GetID(){return id;}float GetPosition(){return pos;}
 float GetAOERange(int){return 100;}float GetActSpellRange(int,float r){return r;}
 float GetRangeDistTargetSizeMod(Mob*){return 0;}void CalcSpellPowerDistanceMod(int,float){}
 bool SpellOnTarget(int,Mob*p,int,bool,int16,bool,uint8){if(p->stacks)landed.push_back(p->id);return p->stacks;}
 bool SpellOnOwnedPets(uint16,Mob*,bool=true,int16=0,uint8=0);
};
// METHOD
void check(bool ok,const char*w){if(!ok)throw std::runtime_error(w);}
int main(){try{
 Mob caster,owner,a,b,c;owner.client=true;owner.id=1;a.id=2;b.id=3;c.id=4;
 owner.roster={&a,&b,&c};
 check(caster.SpellOnOwnedPets(1,&owner),"roster cast failed");
 check(caster.landed==std::vector<int>{2,3,4},"selected pet substituted for whole roster");
 caster.landed.clear();owner.affinity=false;
 check(!caster.SpellOnOwnedPets(1,&owner),"group affinity bypassed");
 check(caster.SpellOnOwnedPets(1,&owner,false),"pet-only buff required group affinity");
 caster.landed.clear();owner.affinity=true;a.stacks=false;b.pos=101;
 check(caster.SpellOnOwnedPets(1,&owner),"one stacking failure stopped other pets");
 check(caster.landed==std::vector<int>{4},"range or stacking bypassed");
 caster.landed.clear();c.charm=true;
 check(!caster.SpellOnOwnedPets(1,&owner),"charmed pet received roster buff");
 c.charm=false;c.dead=true;check(!caster.SpellOnOwnedPets(1,&owner),"dead pet received buff");
 c.dead=false;c.owner=9;check(!caster.SpellOnOwnedPets(1,&owner),"foreign pet received buff");
 c.owner=1;spells[1].target_type=ST_GroupNoPets;
 check(!caster.SpellOnOwnedPets(1,&owner),"no-pets spell included pets");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHOD', method))

    def test_live_inheritance_and_separate_equipment_contribution(self):
        mob = (ZONE / 'mob.cpp').read_text()
        npc = (ZONE / 'npc.cpp').read_text()
        methods = '\n'.join(function(mob, signature) for signature in (
            'Mob *Mob::GetNightcapPetOwner(', 'int Mob::GetNightcapInheritedCasterBonus('))
        methods += '\n' + '\n'.join(function(npc, signature) for signature in (
            'int32 NPC::GetSpellDmg(', 'int32 NPC::GetHealAmt('))
        header = (ROOT / 'server-mods/code/common/nightcap_pet_scaling.h').as_posix()
        fixture = f'#include "{header}"\n' + r'''
#include <iostream>
#include <stdexcept>
using int32 = int32_t;
struct Bonus {
 int SpellDmg=0, HealAmt=0, CriticalSpellChance=0, SpellCritDmgIncrease=0, SpellCritDmgIncNoStack=0;
 int CriticalDoTChance=0, DotCritDmgIncrease=0, CriticalHealChance=0, CriticalHealOverTime=0;
};
struct Mob {
 bool client=false, npc=false, pet=false, charm=false, temp=false, lock=false, familiar=false;
 int ownerid=0; Bonus itembonuses, spellbonuses, aabonuses;
 bool IsClient()const{return client;} bool IsNPC()const{return npc;}
 bool IsPetOwnerClient()const{return pet;} bool IsCharmed()const{return charm;}
 bool IsTempPet()const{return temp;} bool IsTargetLockPet()const{return lock;}
 bool IsFamiliar()const{return familiar;} int GetOwnerID()const{return ownerid;}
 virtual int32 GetSpellDmg()const{return itembonuses.SpellDmg;}
 virtual int32 GetHealAmt()const{return itembonuses.HealAmt;}
 Mob *GetNightcapPetOwner() const;
 int GetNightcapInheritedCasterBonus(NightcapPetScaling::CasterBonus) const;
};
struct NPC : Mob {
 NPC(){npc=true;} int32 GetSpellDmg()const override; int32 GetHealAmt()const override;
};
struct Entities { Mob* owner=nullptr; Mob* GetMob(int id){return id==1?owner:nullptr;} } entity_list;
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
// METHODS
int main(){try{
 Mob owner; owner.client=true; entity_list.owner=&owner;
 owner.itembonuses.SpellDmg=822; owner.itembonuses.HealAmt=752;
 NPC pet; pet.pet=true; pet.ownerid=1; pet.itembonuses.SpellDmg=522; pet.itembonuses.HealAmt=522;
 check(pet.GetSpellDmg()==897 && pet.GetHealAmt()==897,"inheritance cap incorrectly caps whole pet");
 owner.itembonuses.SpellDmg=301; owner.itembonuses.HealAmt=100;
 check(pet.GetSpellDmg()==672 && pet.GetHealAmt()==572,"equipment change not live or rounded incorrectly");
 owner.itembonuses.SpellDmg=-2; check(pet.GetSpellDmg()==522,"negative owner inherited");
 owner.aabonuses.CriticalSpellChance=21; owner.spellbonuses.CriticalSpellChance=10;
 owner.aabonuses.SpellCritDmgIncrease=100;
 using B=NightcapPetScaling::CasterBonus;
 check(pet.GetNightcapInheritedCasterBonus(B::SpellChance)==15,"spell crit chance inheritance");
 check(pet.GetNightcapInheritedCasterBonus(B::SpellDamage)==50,"spell crit damage inheritance");
 owner.aabonuses.CriticalSpellChance=0; owner.spellbonuses.CriticalSpellChance=0;
 check(pet.GetNightcapInheritedCasterBonus(B::SpellChance)==0,"AA/class change not live");
 for(int mode=0;mode<7;++mode){
  pet.charm=mode==0;pet.temp=mode==1;pet.lock=mode==2;pet.familiar=mode==3;
  pet.pet=mode!=4;owner.client=mode!=5;pet.ownerid=mode==6?2:1;
  check(!pet.GetNightcapPetOwner(),"ineligible entity inherited owner");
  check(pet.GetSpellDmg()==522 && pet.GetHealAmt()==522,"ineligible entity inherited output");
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHODS', methods))

    def test_weapon_and_all_augment_attempts_for_owned_pets(self):
        source = (ZONE / 'attack.cpp').read_text()
        method = function(source, 'void Mob::TryWeaponProc(')
        fixture = r'''
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint16=uint16_t;
#define RuleB(a,b) true
#define LogCombat(...) ((void)0)
constexpr int PROC_PETTOOLOW=1,PROC_TOOLOW=2;
namespace Chat { constexpr int Red=1; }
namespace EQ {
namespace invslot { constexpr int slotPrimary=13,slotSecondary=14; }
namespace invaug { constexpr int SOCKET_BEGIN=0,SOCKET_END=5; }
namespace item { constexpr int ItemEffectCombatProc=0; }
struct ItemData { struct ProcData{int Type=0,Effect=0,Level2=1;}Proc;float ProcRate=0;const char* Name="item"; };
struct ItemInstance { ItemData data; std::array<ItemInstance*,6> augs{};
 const ItemData* GetItem()const{return &data;} const ItemInstance* GetAugment(int i)const{return augs[i];} };
}
bool IsValidSpell(int id){return id>0;}
struct Zone {struct Random{bool Roll(float){return true;}}random;} fixture_zone,*zone=&fixture_zone;
struct Bonus {int ProcChanceSPA=0,ProcChance=0;};
struct Mob {
 bool owned=true,client=false;Bonus aabonuses,spellbonuses,itembonuses;std::vector<int> procs;
 bool IsClient(){return client;}
 int GetLevel(){return 65;} float GetProcChances(float,int){return 1.0f;}
 Mob* GetNightcapPetOwner(){return owned?this:nullptr;} Mob* GetOwner(){return this;}
 bool IsPet(){return owned;} void MessageString(int,int){}
 void ExecWeaponProc(const EQ::ItemInstance*,int spell,Mob*){procs.push_back(spell);}
 void TryWeaponProc(const EQ::ItemInstance*,const EQ::ItemData*,Mob*,uint16);
};
// METHOD
int main(){try{
 Mob pet,target;EQ::ItemInstance weapon,heal,rune;
 weapon.data.Proc.Effect=1;heal.data.Proc.Effect=2;rune.data.Proc.Effect=3;
 weapon.augs[0]=&heal;weapon.augs[5]=&rune;
 pet.TryWeaponProc(&weapon,&weapon.data,&target,13);
 if(pet.procs!=std::vector<int>{1,2,3})throw std::runtime_error("innate proc suppressed healing or sixth-slot rune augment");
 pet.owned=false;pet.procs.clear();pet.TryWeaponProc(&weapon,&weapon.data,&target,13);
 if(pet.procs!=std::vector<int>{1})throw std::runtime_error("ordinary NPC proc policy changed");
 pet.client=true;pet.procs.clear();pet.TryWeaponProc(&weapon,&weapon.data,&target,13);
 if(pet.procs!=std::vector<int>{1,2,3})throw std::runtime_error("player innate proc suppressed augments");
 pet.client=false;
 pet.owned=true;pet.procs.clear();rune.data.Proc.Level2=66;
 pet.TryWeaponProc(&weapon,&weapon.data,&target,14);
 if(pet.procs!=std::vector<int>{1,2})throw std::runtime_error("level gate/offhand lost");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHOD', method))
        attack = function(source, 'bool NPC::Attack(')
        self.assertIn('TryWeaponProc(proc_instance, weapon, other, Hand)', attack)
        self.assertIn('equipped->GetID() == weapon->ID', attack)


if __name__ == '__main__':
    unittest.main()
