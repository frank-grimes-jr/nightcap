"""Threshold and capability contract for the native clone spell scheduler."""
import unittest
from test_pet_equipment import compile_run, ROOT
from test_gameplay_policies import function


class Doppelganger(unittest.TestCase):
    def test_native_owner_payment_and_reagent_completion(self):
        source=(ROOT/'server-mods/code/zone/npc.cpp').read_text(encoding='utf-8')
        methods='\n'.join(function(source,s) for s in ('bool DoppelHasReagents(',
                'bool NPC::PrepareNightcapDoppelgangerCast(', 'void NPC::CompleteNightcapDoppelgangerCast('))
        header=(ROOT/'server-mods/code/common/nightcap_doppelganger.h').as_posix()
        fixture=f'#include "{header}"\n'+r'''
#include <algorithm>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <iostream>
using uint16=uint16_t;using uint32=uint32_t;using int32=int32_t;using int64=int64_t;
constexpr int invWhereWorn=1,invWherePersonal=2,focusReagentCost=0;
struct Spell{int mana=50,component[4]={-1,-1,-1,-1},component_count[4]={1,1,1,1},no_expend_reagent[4]={-1,-1,-1,-1};uint32 recast_time=6000,recovery_time=1500;}spells[2];
uint64_t DoppelNow(){return 10000;}
struct Mob{float hp=20;float GetHPRatio(){return hp;}};
struct Inventory{std::map<int,int>counts;int HasItem(int id,int n,int){return counts[id]>=n?id:-1;}};
struct Client:Mob{
 int mana=100,focus=0,deleted=0;Inventory inv;
 Inventory& GetInv(){return inv;}int GetMana(){return mana;}void SetMana(int value){mana=value;}
 int GetActSpellCost(int,int cost){return cost;}int GetFocusEffect(int,int){return focus;}
 void DeleteItemInInventory(int id,int count,bool){inv.counts[id]-=count;deleted+=count;}
};
bool accessible=true,target_allowed=true;
bool DoppelSpellAccessible(Client*,int){return accessible;}
bool DoppelTargetAllowed(Client*,Mob*t,int){return t&&target_allowed;}
NightcapDoppelganger::Role role=NightcapDoppelganger::Role::Heal;
NightcapDoppelganger::Role DoppelRole(int){return role;}
struct Zone{struct Random{bool Roll(int chance){return chance>=100;}}random;}world,*zone=&world;
struct NPC{
 Client*owner=nullptr;int nightcap_doppel_spell=1,nightcap_doppel_target=7;
 uint64_t nightcap_doppel_next_check=0;std::map<int,uint64_t>nightcap_doppel_recast;
 Client*GetNightcapDoppelgangerOwner(){return owner;}
 int64 GetNightcapInheritedFocus(int type,int spell){return owner->GetFocusEffect(type,spell);}
 bool PrepareNightcapDoppelgangerCast(uint16,Mob*,int32&);
 void CompleteNightcapDoppelgangerCast(uint16,int32);
};
// METHODS
void check(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 Client owner;NPC clone;clone.owner=&owner;Mob target;int32 cost=0;
 spells[1].component[0]=5;spells[1].component_count[0]=2;owner.inv.counts[5]=2;
 owner.mana=49;check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"insufficient owner mana accepted");
 check(owner.deleted==0&&owner.mana==49,"failed cast spent resources");
 owner.mana=100;target.hp=76;
 check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"unnecessary heal completed");
 target.hp=20;accessible=false;
 check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"removed/memorized access bypassed");
 accessible=true;owner.inv.counts[5]=1;
 check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"missing components accepted");
 check(owner.deleted==0,"partial reagent spending");
 owner.inv.counts[5]=2;
 check(clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"valid completion rejected");
 check(owner.mana==100&&owner.deleted==2&&cost==50,"prepare paid mana or failed to consume reagents");
 clone.CompleteNightcapDoppelgangerCast(1,cost);
 check(owner.mana==50,"successful cast did not charge owner exactly once");
 check(clone.nightcap_doppel_recast[1]==16000&&clone.nightcap_doppel_next_check==11500,"reuse/recovery deadline");
 check(clone.nightcap_doppel_spell==0&&clone.nightcap_doppel_target==0,"coordination reservation leaked");
 clone.nightcap_doppel_spell=1;owner.focus=100;owner.inv.counts[5]=2;
 check(clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"focused cast failed");
 clone.CompleteNightcapDoppelgangerCast(1,cost);
 check(owner.mana==0&&owner.inv.counts[5]==2,"focus/reagent or shared owner mana incorrect");
 clone.nightcap_doppel_spell=1;
 check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"third clone spent unavailable owner mana");
 clone.owner=nullptr;check(!clone.PrepareNightcapDoppelgangerCast(1,&target,cost),"departed owner accepted");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
        compile_run(fixture.replace('// METHODS',methods))

    def test_healing_priority_interrupts_and_combat_effect_boundary(self):
        header = (ROOT / 'server-mods/code/common/nightcap_doppelganger.h').as_posix()
        compile_run(f'#include "{header}"\n' + r'''
#include <stdexcept>
#include <iostream>
using namespace NightcapDoppelganger;
void require(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 require(Wants(Role::Heal,49.9f)&&!Wants(Role::Hot,49.9f),"critical heal threshold");
 require(!Wants(Role::Heal,50)&&Wants(Role::Hot,50),"regular healing threshold");
 require(Wants(Role::Hot,75)&&!Wants(Role::Hot,75.1f),"upper healing threshold");
 require(!Interrupt(Role::Heal,75)&&Interrupt(Role::Heal,75.1f),"direct heal interruption");
 require(Interrupt(Role::Hot,39.9f)&&!Interrupt(Role::Hot,40),"HoT interruption");
 require(!Interrupt(Role::Rune,100),"rune was treated as a heal");
 require(Priority(Role::Hot,1)<Priority(Role::Heal,65),"role priority");
 require(Priority(Role::Heal,65)<Priority(Role::Heal,1),"higher level preference");
 require(Priority(Role::ResistDebuff,1)<Priority(Role::Damage,65),"debuff priority");
 require(CombatEffect(55)&&CombatEffect(0)&&CombatEffect(100),"core spell effects excluded");
 for(int effect:{22,32,33,58,67,71,374,999})require(!CombatEffect(effect),"unsafe/unknown automatic effect admitted");
 return 0;
}catch(const std::exception &e){std::cerr<<e.what();return 1;}}
''')


if __name__ == '__main__':
    unittest.main()
