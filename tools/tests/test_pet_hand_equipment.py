"""Run the production hand reservation and temporary hand-in paths."""
import unittest
from test_pet_equipment import compile_run, ROOT
from test_gameplay_policies import function


class PetHandEquipment(unittest.TestCase):
    def test_native_hands_restore_and_summoned_items_cannot_overwrite(self):
        zone=ROOT/'server-mods/code/zone'
        methods='\n'.join(function((zone/file).read_text(),signature) for file,signature in (
            ('client_pet_armor.cpp','void NPC::SetNightcapPetArmor('),
            ('client_pet_armor.cpp','bool NPC::IsNightcapPetArmorSlot('),
            ('npc.cpp','bool NPC::CanPetTakeItem(')))
        fixture=r'''
#include <array>
#include <map>
#include <memory>
#include <string>
#include <cstdint>
#include <stdexcept>
using uint8=uint8_t;using int16=int16_t;
namespace EQ {
namespace invslot {constexpr int slotPrimary=13,slotSecondary=14;}
namespace textures {constexpr int materialInvalid=-1;}
struct ItemData {int id=0;unsigned Slots=0;bool two=false;int NoRent=1,NoDrop=1;
 bool IsType2HWeapon()const{return two;}bool IsQuestItem()const{return false;}bool IsPetUsable()const{return true;}};
struct ItemInstance {ItemData data;int serial=0;ItemData*GetItem()const{return const_cast<ItemData*>(&data);}
 int GetID()const{return data.id;}int GetSerialNumber()const{return serial;}
 ItemInstance*Clone()const{return new ItemInstance(*this);}bool IsAttuned()const{return false;}};
struct InventoryProfile {std::map<int,ItemInstance>items;ItemInstance*GetItem(int slot){auto i=items.find(slot);return i==items.end()?nullptr:&i->second;}
 void PutItem(int slot,const ItemInstance&i){items[slot]=i;}void DeleteItem(int slot){items.erase(slot);}
 static uint8 CalcMaterialFromSlot(int){return 255;}};
}
namespace NightcapPetArmor {constexpr std::array<int16,22>Slots={2,17,7,9,12,18,19,20,13,14,1,4,5,3,6,8,10,15,16,11,0,21};}
namespace Chat{constexpr int PetResponse=0;}namespace AppearanceType{constexpr int Light=0;}
namespace fmt{template<class...T>std::string format(const char*s,T...){return s;}}
#define RuleB(a,b) false
struct NPC{
 std::array<bool,22>m_nightcap_armor_active{};
 std::array<std::shared_ptr<EQ::ItemInstance>,22>m_nightcap_armor_base{};
 EQ::InventoryProfile inv;std::array<int,22>equipment{};
 EQ::InventoryProfile&GetInv(){return inv;}bool IsPetOwnerOfClientBot(){return true;}
 bool IsCharmedPet(){return false;}bool IsPetOwnerClient(){return true;}bool IsCharmed(){return false;}
 NPC*GetOwner(){return this;}bool IsClient(){return true;}NPC*CastToClient(){return this;}
 void Message(int,const char*){}const char*GetCleanName(){return "pet";}
 void CalcBonuses(){}void SetAttackTimer(){}void SendWearChange(int){throw std::runtime_error("invalid material packet");}void UpdateEquipmentLight(){}
 bool UpdateActiveLight(){return false;}int GetActiveLightType(){return 0;}void SendAppearancePacket(int,int){}
 void SetNightcapPetArmor(uint8,const std::shared_ptr<EQ::ItemInstance>&,bool=false);
 bool IsNightcapPetArmorSlot(int16)const;bool CanPetTakeItem(const EQ::ItemInstance*);
};
void check(bool value){if(!value)throw std::runtime_error("hand equipment regression");}
// METHODS
int main(){
 auto item=[](int id,unsigned slots,bool two=false,int rent=1){auto p=std::make_shared<EQ::ItemInstance>();p->data={id,slots,two,rent,1};p->serial=id;return p;};
 NPC pet;auto temporary=item(1,1u<<14,false,0),two=item(2,1u<<13,true),shield=item(3,1u<<14);
 pet.inv.PutItem(14,*temporary);
 pet.SetNightcapPetArmor(8,two);pet.SetNightcapPetArmor(9,nullptr,true);
 check(!pet.inv.GetItem(14)&&pet.IsNightcapPetArmorSlot(14));
 check(!pet.CanPetTakeItem(temporary.get()));
 pet.SetNightcapPetArmor(9,nullptr,true);check(pet.m_nightcap_armor_base[9]->GetID()==1);
 pet.SetNightcapPetArmor(8,nullptr);pet.SetNightcapPetArmor(9,nullptr);
 check(pet.inv.GetItem(14)->GetID()==1&&!pet.IsNightcapPetArmorSlot(14));
 check(pet.CanPetTakeItem(temporary.get()));check(!pet.CanPetTakeItem(shield.get()));
 pet.inv.PutItem(13,*two);pet.SetNightcapPetArmor(8,nullptr,true);pet.SetNightcapPetArmor(9,shield);
 check(!pet.inv.GetItem(13)&&pet.IsNightcapPetArmorSlot(13));
 auto summoned_two=item(4,1u<<13,true,0);check(!pet.CanPetTakeItem(summoned_two.get()));
 pet.SetNightcapPetArmor(8,nullptr);pet.SetNightcapPetArmor(9,nullptr);
 check(pet.inv.GetItem(13)->GetID()==2&&pet.inv.GetItem(14)->GetID()==1);
 auto one=item(5,1u<<13);pet.inv.PutItem(13,*one);pet.SetNightcapPetArmor(8,nullptr,true);
 check(pet.inv.GetItem(13)->GetID()==5&&!pet.IsNightcapPetArmorSlot(13));
 auto neck=item(6,1u<<5,false,0);check(pet.CanPetTakeItem(neck.get()));
 pet.SetNightcapPetArmor(12,neck);check(!pet.CanPetTakeItem(neck.get()));
}
'''
        compile_run(fixture.replace('// METHODS',methods))


if __name__=='__main__':unittest.main()
