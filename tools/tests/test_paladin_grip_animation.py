"""Execute real grip projection and server animation selection together."""
import unittest
import test_free_trade as native

class GripAnimationTests(unittest.TestCase):
    compile_run=native.FreeTradeTests.compile_run

    def test_both_grips_select_matching_skill_and_animation(self):
        refresh=native.body((native.CODE/'common/item_instance.cpp').read_text(),'void EQ::ItemInstance::RefreshPaladinWeaponGrip(')
        attack=native.body((native.CODE/'zone/attack.cpp').read_text(),'EQ::skills::SkillType Mob::AttackAnimation(')
        self.compile_run(r'''
#include "common/paladin_weapon_grip.h"
#include <cassert>
#include <cstring>
#include <map>
namespace EQ {
namespace skills {enum SkillType {Skill1HSlashing,Skill2HSlashing,Skill1HPiercing,Skill2HPiercing,Skill1HBlunt,Skill2HBlunt,SkillHandtoHand};}
namespace item {enum {ItemType1HSlash=0,ItemType2HSlash=1,ItemType1HPiercing=2,ItemType1HBlunt=3,ItemType2HBlunt=4,ItemType2HPiercing=35,ItemTypeMartial=45};}
namespace invslot {constexpr int slotPrimary=13,slotSecondary=14;}
namespace versions {enum class ClientVersion {Old,RoF2};}
struct ItemData {
 unsigned ID=5504;int ItemType=1,Damage=23,Delay=45,Accuracy=0,Mana=0,AStr=0,AWis=0,HeroicStr=0,HeroicWis=0,HealAmt=0,SpellDmg=0;
 struct {int Level2=50;} Proc;
 struct {int Effect=13,Type=3,Level=1,Level2=1;} Click;
 char ClickName[65]={};int CastTime=0,CastTime_=0,RecastDelay=0,RecastType=0;
};
struct ItemInstance {
 const ItemData *m_item;ItemData *m_scaledItem=nullptr;std::map<std::string,std::string> m_custom_data;
 const ItemData *GetItem()const{return m_item;}bool IsClassCommon()const{return true;}
 void RefreshPaladinWeaponGrip();
};
}
enum {anim1HPiercing=2,anim2HSlashing=3,anim2HWeapon=4,anim1HWeapon=5,animDualWield=6,animHand2Hand=8};
#define Log(...) ((void)0)
#define RuleB(category,name) false
struct Zone {struct Random {bool Roll(int){return false;}} random;} zone_data,*zone=&zone_data;
struct Mob {
 int animation=-1,dual=0;
 bool IsClient(){return true;}bool IsNPC(){return false;}Mob* CastToClient(){return this;}
 EQ::versions::ClientVersion ClientVersion(){return EQ::versions::ClientVersion::RoF2;}
 int GetDualWieldingSameDelayWeapons(){return dual;}void SetDualWieldingSameDelayWeapons(int n){dual=n;}
 void DoAnim(int n,int,bool){animation=n;}
 EQ::skills::SkillType AttackAnimation(int,const EQ::ItemInstance*,EQ::skills::SkillType);
};
''' + refresh + attack + r'''
int main(){
 for(const auto &profile:NightcapPaladinGrip::Profiles){
  EQ::ItemData data;data.ID=profile.id;EQ::ItemInstance item{&data};Mob actor;
  for(int cycle=0;cycle<4;++cycle)for(bool one:{false,true}){
   item.m_custom_data.clear();if(one)item.m_custom_data[NightcapPaladinGrip::Key]="1";
   item.RefreshPaladinWeaponGrip();
   const auto skill=actor.AttackAnimation(EQ::invslot::slotPrimary,&item,EQ::skills::SkillHandtoHand);
   assert(skill==(one?EQ::skills::Skill1HSlashing:EQ::skills::Skill2HSlashing));
   assert(actor.animation==(one?anim1HWeapon:anim2HSlashing));
  }
 }
}
''')

    def test_attack_uses_owned_instance_and_wire_keeps_action(self):
        source=(native.CODE/'zone/attack.cpp').read_text()
        self.assertIn('GetInv().GetItem(EQ::invslot::slotPrimary)',source)
        self.assertIn('my_hit.skill = AttackAnimation(Hand, weapon);',source)
        codec=(native.CODE/'common/patches/rof2.cpp').read_text()
        encode=native.body(codec,'ENCODE(OP_Animation)')
        self.assertIn('OUT(action);',encode)
        mob=native.body((native.CODE/'zone/mob.cpp').read_text(),'void Mob::DoAnim(')
        self.assertIn('a->action  = animation_id;',mob)
        self.assertIn('false, /* Ignore Sender */',mob)

if __name__=='__main__':unittest.main()
